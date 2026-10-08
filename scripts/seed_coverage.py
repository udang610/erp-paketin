import os
import sys
import django

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.master.models import Coverage

regions = [
    {"city": "CGK - Jakarta", "district": "Cengkareng", "province": "DKI Jakarta"},
    {"city": "HLP - Jakarta", "district": "Halim", "province": "DKI Jakarta"},
    {"city": "BDO - Bandung", "district": "Cicendo", "province": "Jawa Barat"},
    {"city": "SUB - Surabaya", "district": "Sidoarjo", "province": "Jawa Timur"},
    {"city": "DPS - Denpasar", "district": "Tuban", "province": "Bali"},
    {"city": "KNO - Medan", "district": "Deli Serdang", "province": "Sumatera Utara"},
    {"city": "BPN - Balikpapan", "district": "Sepinggan", "province": "Kalimantan Timur"},
    {"city": "UPG - Makassar", "district": "Maros", "province": "Sulawesi Selatan"},
    {"city": "YIA - Yogyakarta", "district": "Kulon Progo", "province": "DI Yogyakarta"},
    {"city": "SRG - Semarang", "district": "Semarang Barat", "province": "Jawa Tengah"},
    {"city": "PLM - Palembang", "district": "Sukarami", "province": "Sumatera Selatan"},
    {"city": "BTH - Batam", "district": "Nongsa", "province": "Kepulauan Riau"},
    {"city": "PKU - Pekanbaru", "district": "Marpoyan Damai", "province": "Riau"},
    {"city": "PDG - Padang", "district": "Padang Pariaman", "province": "Sumatera Barat"},
    {"city": "BDJ - Banjarmasin", "district": "Banjarbaru", "province": "Kalimantan Selatan"},
    {"city": "PNK - Pontianak", "district": "Kubu Raya", "province": "Kalimantan Barat"},
    {"city": "MDC - Manado", "district": "Mapanget", "province": "Sulawesi Utara"},
    {"city": "LOP - Lombok", "district": "Lombok Tengah", "province": "NTB"},
    {"city": "AMQ - Ambon", "district": "Teluk Ambon", "province": "Maluku"},
    {"city": "DJJ - Jayapura", "district": "Sentani", "province": "Papua"}
]

print("Menambahkan data Coverage Daerah Indonesia beserta kode...")
for reg in regions:
    cov, created = Coverage.objects.get_or_create(
        city=reg['city'],
        district=reg['district'],
        province=reg['province'],
        defaults={'is_verified': True}
    )
    if created:
        print(f"Created: {reg['city']}")
    else:
        print(f"Already exists: {reg['city']}")
print("Selesai!")
