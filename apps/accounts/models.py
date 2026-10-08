import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Module Access Flags
    can_access_crm = models.BooleanField(default=False, verbose_name="CRM & Sales")
    can_access_operations = models.BooleanField(default=False, verbose_name="Operational")
    can_access_finance = models.BooleanField(default=False, verbose_name="Finance")
    can_access_hr = models.BooleanField(default=False, verbose_name="HR & GA")
    can_access_admin = models.BooleanField(default=False, verbose_name="Admin Panel")
    can_access_vm = models.BooleanField(default=False, verbose_name="Vehicle Management")
    can_access_monitoring = models.BooleanField(default=False, verbose_name="Monitoring / Dashboard")

    # Scoping
    is_branch_scoped = models.BooleanField(
        default=False,
        verbose_name="Batasi per Cabang",
        help_text="Jika aktif, user dengan role ini hanya melihat data dari cabang-nya sendiri."
    )

    # Preset vs Custom
    is_preset = models.BooleanField(
        default=False,
        verbose_name="Role Bawaan Sistem",
        help_text="Role bawaan tidak bisa dihapus dari sistem."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    # Preset role definitions (name -> config dict)
    PRESET_ROLES = {
        'CS': {
            'description': 'Customer Service — akses modul Operational',
            'can_access_operations': True,
        },
        'Driver': {
            'description': 'Driver / Courier — akses modul Operational',
            'can_access_operations': True,
        },
        'Finance': {
            'description': 'Finance / Keuangan — akses modul Finance',
            'can_access_finance': True,
        },
        'Sales': {
            'description': 'Sales — akses modul CRM & Sales',
            'can_access_crm': True,
        },
        'HR': {
            'description': 'HR & GA — akses modul HR',
            'can_access_hr': True,
        },
        'IT': {
            'description': 'IT — akses semua modul tanpa admin panel',
            'can_access_crm': True,
            'can_access_operations': True,
            'can_access_finance': True,
            'can_access_hr': True,
            'can_access_vm': True,
            'can_access_monitoring': True,
        },
        'VM': {
            'description': 'Vehicle Management — akses modul VM',
            'can_access_vm': True,
        },
        'Customer': {
            'description': 'Kustomer / Klien — akses pelacakan dan dashboard customer',
            'can_access_monitoring': True,
        },
        'Supervisor': {
            'description': 'Supervisor — monitoring semua data dari semua cabang',
            'can_access_crm': True,
            'can_access_operations': True,
            'can_access_finance': True,
            'can_access_hr': True,
            'can_access_monitoring': True,
        },
        'Supervisor Cabang': {
            'description': 'Supervisor Cabang — monitoring data dari cabang sendiri',
            'can_access_crm': True,
            'can_access_operations': True,
            'can_access_finance': True,
            'can_access_hr': True,
            'can_access_monitoring': True,
            'is_branch_scoped': True,
        },
        'Superadmin': {
            'description': 'Superadmin — akses penuh termasuk admin panel',
            'can_access_crm': True,
            'can_access_operations': True,
            'can_access_finance': True,
            'can_access_hr': True,
            'can_access_admin': True,
            'can_access_vm': True,
            'can_access_monitoring': True,
        },
    }

    # Mapping from User.user_type to preset role name
    USER_TYPE_TO_ROLE = {
        'CS': 'CS',
        'DRIVER': 'Driver',
        'FINANCE': 'Finance',
        'SALES': 'Sales',
        'IT': 'IT',
        'CUSTOMER': 'Customer',
        'ADMIN': 'HR',       # General staff defaults to HR access
        'OPS': 'CS',         # Ops/Gudang maps to Operational via CS role
        'MANAGER': 'Supervisor',
    }


class MenuPermission(models.Model):
    """Granular permission for specific menus/features beyond module-level access."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    MODULE_CHOICES = [
        ('crm', 'CRM & Sales'),
        ('operations', 'Operational'),
        ('finance', 'Finance'),
        ('hr', 'HR & GA'),
        ('vm', 'Vehicle Management'),
        ('monitoring', 'Monitoring'),
        ('admin', 'Admin'),
        ('master', 'Data Master'),
    ]
    
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    codename = models.CharField(
        max_length=100, unique=True,
        help_text="Identifier unik, e.g. 'operations.shipment.create', 'finance.invoice.approve'"
    )
    name = models.CharField(max_length=200, help_text="Label tampil, e.g. 'Buat Resi Baru'")
    description = models.TextField(blank=True, null=True)
    
    # Which roles have this permission by default
    roles = models.ManyToManyField(Role, related_name='menu_permissions', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['module', 'codename']
        verbose_name = "Izin Menu / Fitur"
        verbose_name_plural = "Izin Menu / Fitur"

    def __str__(self):
        return f"{self.get_module_display()} — {self.name}"


class MenuVisibilitySetting(models.Model):
    """
    Pengaturan visibilitas menu & modul pada admin panel.
    Memungkinkan Superadmin untuk menyembunyikan / menampilkan modul dan submenu tertentu
    secara global atau khusus role tertentu.
    """
    MODULE_CHOICES = [
        ('master', 'Data Master'),
        ('crm', 'Sales & CRM'),
        ('operations', 'Operational'),
        ('finance', 'Finance'),
        ('hr', 'HR & GA'),
        ('vm', 'Vendor Management (VM)'),
        ('admin', 'Admin & Pengaturan'),
    ]

    code = models.CharField(
        max_length=100, unique=True,
        help_text="Kode identifier unik, contoh: 'module_operations', 'menu_ops_pickup'"
    )
    name = models.CharField(max_length=200, help_text="Nama tampilan menu / modul")
    module_category = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name="Kategori Modul")
    is_module_header = models.BooleanField(
        default=False,
        verbose_name="Header Modul Utama",
        help_text="Jika dinonaktifkan, seluruh grup modul ini akan disembunyikan dari sidebar."
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name="Status Tampil (Aktif)",
        help_text="Hapus centang untuk menyembunyikan menu/modul ini dari sistem."
    )
    hidden_for_roles = models.ManyToManyField(
        Role, blank=True, related_name='hidden_menus',
        verbose_name="Sembunyikan Khusus Role Tertentu",
        help_text="Pilih role yang TIDAK boleh melihat menu ini meskipun modulnya aktif."
    )
    sort_order = models.IntegerField(default=0, verbose_name="Urutan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module_category', 'sort_order', 'code']
        verbose_name = "Pengaturan Visibilitas Menu & Modul"
        verbose_name_plural = "Pengaturan Visibilitas Menu & Modul"

    def __str__(self):
        type_str = "📦 Modul" if self.is_module_header else "📄 Submenu"
        status_str = "Aktif" if self.is_visible else "Disembunyikan"
        return f"{type_str}: {self.name} [{status_str}]"

    @classmethod
    def seed_default_menus(cls):
        """Membuat entri default untuk semua modul dan submenu ERP Paketin."""
        defaults = [
            # 1. DATA MASTER
            ('module_master', 'Modul Data Master', 'master', True, 1),
            ('menu_master_banks', 'Master Banks', 'master', False, 2),
            ('menu_master_branches', 'Master Branches', 'master', False, 3),
            ('menu_master_coverage', 'Master Coverage By District', 'master', False, 4),
            ('menu_master_customer', 'Master Customer', 'master', False, 5),
            ('menu_master_vehicle', 'Master Vehicle', 'master', False, 6),
            ('menu_master_price', 'Master Price', 'master', False, 7),
            ('menu_master_services', 'Master Services', 'master', False, 8),
            ('menu_master_vendors', 'Master Vendors', 'master', False, 9),
            ('menu_master_users', 'Master Users / Karyawan', 'master', False, 10),

            # 2. SALES / CRM
            ('module_crm', 'Modul Sales & CRM', 'crm', True, 20),
            ('menu_crm_client', 'Sales: Klien', 'crm', False, 21),
            ('menu_crm_lead', 'Sales: Peluang (Lead)', 'crm', False, 22),
            ('menu_crm_contract', 'Sales: Kontrak', 'crm', False, 23),
            ('menu_crm_quotation', 'Sales: Penawaran (Quotation)', 'crm', False, 24),
            ('menu_crm_activity', 'Sales: Aktivitas', 'crm', False, 25),
            ('menu_crm_report', 'Sales: Report', 'crm', False, 26),

            # 3. OPERATIONAL
            ('module_operations', 'Modul Operational', 'operations', True, 40),
            ('menu_ops_pickup', 'Ops: Pick Up', 'operations', False, 41),
            ('menu_ops_pos', 'Ops: POS / Data Resi', 'operations', False, 42),
            ('menu_ops_outgoing', 'Ops: Outgoing', 'operations', False, 43),
            ('menu_ops_transfer', 'Ops: Transfer Location', 'operations', False, 44),
            ('menu_ops_transit', 'Ops: Transit', 'operations', False, 45),
            ('menu_ops_incoming', 'Ops: Incoming Destination', 'operations', False, 46),
            ('menu_ops_delivery', 'Ops: Delivery', 'operations', False, 47),
            ('menu_ops_pod', 'Ops: POD', 'operations', False, 48),
            ('menu_ops_dobalik', 'Ops: DO Balik', 'operations', False, 49),
            ('menu_ops_retur', 'Ops: Retur (RTO)', 'operations', False, 50),
            ('menu_ops_tracking', 'Ops: Tracking Pencarian', 'operations', False, 51),
            ('menu_ops_print_bulky', 'Ops: Print Bulky AWB', 'operations', False, 52),
            ('menu_ops_void', 'Ops: Void Resi', 'operations', False, 53),
            ('menu_ops_report', 'Ops: Report SLA & Resi', 'operations', False, 54),

            # 4. FINANCE
            ('module_finance', 'Modul Finance', 'finance', True, 60),
            ('menu_fin_worksheet', 'Finance: Worksheet', 'finance', False, 61),
            ('menu_fin_ldp', 'Finance: LDP (Lembar Daftar Pengiriman)', 'finance', False, 62),
            ('menu_fin_invoice', 'Finance: Invoice & Billing', 'finance', False, 63),
            ('menu_fin_process', 'Finance: Invoice Process (Approve & Reconcile)', 'finance', False, 64),
            ('menu_fin_report', 'Finance: Report Keuangan', 'finance', False, 65),

            # 5. HRGA
            ('module_hr', 'Modul HR & GA', 'hr', True, 80),
            ('menu_hr_employees', 'HR: Karyawan', 'hr', False, 81),
            ('menu_hr_attendance', 'HR: Kehadiran & Absensi', 'hr', False, 82),
            ('menu_hr_policy', 'HR: Kebijakan Absensi', 'hr', False, 83),
            ('menu_hr_leave', 'HR: Pengajuan Cuti & Izin', 'hr', False, 84),
            ('menu_hr_documents', 'HR: Berkas & Dokumen', 'hr', False, 85),

            # 6. VENDOR MANAGEMENT (VM)
            ('module_vm', 'Modul Vendor Management (VM)', 'vm', True, 100),
            ('menu_vm_armada', 'VM: Armada', 'vm', False, 101),
            ('menu_vm_maintenance', 'VM: Maintenance', 'vm', False, 102),
            ('menu_vm_bbm', 'VM: BBM & Pengeluaran', 'vm', False, 103),

            # 7. ADMIN
            ('module_admin', 'Modul Admin & Pengaturan', 'admin', True, 120),
            ('menu_admin_settings', 'Admin: Pengaturan Sistem', 'admin', False, 121),
        ]

        for code, name, category, is_header, sort_order in defaults:
            cls.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'module_category': category,
                    'is_module_header': is_header,
                    'is_visible': True,
                    'sort_order': sort_order,
                }
            )

    @classmethod
    def get_visibility_map(cls, user=None):
        """
        Mengembalikan dict {code: bool} yang menyatakan apakah menu/modul aktif & boleh dilihat user.
        Jika belum ada di DB, fallback ke True (default terlihat).
        """
        try:
            settings_qs = cls.objects.prefetch_related('hidden_for_roles').all()
            if not settings_qs.exists():
                cls.seed_default_menus()
                settings_qs = cls.objects.prefetch_related('hidden_for_roles').all()

            user_role_ids = set(user.roles.values_list('id', flat=True)) if (user and user.is_authenticated and hasattr(user, 'roles')) else set()
            is_super = bool(user and user.is_authenticated and user.is_superuser)

            vis_map = {}
            for item in settings_qs:
                if not item.is_visible:
                    vis_map[item.code] = False
                elif not is_super and user_role_ids and any(r.id in user_role_ids for r in item.hidden_for_roles.all()):
                    vis_map[item.code] = False
                else:
                    vis_map[item.code] = True
            return vis_map
        except Exception:
            return {}


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Use email as the primary login field
    email = models.EmailField(unique=True)
    # Additional user fields
    USER_TYPE_CHOICES = [
        ('ADMIN', 'Admin / Staff'),
        ('IT', 'IT / Tech Support'),
        ('SALES', 'Sales'),
        ('DRIVER', 'Driver / Courier'),
        ('OPS', 'Operations / Gudang'),
        ('CS', 'Customer Service'),
        ('FINANCE', 'Finance / Keuangan'),
        ('MANAGER', 'Manager / SPV'),
        ('CUSTOMER', 'Customer / Klien'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='ADMIN', verbose_name="Kategori User")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Nomor HP")
    is_employee = models.BooleanField(default=True)
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    
    # Per-user custom permission overrides (beyond what their roles give them)
    extra_permissions = models.ManyToManyField(
        MenuPermission, related_name='users_extra', blank=True,
        verbose_name="Izin Tambahan",
        help_text="Permission tambahan di luar role utama. Untuk custom akses lintas divisi."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def has_menu_permission(self, codename):
        """Check if user has a specific menu/feature permission via roles or custom override."""
        if self.is_superuser:
            return True
        # Check via roles
        if self.roles.filter(menu_permissions__codename=codename).exists():
            return True
        # Check via per-user extra permissions
        if self.extra_permissions.filter(codename=codename).exists():
            return True
        return False

    def get_all_module_flags(self):
        """Return a dict of all module access flags for this user."""
        if self.is_superuser:
            return {
                'can_access_crm': True,
                'can_access_operations': True,
                'can_access_finance': True,
                'can_access_hr': True,
                'can_access_admin': True,
                'can_access_vm': True,
                'can_access_monitoring': True,
                'is_branch_scoped': False,
            }
        flags = {
            'can_access_crm': False,
            'can_access_operations': False,
            'can_access_finance': False,
            'can_access_hr': False,
            'can_access_admin': False,
            'can_access_vm': False,
            'can_access_monitoring': False,
            'is_branch_scoped': False,
        }
        for role in self.roles.all():
            for key in flags:
                if key == 'is_branch_scoped':
                    # branch_scoped is True if ANY role has it
                    if role.is_branch_scoped:
                        flags['is_branch_scoped'] = True
                else:
                    if getattr(role, key, False):
                        flags[key] = True
        return flags


# ─── Signal: Auto-assign preset role when user_type changes ───
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver


@receiver(post_save, sender=User)
def auto_assign_role_on_save(sender, instance, created, **kwargs):
    """When a new user is created OR user_type is set, auto-assign the matching preset role."""
    if instance.user_type:
        role_name = Role.USER_TYPE_TO_ROLE.get(instance.user_type)
        if role_name:
            try:
                role = Role.objects.get(name=role_name, is_preset=True)
                if not instance.roles.filter(pk=role.pk).exists():
                    instance.roles.add(role)
            except Role.DoesNotExist:
                pass  # Preset roles not yet seeded
