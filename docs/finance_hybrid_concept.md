# 💼 Blueprint Konsep Keuangan: Hybrid Spreadsheet-ERP Engine
> **Dokumen Analisa, Brainstorming & Rencana Penggabungan Modul Keuangan (Finance)**  
> **ERP Paketin** | Versi 1.1 | *Disiapkan untuk Diskusi & Review Tim*

---

## 📌 1. Latar Belakang & Realita Operasional (Business Reality)

Dalam bisnis ekspedisi, kargo, dan *Third-Party Logistics (3PL)*:
1. **Ketergantungan Tinggi pada Vendor Mitra**:
   - Pengiriman antarpulau, trucking linehaul, dan last-mile sering disubkontrakkan ke berbagai vendor ekspedisi lokal.
   - Tarif modal dari vendor (*Vendor Cost*) bersifat sangat dinamis dan fluktuatif (tergantung ketersediaan armada, musim/peak season, serta kesepakatan per muatan/borongan).
2. **Harga Jual Klien yang Dinamis**:
   - Tarif ke kustomer korporat (B2B) sering kali dinegosiasikan per-project, per-batch pengiriman, atau mendapatkan diskon volume bulanan khusus.
3. **Kebutuhan Staf Finance di Lapangan**:
   - Jika sistem dibuat **terlalu kaku (*rigid ERP*)**, staf akan terbebani oleh form bertingkat yang lambat, sehingga mereka cenderung kembali bekerja menggunakan Microsoft Excel.
   - Namun, jika hanya mengandalkan **Worksheet / Excel murni**, perusahaan kehilangan kontrol penagihan piutang (*AR*), pencatatan hutang (*AP*), cetak faktur/faktur pajak resmi, dan rekonsiliasi kas/bank.

---

## 💡 2. Konsep Solusi: *"Spreadsheet as the Interface, ERP as the Engine"*

Menggabungkan kecepatan dan keleluasaan edit **Spreadsheet (Excel-like)** dengan keteraturan dan kekuatan **ERP Database Relasional**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SISTEM HYBRID FINANCE PAKETIN                         │
│                                                                             │
│   TAMPILAN & PENGALAMAN INPUT                 PENGOLAHAN DATA & OUTPUT      │
│   (Kelebihan Worksheet / Excel)               (Kelebihan ERP Database)      │
│                                                                             │
│  • Grid Interaktif (Keyboard Tab/Enter)       • Integrasi Status Resi & POD │
│  • Edit & Bypass Bebas per Cell               • 1-Click Cetak LDP Resmi     │
│  • Input Jual (AR) & Modal (AP) Sekaligus     • 1-Click Invoice Klien + PPN │
│  • Live Margin / Profit per Baris Resi  ───►  • Rekapitulasi Tagihan Vendor │
│  • Rumus & Kalkulasi Netto Real-Time          • Rekonsiliasi Kas / Bank     │
│  • Copy-Paste & Batch Edit Multi-Baris        • Laporan Aging Piutang (AR)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚖️ 3. Komparasi Tiga Pendekatan

| Parameter | 1. Worksheet Murni | 2. ERP Kaku Konvensional | 🌟 3. Hybrid Engine (Pilihan Kita) |
| :--- | :--- | :--- | :--- |
| **Kecepatan Input Data** | ⚡ Sangat Cepat (Ketik cell) | ⏳ Lambat (Form bertingkat) | ⚡ **Sangat Cepat (Grid + Scan Barcode)** |
| **Penanganan Harga Vendor** | Bebas ketik | Kaku (Wajib ada master) | **Bebas ketik modal vendor per resi** |
| **Penanganan Harga Klien** | Bebas ketik | Kaku / Wajib kontrak | **Bebas bypass + master tarif sebagai referensi** |
| **Visibilitas Margin / Laba** | Rumus Excel manual | Seringkali terpisah | **Live Gross Profit per baris AWB** |
| **Penerbitan Invoice Resmi** | Manual copy ke Word/PDF | Otomatis | **1-Klik generate Invoice PDF resmi** |
| **Integrasi Status Operasional** | Tidak terhubung | Terhubung | **Terhubung langsung ke AWB/POD/DO Balik** |
| **Kepatuhan Audit & Pajak** | Lemah (Rentan terhapus) | Sangat Kuat | **Sangat Kuat (Snapshot terkunci permanen)** |

---

## 🏗️ 4. Empat Pilar Utama Konsep Gabungan

### Pilar 1: Grid Entry Fleksibel (*Excel-Speed Input*)
* Halaman LDP dan Invoicing disajikan dalam bentuk **Interactive Table Grid**:
  * Navigasi mulus menggunakan tombol keyboard panah, `Tab`, dan `Enter`.
  * Kolom **Tarif/Kg**, **Biaya Kirim Pokok**, **Diskon**, **Packing**, **Asuransi**, dan **Handling** terbuka untuk diedit langsung (*inline*).
  * Mendukung input **Harga Borongan / Flat Rate** (misal langsung ketik Rp 1.500.000 tanpa terikat rumus per kg).

### Pilar 2: Auto-Suggest Pintar (*Referensi, Bukan Pembatas*)
* Saat resi dipilih / di-scan:
  * Sistem mengisi tarif otomatis dari Master Rate sebagai **rekomendasi awal**.
  * Pengguna bebas membiarkannya atau langsung menimpa angkanya (*instant bypass*).
  * Tombol **Reset to Master** `↺` disediakan per baris untuk membatalkan perubahan manual sewaktu-waktu.

### Pilar 3: Dual-Perspective (Revenue vs Vendor Cost = Live Profit)
$$\text{Tagihan Klien (Revenue)} - \text{Biaya Vendor (Cost)} = \mathbf{\text{Gross Profit (Laba Kotor)}}$$
* Tim finance dapat melihat dan mengontrol margin keuntungan setiap resi sebelum dokumen tagihan disahkan.

### Pilar 4: One-Click Official Document Pipeline
Dari grid yang telah diedit fleksibel, sistem ERP langsung menghasilkan:
1. **Lembar LDP Resmi**: Dokumen serah terima ber-nomor (`LDPBKS2609210001`) dan ber-barcode.
2. **Faktur Invoice Klien (AR)**: Rincian tagihan resmi lengkap dengan perhitungan PPN (1,1%), materai, dan jatuh tempo.
3. **Rekapitulasi Tagihan Vendor (AP)**: Daftar kewajiban bayar ke mitra vendor ekspedisi.
4. **Rekonsiliasi Pembayaran**: Pencocokan bukti transfer bank dan penutupan piutang (*settlement*).

---

## 🗺️ 5. Pembagian Peran Menu Finance di ERP Paketin

```
FINANCE
├── 1. Worksheet (Analisa Margin & Rekap Vendor Cepat)
│      └── Tempat simulasi biaya, perbandingan vendor, dan audit margin kotor.
│
├── 2. LDP - Lembar Daftar Pengiriman (Grid Batching Resi)
│      └── Tempat menarik AWB, bypass harga manual/diskon klien, dan kunci snapshot nilai.
│
├── 3. Invoice & Billing (Pusat Penagihan Resmi)
│      ├── Tab 1: Invoice Klien (AR - Tagihan Piutang Customer)
│      ├── Tab 2: Invoice Vendor (AP - Kewajiban Bayar Vendor)
│      └── Tab 3: Rekapitulasi Tagihan & Lampiran Rincian Resi
│
├── 4. Rekonsiliasi & Kas/Bank (Settlement)
│      └── Pencatatan pelunasan, upload bukti transfer, dan status Lunas/Partial.
│
└── 5. Laporan Keuangan & Aging Piutang
       └── Analisa umur piutang (0-30 hari, 31-60 hari, dst.) dan performa profit bulanan.
```

---

## 📋 6. Poin-Poin Agenda Diskusi Besok

1. **Konfirmasi Struktur Kolom Input Vendor Cost**:
   - Apakah kolom biaya vendor ingin ditampilkan di tabel LDP utama atau di tab Worksheet khusus analisa internal?
2. **Batas Hak Akses (*Permission*) Bypass Harga**:
   - Apakah semua staf finance boleh bypass harga manual, atau perlu approval khusus jika diskon melebihi persentase tertentu?
3. **Template Format Cetak Invoice & Rekapitulasi**:
   - Finalisasi format layout PDF lampiran rekapitulasi resi kustomer (seperti contoh tabel lampiran yang sudah dianalisa).
4. **Siklus Pembayaran Vendor**:
   - Mekanisme validasi invoice vendor sebelum dibayarkan oleh bagian kas/bank.

---
*Dokumen ini dibuat otomatis sebagai rangkuman hasil sesi analisa sistem keuangan ERP Paketin.*
