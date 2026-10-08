import sqlite3
import pymysql
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.organizations.models import Branch
from apps.crm.models import Client, Lead, Contract, Quotation
from apps.finance.models import KpiFinance, KpiSheet, KpiFile
from apps.employees.models import Employee
# Import other required models here

User = get_user_model()

class Command(BaseCommand):
    help = 'Migrate data from legacy CRM, HR, and Finance databases'

    def add_arguments(self, parser):
        parser.add_argument('--crm-host', type=str, default='localhost', help='CRM MySQL Host')
        parser.add_argument('--crm-user', type=str, default='root', help='CRM MySQL User')
        parser.add_argument('--crm-pass', type=str, default='', help='CRM MySQL Password')
        parser.add_argument('--crm-db', type=str, default='crm_paketin_prod', help='CRM MySQL DB Name')
        parser.add_argument('--is-sqlite', action='store_true', help='Gunakan jika database CRM berupa file SQLite')
        parser.add_argument('--sqlite-path', type=str, default='../crm-paketin/db.sqlite3', help='Path ke file SQLite CRM')

    def handle(self, *args, **options):
        self.stdout.write("Mulai proses migrasi data...")
        
        # 1. Migrate CRM Data
        self.stdout.write("Migrating CRM data...")
        try:
            if options['is_sqlite']:
                import sqlite3
                crm_conn = sqlite3.connect(options['sqlite_path'])
                crm_conn.row_factory = sqlite3.Row
                crm_cursor = crm_conn.cursor()
            else:
                import pymysql
                crm_conn = pymysql.connect(
                    host=options['crm_host'],
                    user=options['crm_user'],
                    password=options['crm_pass'],
                    database=options['crm_db'],
                    cursorclass=pymysql.cursors.DictCursor
                )
                crm_cursor = crm_conn.cursor()

            # Contoh eksekusi query (disesuaikan dengan nama tabel produksi CRM)
            crm_cursor.execute("SELECT * FROM core_branch")
            branches = crm_cursor.fetchall()
            for row in branches:
                Branch.objects.get_or_create(
                    code=row['code'],
                    defaults={
                        'name': row['name'],
                        'city': row['city'],
                        'province': row['province'],
                        'is_active': bool(row['is_active']),
                    }
                )
                
            # TODO: Tambahkan logic untuk memindahkan Users, Clients, Leads, Quotations
            # ...
            
            crm_cursor.close()
            crm_conn.close()
            self.stdout.write(self.style.SUCCESS("Berhasil migrasi data CRM"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Gagal migrasi CRM: {e}"))
            
        self.stdout.write(self.style.SUCCESS("Migrasi data selesai!"))
