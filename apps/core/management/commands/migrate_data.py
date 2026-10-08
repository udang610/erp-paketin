from django.core.management.base import BaseCommand
import sys
import logging

class Command(BaseCommand):
    help = 'Migrasi data dari database CRM, Finance, dan HR ke ERP Paketin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the migration script without saving to the database',
        )
        parser.add_argument(
            '--modules',
            nargs='+',
            type=str,
            default=['crm', 'hr', 'finance'],
            help='Specific modules to migrate. Default: crm hr finance'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        modules = options['modules']
        
        self.stdout.write(self.style.SUCCESS('Memulai proses migrasi data...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN ACTIVE - Tidak ada data yang akan disimpan.'))

        # Migrasi HR
        if 'hr' in modules:
            self.stdout.write('Migrasi Modul HR...')
            self.migrate_hr(dry_run)
            
        # Migrasi CRM
        if 'crm' in modules:
            self.stdout.write('Migrasi Modul CRM...')
            self.migrate_crm(dry_run)
            
        # Migrasi Finance
        if 'finance' in modules:
            self.stdout.write('Migrasi Modul Finance...')
            self.migrate_finance(dry_run)

        self.stdout.write(self.style.SUCCESS('Proses migrasi selesai!'))

    def migrate_hr(self, dry_run):
        # NOTE: Implementasi aktual akan melakukan query ke database `hr_paketin` (menggunakan .using('hr_db'))
        # dan memindahkannya ke tabel default di ERP
        self.stdout.write(' -> Mengambil data karyawan...')
        self.stdout.write(' -> Mengambil data absensi...')
        if not dry_run:
            pass # Insert logic here

    def migrate_crm(self, dry_run):
        # NOTE: Implementasi aktual akan melakukan query ke database CRM lama
        self.stdout.write(' -> Mengambil data client...')
        self.stdout.write(' -> Mengambil data lead & kontrak...')
        if not dry_run:
            pass # Insert logic here

    def migrate_finance(self, dry_run):
        # NOTE: Implementasi aktual akan melakukan query ke database `system_finance`
        self.stdout.write(' -> Mengambil data KPI sheet & file...')
        self.stdout.write(' -> Mengambil data transaksi finance...')
        if not dry_run:
            pass # Insert logic here
