"""
Data migration: Seed 10 preset roles and migrate existing users to matching roles.
"""
from django.db import migrations


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

USER_TYPE_TO_ROLE = {
    'CS': 'CS',
    'DRIVER': 'Driver',
    'FINANCE': 'Finance',
    'SALES': 'Sales',
    'ADMIN': 'HR',
    'OPS': 'CS',
    'MANAGER': 'Supervisor',
}


def seed_preset_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    
    for role_name, config in PRESET_ROLES.items():
        role, created = Role.objects.update_or_create(
            name=role_name,
            defaults={
                'description': config.get('description', ''),
                'can_access_crm': config.get('can_access_crm', False),
                'can_access_operations': config.get('can_access_operations', False),
                'can_access_finance': config.get('can_access_finance', False),
                'can_access_hr': config.get('can_access_hr', False),
                'can_access_admin': config.get('can_access_admin', False),
                'can_access_vm': config.get('can_access_vm', False),
                'can_access_monitoring': config.get('can_access_monitoring', False),
                'is_branch_scoped': config.get('is_branch_scoped', False),
                'is_preset': True,
            }
        )
        if created:
            print(f"  Created preset role: {role_name}")
        else:
            print(f"  Updated preset role: {role_name}")


def migrate_existing_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Role = apps.get_model('accounts', 'Role')
    
    migrated = 0
    for user in User.objects.exclude(user_type='CUSTOMER').exclude(user_type__isnull=True).exclude(user_type=''):
        role_name = USER_TYPE_TO_ROLE.get(user.user_type)
        if role_name:
            try:
                role = Role.objects.get(name=role_name, is_preset=True)
                if not user.roles.filter(pk=role.pk).exists():
                    user.roles.add(role)
                    migrated += 1
            except Role.DoesNotExist:
                pass
    
    print(f"  Migrated {migrated} existing users to preset roles")


def reverse_migration(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    # Only delete roles that were created as presets by this migration
    # Don't delete if they have been customized (users manually added)
    Role.objects.filter(is_preset=True, name__in=PRESET_ROLES.keys()).delete()
    print("  Removed preset roles")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_rbac_enhance_role_add_menupermission'),
    ]

    operations = [
        migrations.RunPython(seed_preset_roles, reverse_migration),
        migrations.RunPython(migrate_existing_users, migrations.RunPython.noop),
    ]
