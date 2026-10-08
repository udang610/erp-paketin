from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.notifications.models import Notification
from apps.notifications.utils import record_activity_and_notify
from apps.operations.models import Shipment, Manifest, DocumentPouch
from apps.crm.models import Lead, Contract, Client
from apps.finance.models import Invoice, LDP
from apps.hr.attendance.models import AttendanceEvent
from apps.hr.leave.models import LeaveRequest

# ─────────────────────────────────────────────────────────────
# 1. OPERASIONAL
# ─────────────────────────────────────────────────────────────

@receiver(post_save, sender=Shipment)
def notify_on_shipment_events(sender, instance, created, **kwargs):
    if created:
        target_users = []
        if instance.client and hasattr(instance.client, 'sales') and instance.client.sales:
            target_users.append(instance.client.sales)
        if instance.created_by:
            target_users.append(instance.created_by)

        dest_city = getattr(instance, 'destination', '') or getattr(instance, 'destination_city', '') or '-'
        recv_name = getattr(instance, 'receiver_name', '') or getattr(instance, 'recipient_name', '') or '-'
        record_activity_and_notify(
            title=f"Resi Baru Dibuat: {instance.resi_number}",
            message=f"Resi {instance.resi_number} untuk penerima {recv_name} ({dest_city}) telah berhasil dibuat.",
            notification_type=Notification.NotificationType.OPS,
            actor=getattr(instance, 'created_by', None),
            target_roles=['CS', 'Supervisor', 'Superadmin'],
            target_users=target_users,
            url=f"/operations/shipments/?resi={instance.resi_number}",
            obj=instance
        )
    else:
        # Status specific events
        if instance.status == 'POD':
            target_users = []
            if instance.client and hasattr(instance.client, 'sales') and instance.client.sales:
                target_users.append(instance.client.sales)
            
            recv_name = getattr(instance, 'receiver_name', '') or getattr(instance, 'recipient_name', '') or '-'
            record_activity_and_notify(
                title=f"Shipment Terkirim (POD): {instance.resi_number}",
                message=f"Resi {instance.resi_number} telah berhasil diantar & diterima oleh {recv_name}.",
                notification_type=Notification.NotificationType.OPS,
                target_roles=['Finance', 'CS', 'Supervisor', 'Superadmin'],
                target_users=target_users,
                url=f"/operations/shipments/?resi={instance.resi_number}",
                obj=instance
            )
        elif instance.status == 'POD_BALIK' or instance.do_balik_date:
            record_activity_and_notify(
                title=f"DO Balik Terverifikasi: {instance.resi_number}",
                message=f"Fisik surat jalan DO Balik untuk resi {instance.resi_number} telah diterima & diverifikasi Hub Asal.",
                notification_type=Notification.NotificationType.DOCUMENT,
                target_roles=['Finance', 'CS', 'Supervisor', 'Superadmin'],
                url=f"/operations/do-balik/?q={instance.resi_number}",
                obj=instance
            )
        elif instance.status in ['RETURNED', 'VOID']:
            record_activity_and_notify(
                title=f"Status Resi {instance.get_status_display()}: {instance.resi_number}",
                message=f"Resi {instance.resi_number} berubah status menjadi {instance.get_status_display()}.",
                notification_type=Notification.NotificationType.OPS,
                target_roles=['CS', 'Supervisor', 'Superadmin'],
                url=f"/operations/shipments/?resi={instance.resi_number}",
                obj=instance
            )


@receiver(post_save, sender=Manifest)
def notify_on_manifest_created(sender, instance, created, **kwargs):
    if created:
        record_activity_and_notify(
            title=f"Manifest Baru: {instance.manifest_number} ({instance.get_manifest_type_display()})",
            message=f"Manifest {instance.manifest_number} rute {instance.origin_branch} → {instance.dest_branch} telah dibuat ({instance.shipments.count()} AWB).",
            notification_type=Notification.NotificationType.OPS,
            actor=instance.created_by,
            target_roles=['CS', 'Driver', 'Supervisor', 'Superadmin'],
            url=f"/operations/manifests/{instance.id}/",
            obj=instance
        )


@receiver(post_save, sender=DocumentPouch)
def notify_on_pouch_events(sender, instance, created, **kwargs):
    if created:
        record_activity_and_notify(
            title=f"Pouch DO Balik Dibuat: {instance.pouch_number}",
            message=f"Pouch surat jalan {instance.pouch_number} dari {instance.origin_branch} menuju {instance.dest_branch} siap dikirim.",
            notification_type=Notification.NotificationType.DOCUMENT,
            actor=instance.created_by,
            target_roles=['CS', 'Finance', 'Supervisor', 'Superadmin'],
            url=f"/operations/do-balik/?tab=in_pouch",
            obj=instance
        )


# ─────────────────────────────────────────────────────────────
# 2. FINANCE
# ─────────────────────────────────────────────────────────────

@receiver(post_save, sender=Invoice)
def notify_on_invoice_events(sender, instance, created, **kwargs):
    client_label = instance.client_name or '-'
    total_val = getattr(instance, 'total_amount', 0) or 0
    if created:
        record_activity_and_notify(
            title=f"Invoice Baru Dibuat: {instance.invoice_number}",
            message=f"Draft invoice {instance.invoice_number} senilai Rp {total_val:,.0f} untuk {client_label} telah digenerate.",
            notification_type=Notification.NotificationType.FINANCE,
            actor=getattr(instance, 'created_by', None),
            target_roles=['Finance', 'Sales', 'Supervisor', 'Superadmin'],
            url=f"/finance/invoices/{instance.id}/",
            obj=instance
        )
    elif instance.status == 'PAID':
        record_activity_and_notify(
            title=f"Invoice Lunas (PAID): {instance.invoice_number}",
            message=f"Pembayaran invoice {instance.invoice_number} ({client_label}) telah lunas terverifikasi.",
            notification_type=Notification.NotificationType.FINANCE,
            target_roles=['Finance', 'Sales', 'Supervisor', 'Superadmin'],
            url=f"/finance/invoices/{instance.id}/",
            obj=instance
        )


@receiver(post_save, sender=LDP)
def notify_on_ldp_created(sender, instance, created, **kwargs):
    if created:
        client_name = instance.client.name if (hasattr(instance, 'client') and instance.client) else (getattr(instance, 'client_name', '-') or '-')
        record_activity_and_notify(
            title=f"LDP Baru Diterbitkan: {instance.ldp_number}",
            message=f"Lembar Daftar Pengiriman {instance.ldp_number} untuk customer {client_name} telah diterbitkan.",
            notification_type=Notification.NotificationType.FINANCE,
            actor=getattr(instance, 'created_by', None),
            target_roles=['Finance', 'CS', 'Supervisor', 'Superadmin'],
            url=f"/finance/ldp/",
            obj=instance
        )


# ─────────────────────────────────────────────────────────────
# 3. CRM & SALES
# ─────────────────────────────────────────────────────────────

@receiver(post_save, sender=Lead)
def notify_on_lead_events(sender, instance, created, **kwargs):
    lead_name = instance.client.company_name if instance.client else getattr(instance, 'name', str(instance))
    owner_name = instance.owner.get_full_name() or instance.owner.username if instance.owner else 'Sales'
    if created:
        record_activity_and_notify(
            title=f"Peluang Baru (Lead): {lead_name}",
            message=f"Lead baru telah ditambahkan oleh {owner_name}.",
            notification_type=Notification.NotificationType.CRM,
            target_roles=['Sales', 'Supervisor', 'Superadmin'],
            url=f"/crm/leads/",
            obj=instance
        )
    elif instance.status == 'WON':
        record_activity_and_notify(
            title=f"🎉 Deal Won: {lead_name}",
            message=f"Lead {lead_name} berhasil dimenangkan (Status: WON). Harap siapkan operasional & kontrak.",
            notification_type=Notification.NotificationType.CRM,
            target_roles=['Sales', 'CS', 'Finance', 'Supervisor', 'Superadmin'],
            url=f"/crm/leads/",
            obj=instance
        )


@receiver(post_save, sender=Contract)
def notify_on_contract_created(sender, instance, created, **kwargs):
    if created:
        record_activity_and_notify(
            title=f"Kontrak Baru: {instance.contract_number}",
            message=f"Kontrak kerja sama {instance.contract_number} dengan klien {instance.client.company_name if instance.client else '-'} telah dibuat.",
            notification_type=Notification.NotificationType.CRM,
            target_roles=['Sales', 'Finance', 'Supervisor', 'Superadmin'],
            url=f"/crm/contracts/",
            obj=instance
        )


# ─────────────────────────────────────────────────────────────
# 4. HRGA
# ─────────────────────────────────────────────────────────────

@receiver(post_save, sender=AttendanceEvent)
def notify_on_attendance_created(sender, instance, created, **kwargs):
    if created:
        user = getattr(instance.employee, 'user', None)
        record_activity_and_notify(
            title=f"Presensi: {instance.employee.full_name} ({instance.get_event_type_display()})",
            message=f"{instance.employee.full_name} mencatat {instance.get_event_type_display()} ({instance.get_status_display()}) pada {instance.server_timestamp.strftime('%H:%M')}.",
            notification_type=Notification.NotificationType.ATTENDANCE,
            actor=user,
            target_roles=['HR', 'Supervisor', 'Superadmin'],
            url=f"/attendance/",
            obj=instance
        )


@receiver(post_save, sender=LeaveRequest)
def notify_on_leave_events(sender, instance, created, **kwargs):
    if created:
        user = getattr(instance.employee, 'user', None)
        record_activity_and_notify(
            title=f"Pengajuan Cuti: {instance.employee.full_name}",
            message=f"Pengajuan {instance.leave_type.name} dari {instance.start_date.strftime('%d/%m/%Y')} s/d {instance.end_date.strftime('%d/%m/%Y')} ({instance.total_days} hari) menunggu persetujuan.",
            notification_type=Notification.NotificationType.LEAVE,
            actor=user,
            target_roles=['HR', 'Supervisor', 'Superadmin'],
            url=f"/employees/",
            obj=instance
        )