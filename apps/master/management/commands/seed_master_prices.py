import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.master.models import Coverage, Service, Price


class Command(BaseCommand):
    help = "Seed complete standard shipping prices strictly with Origin from Bekasi and Jakarta to all 7,800+ destination districts across Indonesia"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Memulai seeding master data harga pengiriman (Price) KHUSUS Origin Bekasi & DKI Jakarta..."))

        # 1. Pastikan seluruh Master Service aktif tersedia
        services_data = [
            {'code': 'REG', 'name': 'Reguler', 'divisor': 5000, 'description': 'Layanan Reguler Standar'},
            {'code': 'ODS', 'name': 'One Day Service', 'divisor': 5000, 'description': 'Layanan 1 Hari Sampai'},
            {'code': 'SDS', 'name': 'Same Day Service', 'divisor': 5000, 'description': 'Layanan Sampai di Hari yang Sama'},
            {'code': 'RD', 'name': 'Reguler Darat', 'divisor': 4000, 'description': 'Layanan Ekspedisi Darat'},
            {'code': 'RL', 'name': 'Reguler Laut', 'divisor': 1000000, 'description': 'Layanan Ekspedisi Laut (Kargo Kapal)'},
            {'code': 'RUC', 'name': 'Reguler Udara Cargo', 'divisor': 6000, 'description': 'Layanan Kargo Udara Cepat'},
            {'code': 'RU', 'name': 'Reguler Udara', 'divisor': 5000, 'description': 'Layanan Pengiriman Jalur Udara'},
            {'code': 'TRK', 'name': 'Trucking', 'divisor': 4000, 'description': 'Layanan Kargo Truk Muatan Besar'},
        ]

        services_map = {}
        for s in services_data:
            svc_obj, _ = Service.objects.get_or_create(
                code=s['code'],
                defaults={
                    'name': s['name'],
                    'divisor': s['divisor'],
                    'description': s['description'],
                    'is_active': True,
                    'is_verified': True,
                }
            )
            services_map[s['code']] = svc_obj

        # 2. HAPUS SEMUA TARIF LAMA YANG BUKAN DARI BEKASI / JAKARTA
        self.stdout.write("Membersihkan seluruh data tarif yang origin-nya bukan dari Bekasi atau Jakarta...")
        Price.objects.all().delete()

        # 3. Origin Hub Eksklusif: Bekasi & Seluruh Wilayah Jakarta
        origin_configs = [
            {'city': 'Kota Bekasi', 'district': 'Bekasi Barat', 'default_id': 734, 'label': 'Bekasi (BKS)'},
            {'city': 'Kota Jakarta Selatan', 'district': 'Cilandak', 'default_id': 1327, 'label': 'Jakarta Selatan (JKS)'},
            {'city': 'Kota Jakarta Pusat', 'district': 'Cempaka Putih', 'default_id': 1204, 'label': 'Jakarta Pusat (JKP)'},
            {'city': 'Kota Jakarta Barat', 'district': 'Cengkareng', 'default_id': 1207, 'label': 'Jakarta Barat (JKB)'},
            {'city': 'Kota Jakarta Timur', 'district': 'Cakung', 'default_id': 1168, 'label': 'Jakarta Timur (JKT)'},
            {'city': 'Kota Jakarta Utara', 'district': 'Kelapa Gading', 'default_id': 2571, 'label': 'Jakarta Utara (JKU)'},
        ]

        origins = []
        for cfg in origin_configs:
            cov = Coverage.objects.filter(city=cfg['city'], district=cfg['district']).first()
            if not cov:
                cov = Coverage.objects.filter(city=cfg['city']).first()
            if not cov and cfg.get('default_id'):
                cov = Coverage.objects.filter(id=cfg['default_id']).first()
            if cov:
                origins.append((cov, cfg['label']))

        self.stdout.write(f"Daftar Origin yang digunakan ({len(origins)} Hub Bekasi & Jakarta):")
        for cov, label in origins:
            self.stdout.write(f" - {label}: {cov.district}, {cov.city} ({cov.tlc})")

        # 4. Fungsi kalkulasi tarif standar dari Bekasi/Jakarta ke Destinasi
        def calculate_tariff(orig_cov, dest_cov):
            dest_prov = (dest_cov.province or '').upper()
            dest_city = (dest_cov.city or '').upper()

            rates = []

            # Intra-Jabodetabek (Jakarta, Bogor, Depok, Tangerang, Bekasi)
            if any(k in dest_city for k in ['BEKASI', 'JAKARTA', 'DEPOK', 'TANGERANG', 'BOGOR']):
                rates.append(('REG', Decimal('8000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('ODS', Decimal('15000'), Decimal('1.0'), '1 Hari'))
                rates.append(('SDS', Decimal('25000'), Decimal('1.0'), 'Hari Ini'))
                rates.append(('RD', Decimal('4500'), Decimal('10.0'), '2-3 Hari'))
                rates.append(('TRK', Decimal('3500'), Decimal('50.0'), '2-3 Hari'))
            # Banten & Jawa Barat
            elif any(k in dest_prov for k in ['BANTEN', 'JAWA BARAT']):
                rates.append(('REG', Decimal('11000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('ODS', Decimal('22000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RD', Decimal('6000'), Decimal('10.0'), '2-4 Hari'))
                rates.append(('TRK', Decimal('4500'), Decimal('50.0'), '2-4 Hari'))
            # Jawa Tengah, DI Yogyakarta, Jawa Timur
            elif any(k in dest_prov for k in ['JAWA TENGAH', 'YOGYAKARTA', 'JAWA TIMUR']):
                rates.append(('REG', Decimal('15000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('ODS', Decimal('28000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RD', Decimal('7500'), Decimal('10.0'), '3-5 Hari'))
                rates.append(('TRK', Decimal('5500'), Decimal('50.0'), '3-5 Hari'))
            # Sumatera Bagian Selatan (Lampung, Sumsel, Bengkulu, Jambi, Bangka Belitung)
            elif any(k in dest_prov for k in ['LAMPUNG', 'SUMATERA SELATAN', 'BENGKULU', 'JAMBI', 'BANGKA']):
                rates.append(('REG', Decimal('24000'), Decimal('1.0'), '3-4 Hari'))
                rates.append(('RUC', Decimal('42000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RU', Decimal('42000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RL', Decimal('12000'), Decimal('5.0'), '4-7 Hari'))
                rates.append(('TRK', Decimal('8500'), Decimal('50.0'), '4-7 Hari'))
            # Sumatera Bagian Tengah & Utara (Sumbar, Riau, Kepri, Sumut, Aceh)
            elif any(k in dest_prov for k in ['SUMATERA BARAT', 'RIAU', 'SUMATERA UTARA', 'ACEH']):
                rates.append(('REG', Decimal('32000'), Decimal('1.0'), '3-5 Hari'))
                rates.append(('RUC', Decimal('52000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RU', Decimal('52000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RL', Decimal('15000'), Decimal('5.0'), '5-9 Hari'))
                rates.append(('TRK', Decimal('11000'), Decimal('50.0'), '5-9 Hari'))
            # Bali, NTB, NTT
            elif any(k in dest_prov for k in ['BALI', 'NUSA TENGGARA']):
                rates.append(('REG', Decimal('30000'), Decimal('1.0'), '3-5 Hari'))
                rates.append(('RUC', Decimal('48000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RU', Decimal('48000'), Decimal('1.0'), '1-2 Hari'))
                rates.append(('RL', Decimal('14000'), Decimal('5.0'), '6-10 Hari'))
                rates.append(('TRK', Decimal('10500'), Decimal('50.0'), '6-10 Hari'))
            # Kalimantan
            elif 'KALIMANTAN' in dest_prov:
                rates.append(('REG', Decimal('36000'), Decimal('1.0'), '3-5 Hari'))
                rates.append(('RUC', Decimal('56000'), Decimal('1.0'), '1-3 Hari'))
                rates.append(('RU', Decimal('56000'), Decimal('1.0'), '1-3 Hari'))
                rates.append(('RL', Decimal('16000'), Decimal('5.0'), '6-11 Hari'))
                rates.append(('TRK', Decimal('12500'), Decimal('50.0'), '6-11 Hari'))
            # Sulawesi & Gorontalo
            elif 'SULAWESI' in dest_prov or 'GORONTALO' in dest_prov:
                rates.append(('REG', Decimal('40000'), Decimal('1.0'), '3-5 Hari'))
                rates.append(('RUC', Decimal('62000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('RU', Decimal('62000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('RL', Decimal('18000'), Decimal('5.0'), '7-12 Hari'))
                rates.append(('TRK', Decimal('14000'), Decimal('50.0'), '7-12 Hari'))
            # Maluku & Maluku Utara
            elif 'MALUKU' in dest_prov:
                rates.append(('REG', Decimal('55000'), Decimal('1.0'), '4-6 Hari'))
                rates.append(('RUC', Decimal('82000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('RU', Decimal('82000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('RL', Decimal('22000'), Decimal('5.0'), '8-14 Hari'))
            # Papua & Papua Barat
            elif 'PAPUA' in dest_prov:
                rates.append(('REG', Decimal('85000'), Decimal('1.0'), '5-8 Hari'))
                rates.append(('RUC', Decimal('125000'), Decimal('1.0'), '2-4 Hari'))
                rates.append(('RU', Decimal('125000'), Decimal('1.0'), '2-4 Hari'))
                rates.append(('RL', Decimal('28000'), Decimal('5.0'), '10-20 Hari'))
            else:
                rates.append(('REG', Decimal('25000'), Decimal('1.0'), '3-5 Hari'))
                rates.append(('RUC', Decimal('45000'), Decimal('1.0'), '2-3 Hari'))
                rates.append(('RU', Decimal('45000'), Decimal('1.0'), '2-3 Hari'))

            return rates

        # 5. Seeding dari Origin Bekasi & Jakarta ke SEMUA 7,813 Destination
        all_destinations = list(Coverage.objects.all())
        self.stdout.write(f"Menyemai tarif untuk {len(all_destinations)} destinasi...")

        prices_to_create = []
        chunk_size = 5000
        total_created = 0

        for orig_cov, label in origins:
            self.stdout.write(f"-> Memproses Origin: {label}...")
            for dest in all_destinations:
                tariff_rates = calculate_tariff(orig_cov, dest)
                for svc_code, price_val, min_w, etd in tariff_rates:
                    svc_obj = services_map.get(svc_code)
                    if not svc_obj:
                        continue

                    prices_to_create.append(Price(
                        origin=orig_cov,
                        destination=dest,
                        service=svc_obj,
                        price_per_kg=price_val,
                        min_weight=min_w,
                        estimated_days=etd,
                        is_active=True
                    ))

                    if len(prices_to_create) >= chunk_size:
                        Price.objects.bulk_create(prices_to_create)
                        total_created += len(prices_to_create)
                        self.stdout.write(f"   -> Disimpan {total_created} tarif...")
                        prices_to_create = []

        if prices_to_create:
            Price.objects.bulk_create(prices_to_create)
            total_created += len(prices_to_create)

        final_count = Price.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Selesai! Seluruh data harga pengiriman sekarang 100% berasal dari Origin BEKASI dan JAKARTA. Total: {final_count} tarif."
        ))
