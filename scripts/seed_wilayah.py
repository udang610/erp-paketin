"""
Seed script untuk mengisi data wilayah Indonesia dari API wilayah.id
Berdasarkan Kepmendagri No. 300.2.2-2138 Tahun 2025

Usage: python manage.py shell < seed_wilayah.py
"""
import os
import sys
import django
import requests
import time

# Setup Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.master.models import Province, Regency, District, Village

API_BASE = "https://www.emsifa.com/api-wilayah-indonesia/api"

def seed_provinces():
    """Seed all 38 provinces"""
    print("=" * 60)
    print("SEEDING PROVINCES...")
    print("=" * 60)
    
    url = f"{API_BASE}/provinces.json"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Error fetching provinces: {e}")
        # Fallback: use static data for all 38 provinces
        data = get_static_provinces()
    
    count = 0
    for item in data:
        prov, created = Province.objects.update_or_create(
            code=str(item['id']),
            defaults={'name': item['name'].title()}
        )
        if created:
            count += 1
        print(f"  {'[NEW]' if created else '[UPD]'} {prov.code} - {prov.name}")
    
    print(f"\nTotal provinces: {Province.objects.count()} ({count} new)")
    return data


def seed_regencies(provinces_data):
    """Seed all regencies/cities"""
    print("\n" + "=" * 60)
    print("SEEDING REGENCIES (KABUPATEN/KOTA)...")
    print("=" * 60)
    
    count = 0
    for prov_item in provinces_data:
        prov_code = str(prov_item['id'])
        try:
            province = Province.objects.get(code=prov_code)
        except Province.DoesNotExist:
            print(f"  [SKIP] Province {prov_code} not found")
            continue
        
        url = f"{API_BASE}/regencies/{prov_code}.json"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            regencies = resp.json()
        except Exception as e:
            print(f"  [ERROR] Fetching regencies for {province.name}: {e}")
            continue
        
        for reg_item in regencies:
            reg_name = reg_item['name'].title()
            reg_type = 'KOTA' if reg_name.upper().startswith('KOTA ') else 'KABUPATEN'
            clean_name = reg_name.replace('Kota ', '').replace('Kabupaten ', '') if reg_type in ['KOTA', 'KABUPATEN'] else reg_name
            
            reg, created = Regency.objects.update_or_create(
                code=str(reg_item['id']),
                defaults={
                    'province': province,
                    'name': clean_name,
                    'type': reg_type,
                }
            )
            if created:
                count += 1
        
        print(f"  {province.name}: {len(regencies)} regencies")
        time.sleep(0.1)  # Be nice to the API
    
    print(f"\nTotal regencies: {Regency.objects.count()} ({count} new)")


def seed_districts(batch_mode=True):
    """Seed all districts (kecamatan)"""
    print("\n" + "=" * 60)
    print("SEEDING DISTRICTS (KECAMATAN)...")
    print("=" * 60)
    
    regencies = Regency.objects.all().order_by('code')
    count = 0
    total = regencies.count()
    
    for idx, reg in enumerate(regencies, 1):
        url = f"{API_BASE}/districts/{reg.code}.json"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            districts = resp.json()
        except Exception as e:
            print(f"  [ERROR] Fetching districts for {reg.name}: {e}")
            continue
        
        for dist_item in districts:
            dist, created = District.objects.update_or_create(
                code=str(dist_item['id']),
                defaults={
                    'regency': reg,
                    'name': dist_item['name'].title(),
                }
            )
            if created:
                count += 1
        
        if idx % 50 == 0 or idx == total:
            print(f"  Progress: {idx}/{total} regencies processed ({count} new districts)")
        time.sleep(0.05)
    
    print(f"\nTotal districts: {District.objects.count()} ({count} new)")


def get_static_provinces():
    """Fallback static data for all 38 provinces"""
    return [
        {"id": "11", "name": "ACEH"},
        {"id": "12", "name": "SUMATERA UTARA"},
        {"id": "13", "name": "SUMATERA BARAT"},
        {"id": "14", "name": "RIAU"},
        {"id": "15", "name": "JAMBI"},
        {"id": "16", "name": "SUMATERA SELATAN"},
        {"id": "17", "name": "BENGKULU"},
        {"id": "18", "name": "LAMPUNG"},
        {"id": "19", "name": "KEPULAUAN BANGKA BELITUNG"},
        {"id": "21", "name": "KEPULAUAN RIAU"},
        {"id": "31", "name": "DKI JAKARTA"},
        {"id": "32", "name": "JAWA BARAT"},
        {"id": "33", "name": "JAWA TENGAH"},
        {"id": "34", "name": "DI YOGYAKARTA"},
        {"id": "35", "name": "JAWA TIMUR"},
        {"id": "36", "name": "BANTEN"},
        {"id": "51", "name": "BALI"},
        {"id": "52", "name": "NUSA TENGGARA BARAT"},
        {"id": "53", "name": "NUSA TENGGARA TIMUR"},
        {"id": "61", "name": "KALIMANTAN BARAT"},
        {"id": "62", "name": "KALIMANTAN TENGAH"},
        {"id": "63", "name": "KALIMANTAN SELATAN"},
        {"id": "64", "name": "KALIMANTAN TIMUR"},
        {"id": "65", "name": "KALIMANTAN UTARA"},
        {"id": "71", "name": "SULAWESI UTARA"},
        {"id": "72", "name": "SULAWESI TENGAH"},
        {"id": "73", "name": "SULAWESI SELATAN"},
        {"id": "74", "name": "SULAWESI TENGGARA"},
        {"id": "75", "name": "GORONTALO"},
        {"id": "76", "name": "SULAWESI BARAT"},
        {"id": "81", "name": "MALUKU"},
        {"id": "82", "name": "MALUKU UTARA"},
        {"id": "91", "name": "PAPUA"},
        {"id": "92", "name": "PAPUA BARAT"},
        {"id": "93", "name": "PAPUA SELATAN"},
        {"id": "94", "name": "PAPUA TENGAH"},
        {"id": "95", "name": "PAPUA PEGUNUNGAN"},
        {"id": "96", "name": "PAPUA BARAT DAYA"},
    ]


if __name__ == '__main__':
    print("=" * 60)
    print("  SEED DATA WILAYAH INDONESIA")
    print("  Kepmendagri No. 300.2.2-2138 Tahun 2025")
    print("=" * 60)
    
    # Step 1: Provinces
    provinces_data = seed_provinces()
    
    # Step 2: Regencies
    seed_regencies(provinces_data)
    
    # Step 3: Districts  
    seed_districts()
    
    print("\n" + "=" * 60)
    print("  SEEDING COMPLETE!")
    print(f"  Provinces: {Province.objects.count()}")
    print(f"  Regencies: {Regency.objects.count()}")
    print(f"  Districts: {District.objects.count()}")
    print("=" * 60)
