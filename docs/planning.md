# Rencana Integrasi (Integration Plan): Paketin Cargo Legacy ➔ ERP Paketin Baru

## 🎯 Tujuan Utama
Menggabungkan alur kerja (workflow) operasional lapangan dari sistem lama (`cargo.paketingroup.com`) ke dalam sistem ERP baru tanpa menghilangkan arsitektur modul-modul modern (HR, CRM, Finance) yang sudah dibangun. Fokus utamanya adalah **meminimalkan kurva pembelajaran (learning curve) bagi tim operasional cabang** dengan mempertahankan istilah, tata letak logis, dan kebiasaan input mereka, namun dengan performa dan UI/UX yang jauh lebih baik.

---

## 🏗️ Strategi Penggabungan (Adoption Strategy)

1. **Pertahankan Terminologi Lama:** 
   Istilah yang sudah melekat di operasional seperti *POS Cash*, *List Entry Credit*, *Do Balik*, *Outgoing*, dan *Cek Tarif* akan dipertahankan sebagai nama menu/sub-menu di dalam modul **OPERATIONAL**, alih-alih menggunakan istilah asing.
   
2. **Replikasi Form Input (Familiarity):**
   Urutan pengisian form saat menerima barang dari pelanggan (Tujuan -> Berat -> Layanan -> Harga) akan dibuat identik dengan versi lama. Pengguna tidak perlu beradaptasi dengan cara input baru, namun sistem ERP akan secara otomatis memvalidasi dan mem-format angka.

3. **Bridge (Jembatan) ke Modul Modern:**
   - **Legacy:** Input resi POS Credit hanya sebatas data tabel.
   - **ERP Baru:** Input resi POS Credit akan secara *real-time* masuk ke dalam keranjang **Worksheet Finance** siap tagih.
   - **Legacy:** Master Klien berdiri sendiri.
   - **ERP Baru:** Master Klien terhubung dari hasil "WON" di modul **CRM & Sales**.

---

## 🗺️ Pemetaan Menu (Menu Mapping)

Berikut adalah bagaimana struktur navigasi ERP baru akan terlihat setelah penggabungan:

| Modul Legacy (cargo.paketingroup.com) | Lokasi di ERP Baru (erp-paketin) | Modul App Terkait |
| :--- | :--- | :--- |
| **Dashboard** (Statistik, Grafik) | `/` (Dashboard Utama) | `apps.core` |
| **Cek Tarif** | Menu Sidebar: **Operasional > Cek Tarif** | `apps.operations` |
| **POS** (Transaksi Tunai) | Menu Sidebar: **Operasional > POS Cash** | `apps.operations` |
| **List Entry Credit** (B2B) | Menu Sidebar: **Operasional > POS Credit** | `apps.operations` |
| **Outgoing / Manifest** | Menu Sidebar: **Operasional > Shipment & Manifest** | `apps.operations` |
| **DO Balik** | Menu Sidebar: **Operasional > DO Balik (POD)** | `apps.operations` |
| **Master Data** (Cabang, Bank, dll) | Menu Sidebar: **Master Data** | `apps.master` |
| *- Belum Ada di Legacy -* | Menu Sidebar: **CRM & Sales** | `apps.crm` |
| *- Belum Ada di Legacy -* | Menu Sidebar: **Finance (Worksheet & Invoice)** | `apps.finance` |
| *- Belum Ada di Legacy -* | Menu Sidebar: **HR & GA (Karyawan)** | `apps.hr` / `accounts` |

---

## 🚀 Fase Implementasi (Roadmap)

### Fase 1: Replikasi "Core Operations" (Fokus UX)
*Membangun pondasi operasional yang sering dipakai kurir/admin setiap hari.*
- [ ] Membuat halaman kalkulator **Cek Tarif** yang dinamis (menggunakan AJAX/JS agar *real-time*).
- [ ] Membangun antarmuka **POS Cash** (Pembuatan AWB/Resi Tunai). Form diurutkan persis seperti sistem lama (Asal, Tujuan, Layanan, Berat Aktual/Volumetrik, Total).
- [ ] Membangun antarmuka **POS Credit** (Pembuatan AWB B2B). Hanya klien dengan status `ACTIVE` dari CRM yang bisa dipilih.

### Fase 2: Integrasi Backend & Otomatisasi Jembatan (Bridge)
*Menghubungkan operasional dengan modul canggih ERP.*
- [ ] Menghubungkan output **POS Credit** ke generator otomatis **Worksheet** di modul Finance (Tarik data otomatis per klien per bulan).
- [ ] Membangun form cetak Resi (PDF/Thermal Printer) dengan layout yang tidak asing bagi admin cabang.

### Fase 3: Manifest, Tracking, dan Fitur Niche
*Menyelesaikan ekosistem logistik tingkat lanjut.*
- [ ] Modul **Outgoing/Manifest**: Mengelompokkan resi-resi POS ke dalam satu kendaraan/supir.
- [ ] Modul **Tracking & DO Balik (Proof of Delivery)**: Konfirmasi barang sampai, upload foto bukti pengiriman.
- [ ] Modul **Dompet / Deposit / TOPUP Cabang** (Bila perusahaan menerapkan sistem saldo untuk tiap agen/cabang).

### Fase 4: Evaluasi & Arsitektur Lanjutan (Robust & Flexible)
*Penyempurnaan sistem agar tangguh, berskala besar (enterprise-grade), namun tetap sangat ramah pengguna.*
- [ ] **Data Sentralisasi (Single Source of Truth):** Menyatukan entitas yang tersebar. Contoh: Penggabungan data Driver, Sales, Admin, Finance ke dalam satu modul Master Data User (Selesai dilakukan), sehingga pengaturan akses peran (RBAC) lebih solid.
- [ ] **Keamanan Transaksi (Robustness):** Menerapkan `transaction.atomic()` pada setiap eksekusi masal (seperti update ratusan resi saat memproses Manifest). Jika 1 resi gagal update, seluruh blok dibatalkan untuk menghindari *data corruption*.
- [ ] **Alur Finance Hibrida (Fleksibel):**
  - **Otomatis:** DO Balik (POD) yang terscan otomatis masuk/terekap di *Worksheet* bulanan Klien.
  - **Manual:** Fitur pintasan *Direct Invoicing* agar tim Finance bisa membuat tagihan khusus/DP proyek tanpa harus menunggu alur DO/Worksheet.
- [ ] **Otomatisasi Latar Belakang (Asynchronous Tasks):** Implementasi *task queue* (contoh: Celery) untuk fitur *blast email* tagihan otomatis, laporan PDF masal, atau sinkronisasi pelacakan (Tracking API) agar server tidak hang.
- [ ] **Frictionless UI/UX:** Adopsi masif teknologi *Barcode Scanner* AJAX (tanpa muat ulang halaman) di setiap titik persinggungan barang (Inbound, Outbound, Manifest, dan DO Balik) sehingga input manual/mengetik berkurang drastis.

---

## 💡 Kesimpulan
Dengan arsitektur ini, **User/Kurir Cabang** hanya akan melihat dan berinteraksi dengan menu **Operasional** yang *flow*-nya 100% familiar bagi mereka, dibantu otomatisasi *scanner*. Sementara itu, **Manajemen, Sales, dan Finance (Pusat)** akan mendapatkan fleksibilitas dan kekuatan penuh dari ERP modern yang tangguh di latar belakang. Kurva adaptasi (learning curve) akan sangat rendah, dan pondasi teknis tetap kokoh menampung jutaan transaksi.
