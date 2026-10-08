# CHANGELOG ERP PAKETIN

Dokumen ini mencatat seluruh riwayat pembaruan, perbaikan (*bug fixes*), dan penambahan fitur secara mendetail pada proses penyatuan sistem *Enterprise Resource Planning* (ERP) Paketin Cargo.


## [Versi 1.24.0-alpha] - 2026-10-07

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Redesain Tab Filter Status Peta Rute Distribusi & Tracing Logistik**:
  - **Pola Tab Status Dinamis Ala Chrome Tab (`.map-filter-pills`)**: Mengadaptasi mekanisme tab navigasi utama dashboard untuk tombol filter rute status pengiriman (*Semua, Pending, Outgoing, Transit, Incoming, Delivery*).
  - **Tab Aktif Square Rounded Card**: Tab aktif memiliki background abu-abu `#f1f5f9` (senada dengan tombol *Filter Detail*), border halus `#cbd5e1`, sudut `border-radius: 6px`, teks tebal `#0f172a`, dan elevasi subtle.
  - **Garis Pembatas Dinamis**: Garis pembatas vertikal halus (`|`) otomatis muncul hanya di antara tab-tab inaktif dan otomatis disembunyikan di sebelah tab yang sedang aktif menggunakan selektor CSS modern `:has()`.
- **Penyempurnaan Ikon Notifikasi Topbar & Palette Metrik**:
  - **Ikon Lonceng Duotone**: Mengganti ikon notifikasi lonceng topbar menjadi **Phosphor Duotone Bell** (`ph-duotone ph-bell`) bernuansa kuning emas/amber hangat (`#f59e0b`) tanpa outline berlebih.
  - **Perbaikan Warna Ikon Metriks Dashboard**: Menghapus override CSS global pada `.text-primary` sehingga ikon-ikon metrik kartu statistik (*Total Klien Aktif, dsb.*) mempertahankan warna aksen standar masing-masing.

### 🐞 Bug Fixes (Perbaikan Bug)
- **Filter Status Master Data (Banks & Reference Entities)**:
  - Memperbaiki masalah penyaringan data pada menu *Banks* (dan data master statis lainnya) di mana filter `Status: Aktif` sebelumnya mengembalikan 0 hasil akibat terikatnya parameter rentang tanggal default/query terhadap entitas referensi statis.
  - Mengisolasi penanganan filter tanggal pada `_build_master_filters` di `apps/master/views.py` khusus untuk entitas transaksional dan menambahkan fallback `is_active` query handling.

---

## [Versi 1.23.0-alpha] - 2026-10-06

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Redesain Sistem Filter & Pencarian Lintas Seluruh Modul (Pop-up Dropdown Filter Ala CRM)**:
  - **Pola Action Bar Modern**: Menggantikan panel collapsible filter yang memakan ruang vertikal dengan sebaris Action Bar yang minimalis dan terintegrasi di atas tabel data.
  - **Search Input Minimalis (`.search-box-clean`)**: Input pencarian bersih berlatar putih dengan ikon kaca pembesar di sisi kiri.
  - **Button Filter Pop-up Dropdown**:
    - Tombol filter independen dengan ikon `ph-bold ph-faders` yang memunculkan dropdown menu melayang (`.filter-dropdown-menu`).
    - Menggunakan atribut `data-bs-auto-close="outside"` agar dropdown tidak menutup otomatis ketika pengguna berinteraksi dengan kontrol form tanggal/select.
    - Dilengkapi **Indikator Titik Merah (`.active-filter-dot`)** yang menyala otomatis jika terdapat parameter filter yang sedang aktif.
    - Tombol aksi *"Terapkan"* (merah `#ed1c2e`) dan *"Reset"* terpasang di bagian bawah dropdown menu.
  - **Implementasi Menyeluruh di Seluruh Modul**:
    - *Sales / CRM*: [Kontrak](file:///c:/Users/dell/code/erp-paketin/templates/crm/sales/contract_list.html), [Peluang / Lead](file:///c:/Users/dell/code/erp-paketin/templates/crm/sales/lead_list.html), [Klien](file:///c:/Users/dell/code/erp-paketin/templates/crm/sales/client_list.html), [Penawaran / Quotation](file:///c:/Users/dell/code/erp-paketin/templates/crm/quotation/quotation_list.html), [Aktivitas Sales](file:///c:/Users/dell/code/erp-paketin/templates/crm/activity/activity_list.html).
    - *Data Master*: [Master List Template](file:///c:/Users/dell/code/erp-paketin/templates/master/master_list.html) (Customer, Vendor, Branch, Bank, Vehicle, Coverage, Price, Services).
    - *Operasional (Operations)*: [Data Shipment](file:///c:/Users/dell/code/erp-paketin/templates/operations/shipment_list.html), [Data Manifest](file:///c:/Users/dell/code/erp-paketin/templates/operations/manifest_list.html), [Destination Inbound / Incoming](file:///c:/Users/dell/code/erp-paketin/templates/operations/incoming_list.html), [POD](file:///c:/Users/dell/code/erp-paketin/templates/operations/pod_list.html), [DO Balik](file:///c:/Users/dell/code/erp-paketin/templates/operations/do_balik_list.html), [Manajemen Retur / RTO](file:///c:/Users/dell/code/erp-paketin/templates/operations/return_list.html), [Pickup Order](file:///c:/Users/dell/code/erp-paketin/templates/operations/pickup_list.html).
    - *Finance*: [LDP (Lembar Daftar Pengiriman)](file:///c:/Users/dell/code/erp-paketin/templates/finance/ldp_list.html), [Invoice & Billing](file:///c:/Users/dell/code/erp-paketin/templates/finance/invoice_list.html).
    - *HRGA*: [Data Pegawai & Karyawan](file:///c:/Users/dell/code/erp-paketin/templates/employees/employee_list.html).

- **Penempatan Judul Menu di Samping Kanan Tombol Sidebar Toggle Topbar**:
  - **Integrasi Topbar Navbar (`templates/base.html` & `static/css/style.css`)**:
    - Menambahkan elemen judul halaman dinamis `.page-title` tepat di samping kanan tombol toggle sidebar (`<` / `#sidebarToggle`).
    - Judul menu terisi otomatis via block `{% block page_title %}` atau fallback variabel konteks `{{ title }}`, memberikan informasi konteks lokasi menu yang jelas bagi pengguna.

- **Penyempurnaan Tampilan Form & Multi Koli**:
  - **Perapian Multi Koli**:
    - Menghilangkan background abu-abu bersarang (`card card-body bg-light`) pada kontainer tabel multi koli di form Quotation dan Shipment, sehingga tabel menyatu bersih di atas card form putih.
    - Menghilangkan padding berlebih dan divider horizontal redundan sehingga tinggi area multi koli presisi dan otomatis menyesuaikan baris item yang ditambahkan.
    - Mempertahankan konsistensi tombol toggle accordion (*"Jika membutuhkan input multi koli"* dan *"Scan Barcode AWB"*) dengan warna abu-abu bersih (`btn btn-light bg-light`).
  - **Form Master Customer (`templates/master/master_customer_form.html`)**:
    - Merapikan susunan field alamat kantor, kota, kecamatan, dan kode pos dalam layout horizontal yang proporsional.
  - **Form Quotation (`templates/crm/quotation/quotation_form.html`)**:
    - Menyelaraskan tata letak berat & dimensi sesuai standar form POS, menyembunyikan kalkulasi tarif manual berlebih, dan merapikan badge status kargo.

---

## [Versi 1.22.0-alpha] - 2026-09-29

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Pengaturan Visibilitas Menu & Modul di Admin Panel (Hide / Show Menu)**:
  - **Model Terpusat (`apps/accounts/models.py`)**: Membuat model `MenuVisibilitySetting` untuk mengatur hak tampil seluruh modul utama (*Data Master, Sales/CRM, Operational, Finance, HRGA, Vendor Management, Admin*) dan submenu spesifik di dalamnya.
  - **Auto-Seeding 48 Item Bawaan**: Fungsi otomatis `seed_default_menus()` yang memetakan seluruh modul dan submenu ERP Paketin ke dalam basis data.
  - **Dua Tingkat Kontrol Visibilitas**:
    - **Global (`is_visible`)**: Menonaktifkan modul/submenu untuk seluruh pengguna sistem.
    - **Role-Based (`hidden_for_roles`)**: Menyembunyikan modul/submenu khusus untuk role tertentu tanpa mengganggu hak akses role lainnya ataupun Superadmin.
  - **Admin Panel Unfold (`apps/accounts/admin.py` & `erp_paketin/settings.py`)**:
    - Registrasi menu *"Pengaturan Visibilitas Menu & Modul"* di sidebar Admin Django.
    - Fitur `list_editable = ('is_visible',)` untuk toggle visibilitas 1-klik langsung dari tabel tanpa membuka form detail.
    - Dilengkapi filter kategori modul, tipe header/submenu, pencarian cepat, serta bulk actions *"Tampilkan/Sembunyikan Menu Terpilih"*.
  - **Integrasi Sidebar Dinamis (`apps/core/context_processors.py` & `templates/base.html`)**:
    - Context processor menginjeksi dictionary `menu_vis` secara otomatis ke setiap request.
    - Seluruh header grup modul dan tautan submenu di sidebar mematuhi konfigurasi aktif secara instan.

- **Pusat Notifikasi & Log Aktivitas Terdistribusi per Role (Activity & Notification Center)**:
  - **Perbaikan Angka Notifikasi Lonceng Topbar**:
    - Memperbaiki kalkulasi badge lonceng topbar yang sebelumnya menjumlahkan seluruh total baris database shipment pending menjadi **secara akurat hanya menghitung notifikasi belum dibaca (`unread_notifications`) milik user aktif**.
    - Indikator perhatian operasional disajikan terpisah tanpa menggelembungkan badge notifikasi pesan.
  - **Peningkatan Model Notifikasi (`apps/notifications/models.py`)**:
    - Menambahkan relasi pelaku aksi (`actor`), tautan halaman tujuan (`url`), waktu dibaca (`read_at`), dan penambahan kategori modul (`MASTER`, `VM`, `HR`).
  - **Perekaman Aktivitas Terpusat (`apps/notifications/utils.py`)**:
    - Fungsi `record_activity_and_notify(...)` yang secara simultan mencatat `AuditLog` sistem dan mendistribusikan notifikasi terarah ke role yang relevan (`CS`, `Sales`, `Finance`, `HR`, `Supervisor`, `Superadmin`, `Driver`).
  - **Sinyal Otomatis Lintas Modul (`apps/notifications/signals.py`)**:
    - *Operasional*: Pembuatan Resi Baru, Status Terkirim (POD), DO Balik Terverifikasi, Retur & Void, Pembuatan Manifest, Pembuatan Pouch DO Balik.
    - *Finance*: Pembuatan Draft Invoice, Pembayaran Invoice (PAID), Penerbitan Lembar Daftar Pengiriman (LDP).
    - *Sales / CRM*: Peluang Baru (Lead), Deal Won (otomatis memberi tahu CS & Finance), Pembuatan Kontrak Kerja Sama.
    - *HRGA*: Presensi Masuk/Keluar Karyawan, Pengajuan Cuti & Izin.
  - **Halaman Web Pusat Notifikasi & Log Aktivitas (`templates/notifications/list.html` & `apps/notifications/views.py`)**:
    - Halaman responsif di `/notifications/` dengan filter kategori modul, filter status (Belum Dibaca/Semua), pencarian teks, pagination, panel *Audit Log Sistem*, dan tombol cepat *"Tandai Semua Sudah Dibaca"*.
  - **Desain Ulang Dropdown Lonceng Topbar (`templates/base.html`)**:
    - Menampilkan preview notifikasi terbaru dengan ikon warna modular, ringkasan pesan, timestamp, indikator belum dibaca, tombol *"Tandai Dibaca"*, serta section *Perhatian Operasional*.

- **Penyempurnaan Modul Operasional & DO Balik**:
  - **Badge DO Balik Merah (`templates/operations/do_balik_list.html`)**: Mengubah seluruh badge angka tab DO Balik (*Semua DO Balik, Tertahan di Tujuan, Dalam Pouch Dokumen, Terverifikasi Hub Asal*) dari warna putih (`bg-light`) menjadi **warna merah bold (`bg-danger text-white rounded-pill`)**.
  - **Sidebar Badge DO Balik (`templates/base.html`)**: Menambahkan badge merah dinamis pada menu DO Balik di sidebar navigasi yang menghitung jumlah fisik dokumen yang sedang menunggu penyelesaian.
  - **Perbaikan Sintaks Template `base.html`**: Memperbaiki pemisahan tag pembuka Dashboard dan Data Master yang sempat memicu `TemplateSyntaxError`.

- **Pembersihan & Restrukturisasi Menu Finance**:
  - Menghilangkan submenu *Vendor* dari modul Finance di sidebar dan Admin Panel Unfold untuk mencegah duplikasi, karena pengelolaan vendor telah dipusatkan pada Data Master (*Master Vendors*).
  - Sinkronisasi helper `parse_currency_decimal` dan perbaikan query relasi customer pada invoice finance.

### 🛡️ Test Suite Verification
- Seluruh 17 unit test dari suite `notifications`, `operations`, `accounts`, dan `finance` lulus 100% (**OK**).

---

## [Versi 1.21.0-alpha] - 2026-09-28

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Sentralisasi Arsitektur Template ERP (`templates/`)**:
  - Menyatukan seluruh template yang sebelumnya terfragmentasi di dalam `apps/*/templates/` (`operations`, `finance`, `master`) ke dalam satu direktori induk terpusat [`/templates/`](file:///c:/Users/dell/code/erp-paketin/templates/) dengan subfolder modular terstandar (`templates/operations/`, `templates/finance/`, `templates/master/`, `templates/crm/`, dsb.).
  - Mengeliminasi duplikasi file HTML sehingga setiap perubahan tampilan langsung aktif dan konsisten tanpa konflik prioritas Django Template Loader.
- **Penyempurnaan Alur & Kalkulasi Modul Finance (Invoicing & Billing)**:
  - **Filter Otomatis Invoice Aktif (`apps/finance/views.py`)**: Mengecualikan invoice dengan status `PAID` (Lunas) dari daftar utama dan counter tab **Invoice Klien (AR)** pada `/finance/invoices/`, menjaga menu penagihan tetap fokus pada invoice berjalan (Draft, Sent, Partial) karena invoice lunas telah diarsipkan pada menu **Invoice Process $\rightarrow$ Riwayat Selesai**.
  - **Kalkulasi & Rincian Tagihan Komprehensif (`templates/finance/invoice_detail.html`)**:
    - Menambahkan `<tfoot>` akumulasi total pada tabel **List Awb Invoice** (berat, freight cost, diskon, packing, asuransi, surcharge).
    - Menambahkan card panel **Rincian Perhitungan Tagihan & Pajak** yang menampilkan rincian Biaya Kirim, Diskon, Biaya Tambahan, Subtotal, Biaya Kemasan, Biaya Lain, PPN 1.1%, Premi Asuransi, Biaya Materai (Rp 10.000 jika > Rp 5.000.000), serta Grand Total.
    - Menambahkan box format resmi **Kalimat Terbilang Rupiah** dan ringkasan status rekonsiliasi pembayaran (Total Terbayar dan Sisa Piutang).
  - **Pembersihan UI Halaman Detail Invoice**: Menghapus tombol export (`COPY`, `EXCEL`, `PDF`) dan search field yang redundan di atas tabel List Awb Invoice untuk antarmuka yang lebih ringkas dan bersih.
  - **Standarisasi Aksi Dropdown Invoice Process**: Menyeragamkan tombol aksi dropdown `.btn-action-table` di Tab 3 Riwayat Selesai agar konsisten dengan tab Draft dan Approval.
- **Integrasi Otomatis Worksheet KPI Finance 2026**:
  - Penerapan sinkronisasi detail per-resi dari batch invoicing ke 1 file database utama `KPI Finance 2026` saat invoice dibuat (`invoice_create`) dan disetujui (`invoice_approve`).
  - Pembersihan badge dan tombol verifikasi di worksheet, serta perbaikan viewport container spreadsheet (sheets bar bawah, status bar pagination, dan scrollbar horizontal/vertikal).

---

## [Versi 1.20.0-alpha] - 2026-09-24

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Security Hardening & Standarisasi Keamanan OWASP**:
  - **Environment-Aware Security Settings (`erp_paketin/settings.py`)**: Konfigurasi `CORS_ALLOW_ALL_ORIGINS`, `DEBUG`, dan `ALLOWED_HOSTS` dinamis berbasis environment dengan whitelist regex domain resmi `*.paketin.co.id` dan `*.paketin.id`.
  - **Security HTTP Headers**: Mengaktifkan `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS = 'SAMEORIGIN'`, serta HSTS dan secure cookie untuk deployment produksi.
  - **Optimalisasi Masa Berlaku Token JWT**: Mengurangi masa berlaku Access Token dari 7 hari menjadi **60 menit** dan refresh token 7 hari dengan *token rotation* untuk memitigasi risiko pembajakan token.
  - **Batas Payload & Ukuran Memori Upload**: Mengatur `FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB` dan `DATA_UPLOAD_MAX_MEMORY_SIZE = 10MB` untuk mencegah serangan Denial-of-Service berbasis ukuran request.
  - **Modul Validator Berkas Terpusat (`apps/core/validators.py`)**: Menerapkan validasi ukuran dan whitelist ekstensi file (`.pdf`, `.jpg`, `.jpeg`, `.png`, `.webp`, `.docx`, `.xlsx`) pada bukti transfer (`PaymentReconciliation`), dokumen pickup (`PickupOrder`), dan dokumen karyawan.
  - **Proteksi Brute-Force Login (`apps/core/security.py`)**: Menerapkan `CustomLoginView` dengan sistem *cache rate-limiting* otomatis (maksimal 10 percobaan per IP/5 menit) untuk melindungi kredensial staf.
  - **Custom Error Handling Tanpa Stack Trace**: Menambahkan template aman `templates/404.html` dan `templates/500.html` berdesain modern yang tidak membocorkan informasi teknis/traceback ke pengguna akhir.
- **Standarisasi Input Data & Global Masking (`static/js/paketin-masking.js`)**:
  - Pemformatan otomatis format baku NPWP (`XX.XXX.XXX.X-XXX.XXX`) saat pengetikan pada form CRM, Finance, dan Master Data.
  - Sanitasi otomatis nomor telepon/WhatsApp (hanya angka dan prefiks `+`) dan nomor rekening bank.
- **Penyempurnaan Switch Bahasa & UX Pop-up Profil (`templates/base.html`)**:
  - Desain ulang switch bahasa profil: latar belakang track menggunakan warna Merah Paketin (`#ed1c2e`) baik pada posisi ID maupun EN.
  - Teks dinamis `ID` dan `EN` (tebal, warna merah) tampil presisi di dalam knob/dot putih geser.
  - Integrasi `sessionStorage` tracker untuk menjaga menu pop-up profil tetap terbuka secara otomatis setelah halaman selesai reload menerapkan bahasa baru.
- **Standarisasi Penyimpanan Aset Produksi**:
  - Menambahkan `STATIC_ROOT = BASE_DIR / 'staticfiles'` untuk standarisasi kompilasi aset statis melalui `python manage.py collectstatic`.
- **Standarisasi Tombol Sekunder & Tampilan Laporan**:
  - Menyeragamkan seluruh tombol dropdown *Export* di CRM dan tombol aksi sekunder menjadi warna abu-abu terstandar (`btn-outline-secondary bg-white`).
  - Merapikan visualisasi Financial Report dengan grouped bar chart bulanan seragam, analisis AR aging, dan export Excel.

### 🛡️ Security Audit & Pentest Verification
- **Uji Kerentanan SQL Injection**: 100% aman (kebal dari SQL Injection) karena seluruh query menggunakan Django ORM Parameterized Queries.
- **SAST Code Scan (Bandit Engine)**: Pemindaian pada 20.344 baris kode sumber menghasilkan **0 High, 0 Medium, 0 Critical Vulnerabilities**.

---

## [Versi 1.19.0-alpha] - 2026-09-23

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Standardisasi & Redesain Layout Cetak Invoice PDF (Finance Module)**:
  - **Struktur Header Presisi 3-Kolom**: Menyelaraskan tata letak header dengan logo dan profil legal perusahaan (`PT. Amanah Cargo Jaya Mandiri`) di sisi kiri, judul dokumen di tengah sejajar dengan logo, serta kotak meta info (No. Invoice, Tanggal, dll.) di sisi kanan.
  - **Format Status DRAFT Bertumpuk (*Stacked DRAFT Title*)**: Menampilkan badge teks `DRAFT` secara bertumpuk di atas judul `INVOICE` saat status invoice masih draft, dan kembali ke teks `INVOICE` tunggal ketika status telah disetujui (*Approved*).
  - **Tabel Rekening Bank 1-Baris & Lebar Kolom Optimal**: Memperlebar alokasi kolom Bank (68%) dan Nomor Rekening (32%) sehingga detail nama bank dan nomor rekening tertata rapi dalam 1 baris tanpa risiko teks bertabrakan (*word-wrapping collision*).
  - **Penyelarasan Garis Outline Kotak Terbilang**: Menyeragamkan warna dan ketebalan border kotak Terbilang (`#aaaaaa`) beserta garis vertikal pemisah nilai agar menyatu mulus dengan tabel rincian biaya di atasnya.
  - **Tipografi & Hierarki Footer**: Memperbesar font teks `Referensi / Reference` (9.5pt) dan penandatangan `(DPT. KEUANGAN)` (9pt) untuk keterbacaan yang lebih jelas dan formal.
  - **Kalibrasi Jarak Bawah (*Bottom Margin Precision*)**: Mengatur margin footer copyright secara presisi (100px) agar pas menempel di batas bawah halaman 1 tanpa menyisakan area kosong berlebih dan tanpa meluber ke halaman 2.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Penanganan Sanitasi Nama File & Judul Tab Browser PDF**:
  - Mengatasi masalah nama file unduhan yang berubah menjadi default `pdf` atau `pdf.pdf` akibat adanya karakter garis miring (`/`) pada nomor invoice dalam header `Content-Disposition`; karakter `/` dan `\` kini otomatis disanitasi menjadi `-` (contoh: `Invoice_INV-2026-09-0001.pdf`).
  - Menambahkan tag `<title>` pada template HTML PDF untuk memastikan metadata judul dokumen terisi dan terbaca dengan benar pada tab Google Chrome maupun ekstensi Adobe Acrobat.
  - Menambahkan rute URL PDF bernama (`invoices/<invoice_id>/pdf/<filename>`) di `apps/finance/urls.py` dan view `invoice_pdf` untuk kompatibilitas tautan langsung browser.

---

## [Versi 1.18.0-alpha] - 2026-09-19

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Standardisasi Layout Cetak AWB Reguler A4 (3 Salinan dalam 1 Halaman)**:
  - Mengoptimalkan proporsi dan tata letak cetak A4 3-in-1 (`shipment_print_reguler_a4_pdf.html` dan `print_bulky_pdf.html`) agar 3 lembar salinan AWB termuat secara presisi dan pas dalam 1 halaman utuh A4 tanpa menyisakan ruang kosong besar di bagian bawah (*zero bottom gap*).
  - Menambahkan garis potong (*cutting line*) bertitik (`. . . .`) yang dilengkapi ikon gunting (`scissor_left.png`) menghadap ke kiri pada sisi kanan garis potong sesuai standar visual dokumen kargo.
- **Penyempurnaan Tampilan Tombol Aksi Print Bulky**:
  - Mengganti menu dropdown aksi pada tabel pratinjau daftar cetak massal (`print_bulky.html`) menjadi tombol hapus langsung berbentuk ikon tempat sampah (*trash icon* `ph-trash`) tanpa teks label "Cancel".

### 🐛 Fixed (Perbaikan Bug & Error)
- **Pencegahan Error VariableDoesNotExist pada Template Cetak**:
  - Memperbaiki pemanggilan atribut dimensi pada model `ShipmentItem` dari `item.length`, `item.width`, `item.height` menjadi `item.panjang`, `item.lebar`, `item.tinggi`, dan `item.get_volume_weight` pada `print_bulky_pdf.html` dan `shipment_print_100x150_pdf.html`.
- **Perbaikan Ikon Gunting pada Cetak Massal (Print Bulky A4)**:
  - Menyediakan variabel `scissor_path` ke dalam konteks dan list item data pada view `print_bulky` di `apps/operations/views.py` sehingga gambar ikon gunting ter-render sempurna saat dicetak.

---

## [Versi 1.17.0-alpha] - 2026-09-18

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Peta Tracing Logistik Nasional & Interaktivitas Resi (Dashboard Map Updates)**:
  - **Filter Status PENDING**: Menambahkan opsi filter cepat `Pending` di samping kiri `Outgoing` pada deretan filter pill peta distribusi logistik di `templates/dashboard.html`.
  - **Detail Daftar Resi pada Popup Rute Logistik**: Menampilkan daftar resi aktif lengkap dengan tautan langsung menuju halaman detail resi (`/operations/shipments/<pk>/`), tipe layanan (*Express/Reguler*), nama pengirim $\rightarrow$ penerima, serta jumlah koli dan berat barang.
  - **Popup Titik Kota (Hub Asal & Titik Destinasi)**: Menampilkan ringkasan resi aktif dari hub asal dan resi yang sedang bergerak menuju kota destinasi dengan link navigasi langsung.
  - **Separasi Jalur Paralel Koridor Sama (*Corridor Arc Track Offset*)**: Menerapkan kalkulasi kurva busur paralel berbasis *Perpendicular Normal Vector* ketika terdapat lebih dari satu status pengiriman pada koridor kota yang sama (misal `PENDING` dan `PICKUP` pada rute Jakarta $\rightarrow$ Banda Aceh), sehingga setiap status memiliki lintasan visual tersendiri tanpa bertumpuk.
- **Standarisasi Modul Pusat Laporan (Operational & SLA Reporting Center)**:
  - Menyelaraskan seluruh tombol aksi filter/pencarian laporan di modul operasional dan modul lainnya menjadi label konsisten **"Preview"**.
  - Penyelarasan tata letak filter input tanggal, asal, tujuan, tipe layanan, dan status laporan serta pembersihan ikon tombol duplikat.
- **Master Referensi Template Impor Tarif Publish**:
  - Mengintegrasikan analisis skema template spreadsheet master (`upload_template_harga_publish (1).xlsx`) sebagai acuan baku impor data tarif multi-wilayah dan cakupan area kargo nasional.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Percampuran Warna Garis Pending (Color Mixing pada Unfiltered / `ALL`)**: Mengatasi masalah garis rute `PENDING` (warna amber `#f59e0b`) yang tampak hijau saat filter `ALL` akibat percampuran optik dengan garis `PICKUP` (cyan `#06b6d4`) pada koordinat yang identik; pemisahan busur paralel koridor mengembalikan kemurnian warna masing-masing status.
- **Garis Rute Menembus Titik Tujuan (*Polyline Overshoot / Layer Collision*)**: Mengatasi ujung garis rute yang mencuat keluar dari lingkaran kota tujuan dengan memindahkan layer marker (`origMarker` & `destMarker`) ke Leaflet `pane: 'markerPane'` ($z\text{-index } 600$) dengan border putih solid ($2.5\text{px}$) dan interpolasi ortogonal sinus murni.
- **NameError pada Laporan SLA Operasional**: Memperbaiki pengecualian `NameError: name 'coverage_city_label' is not defined` pada view laporan SLA (`shipment_sla_report` di `apps/operations/views.py`).

---

## [Versi 1.16.0-alpha] - 2026-09-17

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Desain Tab Interaktif Dashboard Seragam (Uniform Chrome-Style Tabs & Gliding Motion)**:
  - Menyempurnakan navigasi multi-slide dashboard (`templates/dashboard.html`) dengan standarisasi lebar tab yang seragam (`min-width: 175px`).
  - **Sliding Active Tab Indicator (*Gliding Pill/Bubble*)**: Latar belakang tab aktif meluncur mulus (*glides*) secara dinamis menggunakan kurva `cubic-bezier(0.4, 0, 0.2, 1)` durasi `0.22s`.
  - **Directional Panel Slide Transition**: Konten panel modul bergeser lembut (*slide-in* sejauh 12px) dari arah yang sesuai dengan posisi tab (bergeser dari kanan jika menuju tab berikutnya, dan dari kiri jika menuju tab sebelumnya) disertai *fade-in*.
  - Menerapkan garis pembatas vertikal di ujung kiri (sebelum tab *Home*) dan ujung kanan (setelah tab terakhir) serta antar tab menggunakan `::before` dan `::after` dengan transisi opacity halus pada hover/active.
  - Menghilangkan garis aksen merah atas tab aktif untuk koneksi visual yang menyatu (*seamless transition*) tanpa celah ke kartu konten di bawahnya.
- **Penyelarasan Warna Menu Profil Pengguna & Red Accent Removal**:
  - Mengubah seluruh ikon dan teks berwarna merah pada popup profil (*Divisi/Role, Bahasa, Admin Panel, dan tombol Keluar*) menjadi warna netral gelap tegas (`text-dark` / `text-secondary`).
  - Menghilangkan warna merah pada tombol aktif bahasa (`ID`) dan tombol keluar (*Logout*) menjadi tema netral gelap (*slate/dark*).
- **Perbaikan Menyeluruh Mode Gelap (*Dark Mode Polish*)**:
  - Menyelaraskan seluruh kontainer dashboard (`.dashboard-content-wrapper`, `.chrome-tab-glider`, `.nav-tabs-custom`, kartu metrik KPI, dan kartu chart) dalam tema gelap sehingga tidak lagi menyisakan border/kontainer putih yang kontras.
  - Memperbarui gaya tombol aktif pada modal preferensi sistem (*Personalisasi & Opsi*).
- **Standarisasi Skala Tampilan (*View Zoom*) Sesuai Bawaan Google Chrome**:
  - Mengatur ulang pilihan zoom pada menu preferensi menjadi standar bawaan Chrome: `80%`, `90%`, `100% (Bawaan Chrome)`, `110%`, dan `125%`.
- **Personalisasi Dashboard Berbasis Peran Akun (Role-Based Adaptive Dashboard Landing)**:
  - Mengarahkan default tab dashboard otomatis sesuai peran pengguna:
    - Akun CS / Driver / Operasional langsung mendarat pada tab **Operasional**
    - Akun Sales / CRM langsung mendarat pada tab **Sales**
    - Akun Finance / Kasir langsung mendarat pada tab **Finance**
    - Akun Vendor Management (VM) langsung mendarat pada tab **Vendor Management**
    - Akun HR & GA langsung mendarat pada tab **HRGA**
    - Superadmin / Manajemen pusat memiliki akses penuh ke seluruh tab slide.
- **Overhaul Peta Rute Distribusi & Tracing Logistik Nasional (Clean & High Precision)**:
  - **Bebas Watermark & Bebas Blokir (*Watermark-Free & Unrestricted*)**: Mengintegrasikan layer peta *ArcGIS Canvas Dark Gray (Base + Reference)* yang 100% stabil, beresolusi tinggi, tanpa pembatasan tile policy dan tanpa permintaan API Key.
  - **Warna Biru Midnight Senada Sidebar (*Midnight Navy Theme*)**: Mengaplikasikan formula filter kromatik CSS (`sepia(100%) hue-rotate(185deg) saturate(380%)`) yang mentransformasi layer peta menjadi nuansa *Deep Navy Blue* yang serasi dengan sidebar ERP Paketin (`#1a1a2e` s/d `#16213e`).
  - **Tata Letak Bersih Minimalis (*Clean Header Controls*)**: Menghapus kotak widget/HUD melayang yang menutupi peta, memindahkan badge rute aktif, filter status (*Semua, Outgoing, Transit, Incoming, Delivery*), dan pencarian kota (*Fly-to*) ke dalam *card header* gelap yang ramping.
  - **Presisi Titik Kota & Rute 100% (*Exact Coordinates & Sine Geodesic Arc*)**:
    - Mengganti ikon kustom bergeser dengan Leaflet `circleMarker` yang selalu terkunci presisi di titik koordinat pusat kota asal dan destinasi.
    - Menggunakan rumus kurva geodesik natural berbasis fungsi sinus ($\sin(t \cdot \pi)$), menjamin ujung awal ($t=0$) dan akhir ($t=1$) garis rute terhubung 100% tepat di pusat titik lingkaran tanpa offset/pergeseran (*zero drift*).
    - Animasi aliran pulsa bercahaya (*glowing pulse flow*) untuk menggambarkan pergerakan kargo aktif.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Peringatan 'API KEY REQUIRED' & Error 403 Tile Blocked**: Menghilangkan peringatan teks CartoDB dan pemblokiran 403 OSM dengan beralih ke layer resmi ArcGIS Dark Canvas yang terbuka untuk web publik.
- **Garis Rute Melenceng dari Titik Kota**: Memperbaiki algoritma kalkulasi kurva dan offset marker yang sebelumnya menyebabkan garis rute tidak menempel tepat di lingkaran kota asal/tujuan.

---

## [Versi 1.15.0-alpha] - 2026-09-16

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Restrukturisasi & Universal Void Module**:
  - Menyederhanakan alur pembatalan resi menjadi satu modul terpadu (*Universal Void* pada `/operations/void/credit/`) dan menyembunyikan sub-menu void cash yang tidak diperlukan.
  - Menghilangkan kata "AWB" secara menyeluruh dari label sidebar, tombol, judul header, dan tag log audit (`[VOID]`) untuk standardisasi istilah.
  - Menyelaraskan tata letak visual halaman Universal Void agar seragam dengan modul operasional lainnya.
- **Penyelarasan Background Gradient & Kontainer Transparan**:
  - Menerapkan background gradient lembut sistem (`linear-gradient(135deg, #eef5f1 0%, #e2ece6 45%, #f1f6f3 100%) fixed`) di `templates/base.html` dan `static/css/style.css`.
  - Menghilangkan pembungkus card putih berlebih pada menu Destination Inbound (`incoming_list.html`), POD (`pod_list.html`), Data Shipment (`shipment_list.html`), Manifest (`manifest_list.html`), dan Pickup Order (`pickup_list.html`), sehingga header dan tombol aksi mengapung bersih langsung di atas background gradient sementara latar putih dikhususkan untuk tabel data (`table-responsive`).
- **Penyederhanaan Header Dashboard & Navbar Shell**:
  - Mengubah judul Dasbor Utama dari kartu hero dengan icon roket menjadi teks bersih minimalis: **`Paketin Cargo Dashboard`** lengkap dengan sub-teks deskripsi umum.
  - Menghilangkan teks duplikat judul halaman di samping toggle hamburger `☰` pada navbar atas di `base.html` karena telah terwakili oleh judul masing-masing modul.
  - Menyelaraskan seluruh judul kartu di dashboard menjadi rata kiri serta menghilangkan badge *real-time/live*.
- **Desain Tab Interaktif Bergaya Browser (Chrome Tabs Style)**:
  - Menyempurnakan tab navigasi pada daftar Pickup Order (`pickup_list.html`):
    - Tab aktif menyatu secara presisi dan mulus dengan header tabel (`thead th`) tanpa garis pemisah bawah dan rata kiri sejajar (`0px offset`) dengan tepi tabel.
    - Tab tidak aktif tampil bersih dan borderless tanpa kotak pembungkus samping.
    - Menambahkan garis pembatas vertikal tegas (`2px`, tinggi `20px`, warna `#94a3b8`) di antara tab dan pada ujung tab terakhir.
    - Mempertahankan ketajaman font dan warna penuh ikon (100% vibran tanpa efek *muted/faded*).

### 🐛 Fixed (Perbaikan Bug & Error)
- **Offset Indentasi Tepi Kiri Tab**: Mengatasi celah/step 4px pada sisi kiri tab pertama di Pickup Order agar sejajar rata kiri dengan kontainer tabel data di bawahnya.
- **Background Putih Menutupi Header pada Modul Operasional**: Menghilangkan div wrapper card putih yang sebelumnya menutupi warna gradient di menu Destination Inbound dan POD.


## [Versi 1.14.0-alpha] - 2026-09-15

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Standardisasi Cetak AWB Reguler 3-in-1 (Kertas A4)**:
  - Menyempurnakan layout cetak A4 3 salinan dalam 1 lembar (`shipment_print_reguler_a4_pdf.html` dan `print_bulky_pdf.html`), mengoptimalkan margin `@page` (`2mm 4mm`), padding tabel, dan tinggi cell tanda tangan agar seluruh 3 salinan AWB (lengkap dengan tabel biaya, pengirim, penerima, tanda tangan, dan footer) termuat utuh dalam tepat 1 halaman A4 tanpa terdorong ke halaman ke-2.
  - Menambahkan garis potong (*dashed cutting line*) yang jelas di antara salinan AWB pada kertas A4.
  - Mengoptimalkan tabel rincian dimensi & berat untuk pengiriman *multi-koli* (menampilkan 2-3 koli pertama + ringkasan `+N Koli`) agar tetap informatif dan tidak menyebabkan luapan halaman (*page overflow*).
- **Penyelarasan Posisi QR Code & Logo ISO**:
  - Menambahkan margin pemisah (`margin-left: 8px`) dan proporsi ukuran gambar yang seimbang (`width="42"` untuk QR code dan `width="130"` untuk logo ISO) pada template cetak AWB Reguler, A4, dan cetak massal (*bulky print*), mencegah logo ISO menempel atau bertumpuk dengan QR code.
- **Peningkatan Keterbacaan Barcode & Kerapian Footer**:
  - Menyesuaikan proporsi barcode pada AWB Reguler dan A4 (`barWidth="0.85"` - `0.95"`, `barHeight="16"` - `18"`).
  - Merapikan teks informasi input resi (`Entry Date : ... by SUPERADMIN`) agar selalu konsisten dalam 1 baris teks yang rapi.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Halaman 1 Terpotong pada Cetak A4**: Mengatasi isu tabel bagian bawah salinan ke-3 yang hilang/kosong pada halaman 1 akibat batasan ketinggian halaman `xhtml2pdf`.
- **Garis Border Package ID**: Memperbaiki kerapian garis bingkai pada cetak thermal Package ID agar tersambung sempurna dengan ketebalan outline yang konsisten.


## [Versi 1.13.0-alpha] - 2026-09-14

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Grafik Interaktif Top Destinasi Pengiriman**: Mengganti tampilan list statis Top Destinasi menjadi grafik batang horizontal interaktif (*Horizontal Bar Chart*) berbasis Chart.js di dashboard operasional, yang mengagregasikan seluruh resi aktif dan valid secara dinamis.
- **Grafik Aktivitas Sales & Pipeline CRM**: Menambahkan visualisasi grafik interaktif untuk modul CRM di dashboard:
  - *Chart Status CRM Leads / Funnel Pipeline*: Menampilkan sebaran tahapan lead (Baru, Dihubungi, Kualifikasi, Proposal, Negosiasi, Won, Lost).
  - *Chart Aktivitas Sales (PIC)*: Menampilkan peringkat dan sebaran aktivitas tim sales (Telepon, WhatsApp, Kunjungan, Meeting, Email).
- **Sinkronisasi Perhitungan Berat Charge & Biaya Packing pada Edit Resi**: Memperbarui logika kalkulasi `shipment_update` di `apps/operations/views.py` agar saat data dimensi, berat aktual, atau koli anak diperbarui, sistem otomatis menghitung ulang `volume_weight`, `chargeable_weight`, dan `packing_cost` secara real-time serta menyimpan field nomor referensi (`reference_no`) ke basis data.
- **Penyelarasan Pemetaan Field Pengirim (Nama PIC vs No. Telepon)**: Memperbaiki pemetaan input field antara `sender_attention` (UP / Nama PIC Pengirim) dan `sender_phone` (No. Telepon Pengirim) pada formulir POS Resi (`shipment_form_resi.html`) dan tampilan detail resi (`shipment_detail.html`) agar data tidak tertukar.
- **Standardisasi Tampilan Detail Resi**: Menyelaraskan warna teks No. Referensi dan detail resi menjadi warna netral tegas (`text-dark`) untuk konsistensi visual di seluruh modul operasional.

### 🐛 Fixed (Perbaikan Bug & Error)
- **VariableDoesNotExist pada Form POS Credit & Cash (`/operations/pos/credit/` & `/operations/pos/cash/`)**: Memperbaiki kegagalan *render* template pada pembuatan resi baru akibat pemanggilan atribut `shipment` yang belum ada di context (`is_edit=False`). Menambahkan penanganan kondisional `{% if shipment %}` dengan fallback aman ke data `form`, serta menyertakan `shipment: None` secara eksplisit pada view `pos_credit` dan `pos_cash`.
- **FieldError 'photo' pada Cetak Bulky (`/operations/print-bulky/`)**: Memperbaiki lookup query tracking pada fungsi cetak bulky resi di `apps/operations/views.py` agar tidak me-resolve field yang tidak terdefinisi pada model `Tracking`.
- **VariableDoesNotExist 'office_address' pada Detail Resi & Tracking**: Menambahkan pengecekan keberadaan objek dan atribut alamat kantor cabang (*branch office address*) sebelum dirender pada template `shipment_detail.html` dan `tracking.html`.


## [Versi 1.12.0-alpha] - 2026-09-11

### 🚀 Added & Enhanced (Fitur & Peningkatan)
- **Dukungan Scan Manifest Delivery pada Entry POD**: Menambahkan integrasi pemindaian nomor Delivery Manifest (`DEL-...`) pada formulir Entry POD. Sistem secara otomatis memverifikasi manifest dan memasukkan seluruh daftar resi di dalamnya ke dalam antrean POD secara massal tanpa perlu scan satu per satu.
- **Penyederhanaan Form Entry POD**: Menghilangkan field input lokasi manual dari form POD. Riwayat tracking POD kini otomatis menggunakan kota tujuan dari data resi pengiriman (`shipment.destination` / `shipment.receiver_city`).
- **Otomatisasi Waktu & Tanggal Kejadian (Local Timezone Sync)**: Menyempurnakan inisialisasi waktu kejadian POD di frontend dan backend. Di backend, menggunakan `timezone.localtime()` (Asia/Jakarta / WIB) untuk mencegah perbedaan jam UTC, dan di frontend menggunakan jam lokal perangkat secara dinamis.
- **Redesign Popup User Profile (Navbar)**: Merombak total tampilan pop-up profil user di navbar menjadi antarmuka kartu terpadu (*clean unified list*) berlatar putih dengan efek hover yang halus:
  - Informasi identitas: Avatar/Foto, Nama Lengkap/Username, Nama Cabang, dan Badge Kode Cabang (misal `BKS`).
  - Informasi Divisi: Menampilkan nama divisi/departemen dan jabatan karyawan.
  - Pengganti Bahasa (*Language Switcher*): Toggle pill responsif `ID` / `EN` yang terintegrasi dengan preferensi bahasa sistem Django.
  - Shortcut Personalisasi & Opsi untuk pengaturan akun.
  - Shortcut Admin Panel khusus untuk role Superadmin / Admin / Staff ke `/admin/`.
  - Tombol Keluar (*Logout*) beraksen merah yang elegan dan aman di bagian bawah.
- **Pembaruan Tampilan Tabel POD List**: Menyesuaikan kolom daftar data POD (`Awb No`, `Tipe`, `Courier`, `Receiver Name`, `Destination`, `Weight (kg)`, `Colly`, `Created Date`, `Foto`, `Aksi`) lengkap dengan preview modal gambar dan badge tipe teks minimalis.

### 🐛 Fixed (Perbaikan Bug & Error)
- **AttributeError: 'Shipment' object has no attribute 'manifest_set'**: Memperbaiki pemanggilan relasi *reverse Many-to-Many* model `Shipment` ke `Manifest` di `apps/operations/views.py` (pada fungsi `entry_pod`, `entry_pod_return`, dan `update_status`) menjadi `shipment.manifests.all()`.
- **AttributeError: 'Customer' object has no attribute 'owner'**: Memperbaiki helper resolusi kepemilikan data klien di `apps/finance/models.py` saat proses sinkronisasi transaksi finance dari modul operasional.
- **TemplateSyntaxError pada Form Pembuatan Manifest**: Memperbaiki tag template Django (`{% endif %}` dan `{% include %}`) di `apps/operations/templates/operations/manifest_form.html` yang terpotong menjadi multi-baris sehingga menyebabkan kegagalan rendering.
- **Text Color No. Resi pada Antrean Scan POD**: Mengubah warna font teks resi pada tabel antrean scan POD dari warna merah (`text-primary`) menjadi hitam pekat (`text-dark fw-bold`) untuk keterbacaan yang optimal.

## [Versi 1.11.0-alpha] - 2026-09-09

### 🚀 Added (Penambahan Fitur)
- **Command Palette / Quick Access Berbasis Role**: Menambahkan command palette yang dapat dibuka melalui tombol pada header atau shortcut `Ctrl + K`. Daftar menu yang ditampilkan dibatasi oleh hak akses modul pengguna, sehingga user hanya melihat shortcut yang memang dapat dibuka. Shortcut yang tersedia mencakup Dashboard, Buat Resi, Data Shipment, Scan Transit, Pick Up, Tracking, CRM, Finance, dan HR.
- **Action Center pada Notifikasi**: Memindahkan alert operasional dari dashboard ke dropdown notifikasi agar dashboard tetap fokus pada monitoring. Alert mencakup shipment pending, transit lebih dari 48 jam, incoming destination, dan transfer location aktif. Setiap alert mengarah langsung ke daftar shipment dengan filter status yang relevan.
- **Design Tokens Global**: Menambahkan token terpusat untuk warna brand, status, border, radius, shadow, dan ukuran layout melalui `static/css/style.css`. Komponen baru dapat menggunakan primitive `.pk-card`, `.pk-btn`, `.pk-table`, `.pk-status`, dan `.pk-empty-state`.

### 🎨 Changed (Perubahan UI/UX)
- **Dashboard Lebih Ringkas**: Menghapus tombol `Buat Resi` dan `Scan Transit` dari header dashboard. Akses ke kedua menu tetap tersedia melalui sidebar dan command palette.
- **Search dan Quick Access Menyatu**: Menggabungkan field pencarian global dengan trigger Quick Access dalam satu komponen header. Pencarian tetap digunakan untuk resi/manifest, sedangkan ikon command membuka pencarian menu.
- **Badge Notifikasi Terpadu**: Angka pada badge notifikasi kini menghitung notifikasi sistem dan jumlah alert operasional secara bersamaan.
- **Palette Warna Terstandardisasi**: Primary dan danger memakai aksen merah Paketin, success memakai hijau, warning memakai amber, dan elemen netral memakai slate/abu-abu. Focus state, form control, button, card, table, dan status badge mengikuti aturan yang sama.
- **Konsistensi Lintas Modul**: Menambahkan baseline visual global untuk radius, shadow, border, hover, focus, empty state, dan sticky table header. Template setiap modul tetap boleh memiliki layout khusus sesuai kontennya, tetapi menggunakan bahasa visual yang seragam.

### 🛠️ Technical Notes (Catatan Teknis)
- Menambahkan view `command_palette` pada `apps/core/views.py`.
- Menambahkan route `GET /api/search/` pada `erp_paketin/urls.py` untuk data command palette role-aware.
- Menambahkan alert operasional global pada `apps/core/context_processors.py` agar dapat digunakan oleh notification dropdown di seluruh halaman.
- Tidak ada perubahan model atau migrasi database pada versi ini.
- Validasi yang dijalankan: `manage.py check`, `makemigrations --check --dry-run`, kompilasi template, render dashboard HTTP 200, dan pengujian endpoint command palette.


## [Versi 1.10.0-alpha] - 2026-09-08

### 🐛 Changed & Fixed (Peningkatan & Perbaikan)
- **Robust Auto-Fill Kecamatan (District) di Form POS & Pick Up**: Menumpas *bug* regresi (*race condition*) pada formulir pembuatan resi dan *pick up* di mana kolom Kecamatan (District) yang sudah terisi otomatis dari data Klien kembali menjadi kosong (*reset*). Perbaikan ini menggunakan HTML attribute State (`data-current-val`) untuk mengunci nilai tujuan (*intended value*) secara persisten, sehingga ketika AJAX request yang memuat daftar kecamatan baru selesai di-*load*, sistem tetap dapat membaca atribut tersebut dan menempelkan nilai yang tepat tanpa terinterupsi.
- **Pembersihan String Kota (City Name Stripping) di PDF Manifest**: Menyempurnakan properti *backend* (`get_city_origin`, `get_city_dest`, `get_tlc_origin`, `get_tlc_dest`) pada model `Shipment` dan `Manifest` untuk secara proaktif dan *case-insensitive* membuang kata imbuhan seperti "KOTA " atau "KABUPATEN " menggunakan Regular Expressions (`re.sub`). Hasil *render* di PDF kini menjadi jauh lebih bersih (contoh: "KOTA BEKASI" menjadi "BEKASI") dan meminimalisir kegagalan pencarian kode TLC di Master Data.
- **Logika Fallback TLC & Penghapusan Anomali Tampilan**: Mengganti logika *fallback* pada pencarian TLC (Three Letter Code). Apabila database *Coverage* gagal mencocokkan kota, sistem kini mengambil 3 huruf pertama dari nama kota yang sudah **dibersihkan** (misal: "BEKASI" -> "BEK"), bukan lagi dari nama mentah ("KOTA BEKASI" -> "KOT"). Selain itu, membasmi kemunculan *strip* gantung (`--`) saat data Vendor kosong, serta menuntaskan masalah nilai ganda di kolom "Cab. Tujuan" dengan mengimplementasikan filter CSS yang menyembunyikan *duplicate span* (*nth-of-type*).
- **Logika Toggle Radio "Sama Dengan Pick Up"**: Merevisi interaksi UI pada pembuatan resi. Ketika *user* memilih opsi "Tidak" pada radio button *Sama dengan pick up*, sistem kini secara otomatis dan instan mengosongkan kolom input "Alamat Pengirim", memberikan kanvas kosong bagi pengguna untuk mengisi alamat kustom yang berbeda dari titik lokasi *pick up* klien terkait.

## [Versi 1.9.0-alpha] - 2026-09-04

### 🐛 Changed & Fixed (Peningkatan & Perbaikan)
- **Implementasi Checkbox Dinamis (Layanan & Asuransi)**: Mengubah komponen HTML statis (`[ ]`) pada template cetak AWB 100x150 dan AWB A4 menjadi blok logika template Django dinamis. Checkbox sekarang me-render huruf `V` (tercentang) secara otomatis sesuai dengan data asli (`shipment.service`) seperti 'REGULER', 'ODS', atau 'SameDay'. Penanganan serupa juga diterapkan pada field Asuransi dan Handling (misal: merender "Tidak, Asuransi" jika data kosong).
- **Resolusi Page Break (Halaman ke-2) pada AWB 100x150**: Menumpas permasalahan luapan halaman (*spill over*) di cetakan AWB 100x150 yang melempar teks `Entry Date` dan `Copyright` ke halaman kedua saat deskripsi panjang. Perbaikan melibatkan kompaktifikasi *spacer* di kotak `Keterangan Item` (ketinggian dipangkas dari `25px` menjadi `2px`) dan penempatan ulang tag penutup tabel `</table>` yang posisinya tidak beraturan (liar) pada rilis terdahulu.
- **Resolusi Estetika Garis Putus-putus & Penyelarasan Ikon Gunting**: Memecahkan anomali rendering PDF engine `xhtml2pdf` di mana aturan CSS `border-bottom: 1px dashed` salah diterjemahkan menjadi garis padat (*solid*). Solusi final menggunakan **karakter titik literal asli (`.......`)**. Untuk mencegah melayangnya ikon gunting (&#x2702; dan &#9986;) di atas garis, ikon dan baris titik diposisikan di dua sel berdampingan dengan perlakuan *vertical-align: bottom* dan kompensasi presisi `padding-bottom: 2px` pada sisi titik literal, sehingga pusat sumbu ikon gunting kini lurus sempurna.
- **Finalisasi Margin Footer & Penyeragaman Ukuran 100x150**: Memperbesar ukuran teks (*font-size*) area `Entry Date` dan `Copyright` pada AWB 100x150 dari `5px` menjadi `6px` agar seragam dengan template AWB 100x100. Disertai dengan kalibrasi batas tepi: margin atas ditambah perlahan sebesar `2px` (*margin-top: 2px*) agar teks riwayat tidak lagi menempel kaku mencium garis batas (*outline*) tabel di atasnya, namun dipastikan tetap bertahan di satu halaman utuh (150mm).

## [Versi 1.8.0-alpha] - 2026-09-03

### 🐛 Changed & Fixed (Peningkatan & Perbaikan)
- **Penyempurnaan Cetakan PDF AWB Reguler**: Memperbaiki *bug* krusial pada engine `xhtml2pdf` di mana Logo ISO bergeser keluar jalur (jatuh ke bawah halaman) jika ukurannya sedikit diperbesar. Resolusi dilakukan dengan menempatkan QR Code dan Logo ISO ke dalam struktur tabel bersarang (*nested table*) yang kaku agar mereka terkunci bersebelahan. Menyempurnakan spasi antar baris (*gap*) pada statistik *header*, serta memperbaiki logika *template* untuk teks asuransi ("NO" menjadi "Tidak"). Memastikan PDF merender pada proporsi *Actual Size* (21.5cm x 11cm).
- **Redesign UI Tab Menu Pick Up (Chrome-Style)**: Merombak gaya antarmuka (*CSS Custom*) komponen tab pada menu Pick Up ("Menunggu Penugasan", "Manifest", "Riwayat Selesai") menjadi desain *flat* premium. Menerapkan warna abu-abu yang seragam (`#e9ecef`) pada tab aktif dan inaktif, dengan pembeda berupa *lining* (garis) pemisah vertikal khusus pada tab inaktif, sementara tab aktif menggunakan sudut melengkung.
- **Konsistensi Layout Tabel Pick Up**: Menyeragamkan (*unification*) seluruh wadah pembungkus (*wrapper*) tabel pada menu Pick Up sehingga menempel presisi di bawah tab tanpa adanya celah/jarak (margin) putih. Menyingkirkan *background* abu-abu pucat pada kotak kosong (*empty state*) sehingga area tabel sepenuhnya bersih, putih, dan menyatu (seamless).

## [Versi 1.7.0-alpha] - 2026-08-31

### 🚀 Added (Penambahan Fitur Baru)
- **Migrasi Relasi Klien ke Master Customer**: Mengalihkan seluruh relasi pelanggan pada Modul Operasional (terutama POS / Buat Resi) dari modul CRM lama ke modul Master Customer terpusat. Hal ini mencakup perbaikan *query* dasbor utama agar merujuk ke field yang valid (`client__name`) dan mem-bypass pengecekan atribut kadaluarsa (`credit_limit`).
- **Integrasi Penuh Auto-Fill Kota & Kecamatan**: Memperkaya sistem Auto-Fill pada formulir pembuatan resi dengan tambahan sinkronisasi data Wilayah (Kota dan Kecamatan). Jika Klien B2B dipilih pada modul POS, data Kota dan Kecamatan akan di-fetch dari API dan terisi otomatis ke input `<select>` berjenis Select2 secara dinamis.
- **Auto-Generate Nomor Resi Berbasis Customer ID**: Mengunci (*readonly*) isian Nomor Resi di UI formulir pembuatan untuk menghindari manipulasi manual, dan merombak fungsi *backend* agar menerbitkan resi dengan format unik & spesifik ke klien (`[KODE_CABANG]-CRD-[TANGGAL]-[KODE_CUSTOMER]-[NOMOR_URUT]`) secara otomatis, mempersiapkan skalabilitas pelacakan per customer.

### 🐛 Changed & Fixed (Peningkatan & Perbaikan)
- **UI/UX Data Master Customer & Resi**: Menyelaraskan estetika form dan tabel *Master Customer* menggunakan kelas CSS `.table-premium` agar identik dengan menu pengiriman.
- **Perbaikan UI Tabel Shipment**: Menghapus avatar lingkaran nama pengguna pada kolom "User Input" di Data Shipment (Resi) agar tampilan daftar baris muatan lebih leluasa, rapi, dan tak membebani secara visual, serta membenahi syntax error template yang timbul akibat penghapusan.

## [Versi 1.6.0-alpha] - 2026-08-29

### 🚀 Added (Penambahan Fitur Baru)
- **Desain Template Cetak AWB/Resi (POS)**: Menambahkan 4 jenis *template* cetakan AWB yang lengkap dan akurat sesuai kebutuhan kurir/cargo, yakni AWB Reguler A4 (mendukung 3 resi/koli per halaman), AWB Sticker 100x100, AWB Sticker 100x150, dan Package ID. Seluruh template sudah dilampiri logo perusahaan secara rapi dan otomatis.
- **Logika Nomor Resi Dinamis berbasis Cabang**: Menyempurnakan skema *auto-generate* Nomor Resi (AWB) dengan prefiks cabang (contoh `BDO-CRD-20260829-0001` untuk Bandung), di mana data cabang akan ditarik secara dinamis dari relasi *Employee Profile*. 
- **Integrasi Filter Klien Berkontrak di POS**: Membatasi opsi daftar *Customer/Shipper* pada form "Buat Resi" (POS Cash/Credit) hanya kepada Klien yang memiliki status Kontrak valid pada Modul CRM, memastikan alur *lead-to-cash* dan pembukuan tagihan lebih terjaga keakuratannya.
- **Header Badge Statistik POS/Resi**: Menambahkan kumpulan indikator (*badge*) interaktif di atas daftar resi untuk merekap jumlah total resi, Pending, In Transit, dan Terkirim secara instan. Menambahkan *Branch Code* pada label User (Navbar atas).
- **Tooltips Detail Flow Status**: Menambahkan *Tooltips* canggih di setiap *Badge Status* tabel resi. Saat di-hover, pop-up ringan akan mengilustrasikan sejarah alur perjalanan (*flow*) dari status tersebut tanpa harus membuka menu Detail.

### 🐛 Changed & Fixed (Peningkatan & Perbaikan)
- **Tweak Tabel Data POS/Resi & Pick Up**: Mengubah orientasi barisan tabel (Aksi dipindah ke sisi paling kanan, dan Status tepat di kirinya). Gaya font (*font-size*) diperkecil (mode `table-sm`), mengubah seluruh tipe *badge status* menjadi berbentuk oval (Pills) dengan ragam warna dinamis, dan menyeragamkan tombol *Aksi* menjadi warna merah.
- **Cleanup Form Buat Pick Up**: Menghilangkan atribut mandatory dari field "No Dokumen Ref", menyederhanakan "Shipment Type" menjadi form *Dropdown* statis, membuat pengisian "Jam/Tanggal Pickup" otomatis sesuai waktu akses form (bisa disesuaikan manual), serta memunculkan kembali tombol navigasi "Kembali".
- **Cleanup Form Buat AWB/Resi**: Menyembunyikan kolom "COD Value", menetralisir semua teks (label) menjadi hitam murni dari sebelumnya yang berwarna kemerahan/muted, serta menukar mode dropdown otomatisasi Nomor Referensi Pick Up & Nomor AWB menjadi text *input manual* (dengan mode auto-generate jika dikosongkan).
- **Seeding Data Wilayah Dasar (Coverage)**: Menyuntikkan (*seeding*) daftar data distrik/regional utama (BKS, BDO, CGK, SUB) ke *database master* Coverage, demi memastikan seluruh dropdown pemilihan kota/kecamatan operasional tidak kosong.
## [Versi 1.5.0-alpha] - 2026-08-28

### 🚀 Added (Penambahan Fitur Baru)
- **Perombakan UI/UX Modul Data Resi (POS)**: Merombak total formulir *Create Resi* (Shipment) menjadi antarmuka *card-based* modern yang terbagi ke dalam blok-blok jelas (Detail Shipper, Detail Receiver, Shipment Info, dan Detail Package). Mengadopsi style tabel `.table-premium` untuk daftar resi, menyelaraskan estetika visual yang konsisten dengan modul Pick Up.
- **Auto-Fill Data Klien & Integrasi CRM Lanjutan**: Memperkaya dropdown *Customer/Shipper* dengan dataset pintar (`data-attributes`). Saat PIC operasional memilih pelanggan korporat (B2B), seluruh data pengirim (Nama, Alamat, Kota, Kode Pos) otomatis terisi secara instan berkat eksekusi JavaScript tanpa *loading* berlebih. Menambahkan saklar praktis *Detail Shipper = Detail Pickup* untuk akselerasi operasional.
- **Pricing Engine Cerdas & Formula Volumetrik Dinamis**: Menggeser *hardcoded logic* harga menjadi algoritma kalkulasi dinamis berdasarkan Jenis Layanan (misal: *Reguler Darat* membagi volume dengan 4000, sedangkan udara membagi 6000). Sistem kini menghitung *Chargeable Weight* (maksimum antara berat aktual dan volumetrik) per-koli (baris barang). Mendukung penambahan biaya layanan opsional (*Insurance*, *COD*, *Surcharge*, *Handling*) dan biaya asuransi packing berdasar formula dimensi `((P+L+T+15)/3 * rate)` secara transparan di UI.
- **Dukungan Multi-Colly (Banyak Koli)**: Menambahkan input form dinamis (Formset) yang dilipat dalam *Accordion Menu* yang elegan untuk mendata setiap barang/koli (berat, dimensi, asuransi packing, dan deskripsi) jika pengiriman lebih dari 1 paket. Masing-masing barang otomatis dibuatkan resi colly (barcode) tersendiri di database saat tersimpan.
- **Import Resi via Excel Terotomatisasi**: Menghadirkan fitur *Import Data Resi* canggih yang mampu membaca puluhan/ratusan resi sekaligus menggunakan file *Excel*. Dilengkapi dengan *Template Standar* (.xlsx) siap unduh, otomatis mencari data CRM Klien berdasarkan nama perusahaan, membuat nomor resi (prefix: `IMP-`), hingga menghitung ulang *Chargeable Weight* masing-masing kargo sesuai logika harga sebelum tersimpan ke *Database*.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Penyesuaian Model Shipment (Database Migration)**: Membersihkan *duplicate class* usang pada struktur data dan menanamkan kolom-kolom kritikal baru (`sender_city`, `receiver_district`, `cod_value`, `surcharge_cost`, dsb) di model `Shipment` tanpa mencederai relasi yang sudah ada.
- **Depresiasi POS Cash (Hide Feature)**: Menyembunyikan menu *POS Cash (Tunai)* dari alur utama demi fokus implementasi proses B2B/Kredit sesuai arahan manajemen, mencegah potensi tercampurnya omset tunai sementara pada database ERP baru.

## [Versi 1.4.0-alpha] - 2026-08-27

### 🚀 Added (Penambahan Fitur Baru)
- **Rekonstruksi Workflow Modul Pick Up Operational**: Merombak total alur penugasan Pick Up (Request) agar lebih efisien dan modern dengan konsep 3-Tab ("Menunggu Penugasan", "Pick Up Manifest", dan "Riwayat Selesai").
- **Bulk Assign to Driver (Smart Modal)**: Menambahkan fitur *checkbox* massal di Tab 1 untuk memilih banyak order Pick Up sekaligus, yang akan memunculkan *Modal Pop-up* elegan untuk memilih Supir dan Armada tanpa perlu berpindah ke halaman form yang rumit.
- **Auto-Manifest & Relasi Database Pick Up**: Memperbarui struktur *Database* dengan menambahkan relasi `pickup_orders` (ManyToManyField) pada model `Manifest`. Sistem kini dapat menerbitkan dokumen Surat Jalan/Manifest bertipe `PICKUP` secara otomatis setelah supir di-assign, lengkap dengan pembuatan Nomor Manifest resmi (misal: `PKP-20260827-0001`).
- **Quick Status Update Dropdown**: Menambahkan menu *dropdown* "Aksi" pada tabel Pick Up Manifest untuk mempercepat tim Operasional mengubah status (Persiapan -> Menuju Lokasi -> Selesai Pick Up) langsung dari tabel. Dilengkapi sistem *auto-update* di mana jika Manifest berstatus "Selesai", seluruh order di dalamnya otomatis pindah ke Tab Riwayat.

### 🐛 Fixed (Perbaikan Bug & Error)
- **CSS Tab Active State**: Memperbaiki masalah Bootstrap Tab di `pickup_list.html` yang tidak ter-*highlight* saat diklik akibat bentrokan dengan *hardcoded utility classes*. Kini menggunakan *custom CSS* yang lebih elegan dan responsif.
- **Dropdown Tertutup oleh Table Responsive**: Menyelesaikan isu *CSS overflow* pada wadah `.table-responsive` yang menyebabkan menu *dropdown* Bootstrap 5 terpotong (*clipped*) atau tersembunyi di balik *scrollbar* jika jumlah baris tabel hanya sedikit.

## [Versi 1.3.0-alpha] - 2026-08-26
### 🚀 Added (Penambahan Fitur Baru)
- **Status (Update) pada Incoming Destination**: Label pada UI form scan (berdasarkan Resi maupun Manifest) diubah dari "Lokasi Terkini" menjadi "Status (Update)", menegaskan bahwa Customer Service dapat menginput string deskriptif secara dinamis (seperti "Tiba di Gudang Utama") sebagai riwayat status. 
- **Arsitektur Deteksi Mode Manifest Cerdas (`get_transfer_mode`)**: Menambahkan properti deterministik di model `Manifest` yang menggunakan ketersediaan field relasional (seperti `vendor`, `vehicle`, `flight_no`) untuk membedakan secara presisi antara Land Manifest Internal, Vendor Manifest, Air Freight, dan Sea Freight, alih-alih mengandalkan field teks kaku.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Anti-Duplikasi & Performa History Incoming**: Merombak mekanisme render *list view* pada fitur Incoming Destination. Tabel tidak lagi melakukan *looping* dari model riwayat `Tracking` yang menyebabkan satu resi tampil berulang kali jika dipindai berkali-kali. Kini iterasi menggunakan data `Shipment` sebagai *parent* dengan query `prefetch_related('tracking_history')`, menjamin resi hanya tampil sekali namun menayangkan status pemindaian terakhir.
- **Tampilan Waktu Scan Kosong**: Memperbaiki konflik syntax filter Django Template yang menyebabkan Waktu Scan dan Lokasi tidak terender di daftar Incoming Destination, serta mengganti nama kolom LOKASI SCAN menjadi STATUS.
- **Bug Penimpaan Tipe Vendor Manifest**: Memperbaiki celah logika fatal pada fungsi Edit/Update. Sebelumnya, saat *User* memilih "Moda Transportasi: DARAT" untuk Vendor Manifest, sistem otomatis memaksa nilai transport mode menjadi "VENDOR". Jika dibiarkan "DARAT", ketika form di-edit sistem akan meleset dan mengira itu adalah Land Internal atau form Outgoing biasa. Berkat fitur `get_transfer_mode`, pengklasifikasian menjadi absolut aman, mode DARAT di Vendor Manifest tersimpan secara persisten, render ikon (lencana) di tabel akurat 100%, dan rute halaman saat Edit tidak akan menyimpang.
- **Pembersihan Root Directory (Cleanup)**: Menghapus secara permanen lebih dari 25+ *file script Python ad-hoc* sisa proses iterasi pengembangan dan migrasi database (`patch_hr_apps.py`, `generate_worksheet.py`, dll.) dari dalam repositori utama untuk menjaga keamanan serta kebersihan struktur direktori *production*.

## [Versi 1.2.0-alpha] - 2026-08-21

### 🚀 Added (Penambahan Fitur Baru)
- **Arsitektur Hibrida Master Data (Hybrid Pattern)**: Menerapkan pendekatan gabungan pada Master Data (`Coverage` & `Service`) untuk modul CRM (`Quotation`) dan Operasional (`Shipment`). Fitur ini memungkinkan pengguna memilih rute standar dari *dropdown* (untuk otomasi harga), **ATAU** menggunakan mode **Auto-Create** untuk mendaftarkan rute baru yang otomatis tersimpan sebagai *draft* (`is_verified=False`), **ATAU** mengaktifkan tombol saklar *"Kargo Khusus (Bypass Master Data)"* untuk mengetik bebas tanpa menyimpan ke basis data Master.
- **Smart Combobox UI**: Mengimplementasikan `Select2 Tags` pada form Quotation dan Shipment, memungkinkan input ketik bebas layaknya tag yang diinterpretasi dengan cerdas oleh *backend*.
- **Standardisasi Tabel Enterprise (UI/UX)**: Menyelaraskan ukuran font dan tata letak tabel pada seluruh modul Operasional (`manifest_list`, `shipment_list`) dan HR (`attendance_list`) agar serasi dengan antarmuka ringkas bergaya CRM, menggunakan utilitas CSS `.table-enterprise`.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Integrasi Absensi Mobile ke Backend HR**: Memperbaiki variabel *context* (`events` bukan `attendance_records`) dan menyinkronkan data lokasi GPS dari aplikasi mobile (Flutter) dengan logika model `AttendanceEvent` di server Django, sehingga absensi presensi *real-time* dapat dimonitor langsung di web panel HR.
- **Notifikasi Global Dropdown**: Memperbaiki dan mengaktifkan fungsionalitas menu drop-down notifikasi (*bell icon*) pada Navbar melalui perbaikan *context processors* `apps.core.context_processors.unread_notifications`.
- **Styling Warna Status & Tombol**: Mengganti warna *badge* dan tombol yang sebelumnya kebiruan menjadi merah (`btn-danger`, `text-danger`) agar sejalan dengan palet warna dan identitas merek aplikasi lama.

## [Versi 1.1.0-alpha] - 2026-08-20

### 🚀 Added (Penambahan Fitur Baru)
- **Integrasi Penuh CRM ke Operasional**: Formulir Pembuatan Resi (Shipment) kini terintegrasi langsung dengan database CRM. Disediakan *dropdown* khusus Klien yang hanya menampilkan perusahaan/client yang telah berstatus `WON` dan memiliki kontrak aktif. Kolom pengirim lainnya dibuat opsional mengikuti profil klien.
- **Fitur Hapus dan Edit Resi Eksklusif Superadmin**: Menambahkan fungsionalitas Edit (`shipment_update`) dan Hapus (`shipment_delete`) Resi Pengiriman di modul Operasional. Akses ini dikunci murni secara *backend* dan *frontend* khusus untuk `is_superuser`. Halaman konfirmasi hapus khusus juga ditambahkan demi keamanan.
- **Standardisasi UX (Tombol Kembali)**: Menyematkan tombol "Kembali" (*Back*) pada seluruh *form interface* di modul Operasional (Shipment & Manifest) agar memiliki *experience* yang konsisten dengan modul Sales.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Migrasi Webhook ke ORM Internal**: Menghapus ketergantungan library eksternal `requests` di `apps/crm/views/sales.py`. Sistem kini tak lagi memanggil *webhook* via HTTP untuk transfer data antar modul, melainkan secara elegan menggunakan *query/import* langsung dari `apps.operations.models` dan `apps.finance.models` berkat arsitektur *monolithic* yang baru.
- **Bug Nomor Kontrak (AttributeError)**: Menyelesaikan malfungsi *error 500* saat Sales membuat Kontrak baru dengan menanamkan fungsi `generate_contract_number()` (generator nomor format `PT-KTR-YYYYMM-XXXX`) dan fungsi `get_absolute_url()` di dalam `Contract` model.
- **CSS Bootstrap Hilang (Offline Support)**: Memperbaiki masalah seluruh antarmuka yang rusak / kehilangan _styling_. Memigrasi penggunaan CDN *Bootstrap 5* ke file *static resource* lokal di dalam repositori agar aplikasi dapat dirender sempurna meskipun tanpa koneksi eksternal.
- **Anomali Indikator Status CRM**: Memperbaiki logika perwarnaan _badge_ di halaman detail *Lead* agar status yang sudah menang (`WON`) tampil dengan warna sukses (hijau) alih-alih peringatan (merah).

## [Versi 1.0.0-alpha] - 2026-08-19
- **Fase 4 & 5 - Operations & Finance Integration**:
  - **Auto-Tracking Barcode**: Membuat fungsi `/operations/scan/` yang mengizinkan admin logistik *scan* resi untuk meng-update status ke "In Transit", "Delivered", dsb secara masif dengan autofokus input.
  - **Otomatisasi Tagihan (Invoice Auto-Generation)**: Menerapkan *signal* `post_save` pada modul Operations di mana setiap `Shipment` yang berstatus `DELIVERED` akan otomatis:
    1. Membuat baris rekapan Profit & Loss di spreadsheet `KpiFinance`.
    2. Membuat atau memperbarui `Invoice` bulanan berstatus DRAFT untuk klien yang bersangkutan.
  - **Model Invoice & PaymentRecord**: Mendefinisikan skema tabel faktur dan riwayat pembayaran di modul Keuangan.
- **Inisiasi Proyek ERP Monolithic**:
  - Menggabungkan tiga repositori terpisah (`crm-paketin`, `System-Finance`, dan `hr-paketin`) ke dalam satu sistem terpusat bernama `erp-paketin`.
  - Mengkonfigurasi `erp_paketin/settings.py` untuk mengelola seluruh modul sebagai aplikasi Django individual (`apps.core`, `apps.crm`, `apps.finance`, `apps.employees`, `apps.organizations`, `apps.hr.*`).
- **Dashboard ERP Terpusat**: 
  - Membuat `apps/core/views.py` dan `templates/dashboard.html` sebagai halaman utama (Root URL `/`) yang memberikan ikhtisar performa (*high-level analytics*).
  - Menambahkan *Card KPI* yang menghitung *Total Revenue* (dari modul Finance), *Total Karyawan* (dari modul HR), dan data lainnya yang relevan sesuai tingkat akses pengguna (*Role-Based Access*).
- **Endpoint API Autentikasi (`/accounts/api/me/`)**: 
  - Membuat fungsi `api_me` di `apps/accounts/views.py` dengan respon JSON berisi detail kredensial (ID, username, email). 
  - Fungsi ini dirancang agar *Single Page Application* (seperti frontend React/Vanilla JS pada modul Finance) dapat mendeteksi sesi *SessionAuthentication* dari Django secara otomatis tanpa memerlukan login manual (JWT).
- **Modul Rekapitulasi (Recap) Finance**: 
  - Memulihkan dan menyuntikkan ulang seluruh blok HTML `<!-- PAGE: Rekap -->` (sekitar 200 baris kode yang mencakup UI *Revenue*, *Profit*, *List Customer*, dan *Asuransi*) dari repositori lama `System-Finance` ke file `templates/finance/index.html` menggunakan injeksi skrip Python `re.sub()`.

### 🐛 Fixed (Perbaikan Bug & Error)
- **Error `NoReverseMatch at / 'employees'`**: 
  - **Penyebab**: Dashboard mencoba merender URL untuk namespace `employees`, namun modul `employees` dari `hr-paketin` belum dipindahkan.
  - **Penyelesaian**: Menyalin direktori aplikasi `apps/employees` dan `apps/organizations` (termasuk *Views*, *Urls*, *Serializers*, *Forms*) dari HR ke ERP. Mendaftarkan `path('employees/', include('apps.employees.urls'))` ke dalam `erp_paketin/urls.py`. Menyalin seluruh `templates/employees/` agar tampilan HTML dapat dirender dengan sempurna.
- **FieldError pada Agregasi Total Revenue**: 
  - **Penyebab**: Terdapat panggilan fungsi `KpiFinance.objects.aggregate(Sum('credit'))`, padahal di database tabel Worksheet tidak memiliki kolom bernama `credit`.
  - **Penyelesaian**: Mengubah pemanggilan fungsi di `apps/core/views.py` menjadi `Sum('penjualan')` sesuai dengan skema model dari `KpiFinance`.
- **TemplateSyntaxError (`humanize` is not a registered tag library)**:
  - **Penyebab**: Tag `{% load humanize %}` di `dashboard.html` memicu error karena pustakanya tidak diaktifkan. Saat dicoba diperbaiki, seluruh *3rd-party apps* tak sengaja terhapus.
  - **Penyelesaian**: Me-*restore* konfigurasi `settings.py` secara penuh, lalu mendaftarkan `'django.contrib.humanize'` ke dalam blok `INSTALLED_APPS` dengan aman.
- **Konflik Halaman Login & Redirect (Error 404)**:
  - **Penyebab**: Pengguna yang sukses login diteruskan ke rute *default* Django (`/accounts/profile/`) yang tidak ada.
  - **Penyelesaian**: Menambahkan konfigurasi eksplisit di `settings.py` yaitu `LOGIN_URL = '/accounts/login/'`, `LOGIN_REDIRECT_URL = '/'`, dan `LOGOUT_REDIRECT_URL = '/accounts/login/'`.
- **Form Login Berulang di Modul Finance**:
  - **Penyebab**: Kode *client-side* di `static/finance/src/js/core/app.js` milik SPA terus memunculkan UI login karena fungsi `authManager.init()` gagal mendapatkan validasi *state*.
  - **Penyelesaian**: Endpoint `/accounts/api/me/` yang baru dibangun (sebagai *bridging*) berhasil menjawab *fetch request* dari `authManager.init()` dengan status 200 OK. Aplikasi SPA langsung menghilangkan div `#loginSection` dan menampilkan `<div id="dashboardContainer">`.

### 🔄 Changed (Perubahan Teknis Lainnya)
- **Root Routing**: Memindahkan halaman awal saat menjalankan `localhost:8002` dari yang sebelumnya memuat antarmuka Admin bawaan (`/admin`) menjadi Dashboard ERP kustom.
- **Penyesuaian UI Login**: Menyelaraskan tampilan laman `/accounts/login/` (template login Django default) agar menggunakan antarmuka modern bawaan `crm-paketin` (merah khas Paketin) yang dioptimasi dengan Bootstrap 5 dan FontAwesome.
