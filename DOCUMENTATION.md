# DOKUMENTASI TEKNIS: ERP PAKETIN CARGO

## 1. Ikhtisar Sistem (System Overview)

ERP Paketin Cargo merupakan platform *monolithic* berskala besar yang dikembangkan menggunakan kerangka kerja (framework) **Django 6.1 (Python 3.13)**. Sistem ini mengonsolidasikan tiga sistem bisnis yang dulunya terpisah (HR, CRM, dan Logistik/Finance) menjadi satu atap untuk memudahkan manajemen sumber daya, efisiensi lalu lintas data lintas divisi, dan pelacakan *Key Performance Indicators* (KPI) secara terkontrol dan terpusat (*Single Source of Truth*).

Sistem menggunakan database relasional tunggal (secara default `db.sqlite3` untuk pengembangan) untuk mengkoneksikan relasi data seperti *Sales/Karyawan* dari HR, kepada *Customer/Client* di CRM, dan *Profit/Worksheet* di Finance.

## 1.1 Standar UI/UX Global dan Shell Aplikasi

Seluruh halaman yang menggunakan `templates/base.html` memakai shell aplikasi bersama agar modul Operasional, CRM, Finance, HR, dan Master Data memiliki pola interaksi yang konsisten.

### Header, Judul Halaman (Page Title), dan Pencarian

- **Judul Menu Navbar (`.page-title`)**: Judul menu/halaman diletakkan di topbar tepat di sebelah kanan tombol toggle sidebar (`#sidebarToggle` / `<`). Judul diisi secara dinamis melalui block `{% block page_title %}` (atau fallback variabel `{{ title }}`).
- **Pencarian Global**: Terletak di bagian tengah navbar dan mengarah ke `/search/` untuk pencarian entitas bisnis (resi, manifest, klien, invoice, vendor, karyawan).
- **Quick Access / Command Palette**: Dibuka melalui ikon command pada search bar atau shortcut keyboard `Ctrl + K` / `Cmd + K`. Endpoint: `GET /api/search/?q=<kata-kunci>`. Menu yang tampil otomatis disaring sesuai hak akses role user aktif.

### Standar Action Bar & Filter Pop-up Dropdown

Seluruh halaman daftar data (list views) di semua modul menggunakan pola **Action Bar Minimalis** seragam (mengadopsi gaya CRM Paketin):
1. **Search Box Bersih (`.search-box-clean`)**: Input pencarian minimalis dengan ikon `ph-bold ph-magnifying-glass` di sebelah kiri Action Bar.
2. **Tombol Filter Pop-up**:
   - Menggunakan icon `ph-bold ph-faders` dengan dropdown melayang (`.filter-dropdown-menu`).
   - Atribut `data-bs-auto-close="outside"` memastikan menu filter tidak menutup saat interaksi dengan input tanggal/select.
   - Dilengkapi **Active Filter Dot (`.active-filter-dot`)** berwarna merah di atas tombol saat filter aktif.
   - Di dalam dropdown terdapat parameter filter modular, tombol *"Reset"*, dan tombol *"Terapkan"* (`btn-danger`).
3. **Tombol Aksi Kanan**: Mengelompokkan tombol bulk action, import/export, dan tombol primary *"Buat Baru"* (`btn-danger`).

### Notifikasi dan Action Center

- **Ikon Notifikasi Lonceng Topbar**: Menggunakan ikon **Phosphor Duotone Bell** (`ph-duotone ph-bell`) beraksen warna kuning emas/amber `#f59e0b` tanpa border outline agresif.
- **Badge Unread**: Menghitung secara real-time jumlah notifikasi belum dibaca (`unread_notifications`) untuk user yang sedang aktif.
- **Alert Operasional**: Terintegrasi di dropdown notifikasi topbar dan dibangun oleh context processor `apps/core/context_processors.py`.

Kategori alert operasional:

| Alert | Kondisi | Aksi |
|---|---|---|
| Shipment menunggu proses | Shipment berstatus `PENDING` | Membuka daftar shipment dengan filter `PENDING` |
| Transit lebih dari 48 jam | Shipment berstatus `TRANSIT` dan `updated_at` lebih lama dari 48 jam | Membuka daftar shipment dengan filter `TRANSIT` |
| Menunggu incoming destination | Shipment berstatus `INCOMING_DESTINATION` | Membuka daftar shipment terkait |
| Transfer location aktif | Shipment berstatus `TRANSFER` | Membuka daftar shipment terkait |

### Komponen Tab Status Peta Rute Distribusi (`.map-filter-pills`)

Pada modul Dashboard Core (`templates/dashboard.html`), tombol filter status rute logistik (*Semua, Pending, Outgoing, Transit, Incoming, Delivery*) mengadopsi struktur segmented tabs yang konsisten dengan tab modul atas:
- **Tab Aktif (Square Rounded Card)**: Memiliki background abu-abu `#f1f5f9` (seragam dengan tombol *Filter Detail*), border `#cbd5e1`, `border-radius: 6px`, teks gelap tebal `#0f172a`, dan bayangan halus.
- **Tab Inaktif**: Latar belakang transparan tanpa garis kotak dengan teks `#64748b` (hover: `#f1f5f9`).
- **Garis Pembatas Dinamis (`.map-pill-item::after`)**: Garis vertikal pembatas setinggi 14px (`#94a3b8`) otomatis ditampilkan di antara tab inaktif dan tersembunyi secara cerdas di sebelah tab aktif melalui `:has(.active)`.

### Design system & Global Background

- **Background Gradient Global**: Seluruh sistem ERP menggunakan latar belakang gradient lembut bernuansa sejuk (`linear-gradient(135deg, #eef5f1 0%, #e2ece6 45%, #f1f6f3 100%) fixed`) yang didefinisikan pada `templates/base.html` dan `static/css/style.css`.
- **Kontainer Halaman Transparan**: Kontainer `.main-wrapper` dan `.page-content` disetel transparan (`background: transparent !important`). Pada modul list (Shipment, Manifest, Inbound, POD, Pickup), elemen header (judul, sub-teks deskripsi, tombol aksi, dan filter bar) mengapung langsung di atas background gradient, sedangkan latar belakang putih eksklusif diterapkan hanya untuk membungkus tabel data (`table-responsive`).

Token visual utama berada di `static/css/style.css`:

- `--pk-primary` dan `--pk-primary-dark`: aksen merah brand Paketin.
- `--pk-status-pending`, `--pk-status-transit`, `--pk-status-transfer`, dan `--pk-status-success`: warna status bisnis.
- `--pk-radius-sm`, `--pk-radius-md`, dan `--pk-radius-lg`: standar radius komponen.
- `--pk-border`, `--pk-shadow-sm`, dan `--pk-shadow-md`: standar border dan elevation.

Primitive yang dapat digunakan oleh template baru:

| Class | Kegunaan |
|---|---|
| `.pk-card` | Container konten dengan border, radius, dan shadow standar |
| `.pk-card-header` | Header card dengan padding dan separator konsisten |
| `.pk-btn` | Dasar tombol dengan alignment dan focus state standar |
| `.pk-table` | Tabel dengan sticky header dan hover row |
| `.pk-status` | Badge status berbentuk pill yang konsisten |
| `.pk-empty-state` | Tampilan kosong yang informatif |

Untuk status, gunakan kombinasi `.pk-status` dengan modifier seperti `.pk-status-pending`, `.pk-status-transit`, `.pk-status-transfer`, atau `.pk-status-success`. Hindari hardcode warna baru di template tanpa alasan bisnis yang jelas.

### Pedoman konsistensi antar modul

Setiap menu boleh memiliki konten berbeda, tetapi mengikuti urutan konseptual berikut:

1. Header halaman dan konteks modul.
2. Action/filter bar.
3. Summary atau KPI yang relevan.
4. Konten utama berupa tabel, form, timeline, chart, atau map.
5. Empty state, loading state, dan error state yang jelas.

Perbedaan konten tidak boleh mengubah aturan dasar typography, spacing, warna status, bentuk tombol, border, dan focus state.

### File teknis terkait

- `templates/base.html`: shell, header, search, command palette, notification dropdown, dan user menu.
- `static/css/style.css`: token dan primitive design system global.
- `static/js/main.js`: shortcut `Ctrl + K`, pembukaan modal, debounce pencarian, dan render hasil.
- `apps/core/views.py`: data command palette role-aware dan universal search.
- `apps/core/context_processors.py`: akses modul, branch, unread notification, dan operational alerts.
- `erp_paketin/urls.py`: route `/search/`, `/api/search/`, dan route bahasa.

## 2. Arsitektur Hibrida (Hybrid Architecture)

Tidak seperti aplikasi tradisional pada umumnya, ERP ini mengadopsi arsitektur gabungan (Hibrida):

1. **Server-Side Rendered (MPA)**:
   - Digunakan untuk modul **Core Dashboard, HR, dan CRM**.
   - Di-*render* sepenuhnya oleh backend (menggunakan *Django Templates*, Bootstrap 5, dan Crispy Forms).
   - Pengolahan logika, penarikan data dari ORM, dan penyortiran terjadi pada saat *page load*. 
   
2. **Client-Side Rendered (SPA)**:
   - Digunakan secara eksklusif untuk modul **Finance/Worksheet**.
   - Modul ini pada dasarnya adalah aplikasi Vanilla JS (*Single Page Application*) yang bersarang di dalam *view* Django. UI tidak pernah me-*reload* halaman browser. Seluruh proses (menambah baris Excel, menghitung *margin*, menampilkan grafik rekapitulasi) dieksekusi secara instan menggunakan JavaScript (`static/finance/src/js/`).
   - SPA ini berkomunikasi asinkron (*fetch API*) dengan **Django REST Framework** (`apps/finance/urls.py` -> `api/`) untuk menyimpan perubahan ke basis data.

## 3. Pemetaan Direktori Modul (Module Layouts)

Seluruh logika sistem dipecah menjadi beberapa *Django Apps* mandiri yang diletakkan di dalam *directory* `apps/`.

### 3.1 `apps.core`
- **Fungsi**: Titik pusat dan *landing page* (`/`).
- **Fitur**: Memuat `dashboard.html` yang menarik statistik tingkat tinggi dari semua aplikasi lain menggunakan fungsi `.aggregate()` dari ORM Django (seperti menghitung `total_revenue = KpiFinance.objects.aggregate(Sum('penjualan'))`).

### 3.2 `apps.finance`
- **Fungsi**: Pusat logistik operasional & penghitungan profit (Worksheet).
- **Fitur**:
  - `models.py`: Menyimpan model utama `KpiFinance` (Awb, Surcharge, Penerima, Aktual, Vol, Harga, Penjualan).
  - `views.py` (API): Terdapat rutin *ViewSets* (`KpiFinanceViewSet`, `CrmClientViewSet`) untuk melayani *requests* dari frontend SPA.
  - SPA Layout: Di-host pada file besar `templates/finance/index.html` dan direpresentasikan oleh puluhan script spesifik (misal: `recap.js`, `table.js`, `chart.js`).

### 3.3 `apps.crm`
- **Fungsi**: *Customer Relationship Management*.
- **Fitur**: Memelihara siklus prospek (Leads), klien terdaftar (Clients), dan kontrak layanan. Seringkali di-*reference* oleh modul Finance saat *data entry* AWB.

### 3.4 Modul Sumber Daya Manusia (HR)
Direktori ini dipecah demi spesifisitas tingkat granular:
- `apps.employees` & `apps.organizations`: Mengelola struktur *Tree* perusahaan, posisi jabatan, izin (*Roles*), dan daftar data *Employee*.
- `apps.hr.attendance`: Sistem absensi (masuk/pulang).
- `apps.hr.leave`: Permohonan dan persetujuan cuti.
- `apps.hr.documents` & `apps.hr.approvals`: Dokumen legal dan matriks persetujuan (contoh: persetujuan pencairan dana logistik).

## 4. Sistem Autentikasi Jembatan (Bridged Auth System)

Salah satu tantangan sistem Hibrida adalah menyamakan *state* login antara sesi peramban tradisional dan aplikasi asinkron REST.

**Langkah demi Langkah (Step-by-Step Flow):**
1. Pengguna membuka URL ERP (`localhost:8002/`). Jika tidak ada sesi aktif (cookie *sessionid* tidak ditemukan), sistem `django.contrib.auth` otomatis me-lempar (*redirect*) pengguna ke `/accounts/login/`.
2. Pengguna memasukkan kredensial (contoh: Username `Superadmin`). Setelah verifikasi kata sandi di backend sukses, Django menerbitkan cookie sesi yang diamankan (*HttpOnly*).
3. Pengguna mengakses `/finance/`.
4. *Frontend Router* (SPA JavaScript `app.js`) menyala dan curiga apakah pengguna telah divalidasi. 
5. Skrip memanggil objek `authManager.init()`, yang akan menembakkan permintaan `GET /accounts/api/me/` dengan membawa *credentials: 'include'* (cookie).
6. Di backend, URL tersebut dijaga oleh *decorator* `@login_required`. Karena *cookie* sah, backend merespon HTTP 200 OK beserta payload profil (berformat JSON).
7. Menerima HTTP 200 OK, SPA sadar pengguna telah lolos autentikasi dan membi-pass form login (menyembunyikan `#loginSection`) lalu menampilkan *Spreadsheet Worksheet* seutuhnya.
8. Seluruh operasi CRUD di Worksheet selanjutnya (ke endpoint `/finance/api/...`) diproteksi menggunakan metode kombo `SessionAuthentication` dan `JWTAuthentication` yang diatur via `REST_FRAMEWORK` di `settings.py`.

## 5. Arsitektur Master Data Fleksibel (Hybrid Pattern)

ERP ini menerapkan pendekatan pengelolaan referensi data (*Master Data*) yang sangat unik pada model `Coverage` (Rute/Cakupan Kota) dan `Service` (Layanan). Pendekatan ini dinamakan pola **Hibrida + Auto-Create**.

Sistem ini diciptakan untuk menjawab kebutuhan keluwesan (*agility*) di lapangan:
1. **Pola Standar (Normal Flow)**: Di modul CRM dan Operasional, tim memasukkan rute melalui komponen *Smart Dropdown*. Jika rute dipilih dari basis data, referensi silang (FK `origin_coverage` / `destination_coverage`) akan diikat, dan tarif standar dapat ditarik secara otomatis.
2. **Pola Auto-Create (Drafting)**: Jika tim lapangan harus mengirim ke desa terpencil yang belum pernah ada di database, mereka cukup mengetik nama desa tersebut di *Smart Dropdown* dan menekan `Enter`. Sistem (*backend parser* di form) akan secara gaib membuatkan rekaman data Master baru dengan label `is_verified = False` (status *Draft*), membiarkan resi tercetak saat itu juga, sembari memberi tahu Admin Pusat untuk menstandarisasi harganya kelak.
3. **Pola Bypass (Charter / Kargo Khusus)**: Untuk proyek *charter* helikopter atau kargo sekali jalan yang penamaannya sangat kustom dan tidak ingin dikotorkan ke dalam tabel Master Data, pengguna dapat menyalakan saklar **"Kargo Khusus"** (`is_manual_override = True`). Saat saklar ini aktif, seluruh *dropdown* berubah menjadi input teks polos tanpa validasi relasi, memberikan kebebasan mutlak *(100% decoupling)* bagi divisi terkait.

### 5.1 Pemfilteran Master Data (Reference Tables vs Transactional Entities)
Pada `apps/master/views.py`:
- **Tabel Referensi Statis** (*Bank, Branch, Coverage, Service, Price, Vehicle, Vendor*): Penyaringan status (`is_active`) berdiri independen tanpa filter rentang tanggal `created_at` otomatis. Hal ini mencegah data referensi statis tereliminasi saat filter default dikirimkan.
- **Entitas Transaksional**: Filter rentang tanggal tetap tersedia pada modul transaksional (Shipment, Manifest, Worksheet, Invoices).

## 6. Panduan Pengembangan Selanjutnya (Next Phase: Logistik)

Untuk *Fase 4 (Modul Operasional)* yang merencanakan fitur pengiriman dan pembuatan nomor resi, pedoman berikut harus dipatuhi:

1. **Buat Aplikasi Baru**: Gunakan sintaks `python manage.py startapp logistics`. Pindahkan folder hasil ke dalam subdirektori `apps/`.
2. **Model Database**: Buat relasi *Foreign Key* (FK) yang merujuk pada `finance.KpiFinance` jika diperlukan, agar tidak terjadi tumpang tindih rekam logistik.
3. **Template (UI)**: Disarankan untuk `extend 'base.html'` yang sudah ada, guna mempertahankan bentuk *Sidebar* (navbar kiri) agar serasi dengan HR dan CRM. Kecuali jika Anda memerlukan *spreadsheet* yang super dinamis, barulah kembangkan sebagai SPA seperti modul Finance.
7. **Pendaftaran URL**: Pastikan URL modul ditambahkan (`path('logistics/', include('apps.logistics.urls'))`) di file *root router* `erp_paketin/urls.py` dan namespace dideklarasikan dengan jelas di tiap tautan HTML *sidebar*.

## 7. Arsitektur Operasional (Tracking & Manifesting)

Pada modul operasional, arsitektur pemrosesan data (seperti Pembuatan Manifest dan Riwayat Tracking) mengedepankan performa dan integritas historis.

### 7.1 Identifikasi Klasifikasi Manifest (Robust Sub-typing)
Struktur *Transfer Location Manifest* di dalam sistem terdiri dari banyak jenis (Vendor, Udara, Laut, dan Darat/Internal). Daripada menyimpan tipe sub-manifest secara kaku ke dalam satu *database field* yang berpotensi ditimpa form HTML (misal: `<select name="transport_mode">`), sistem ERP menggunakan pendekatan deterministik (*Smart Property Getter*):

- `@property def get_transfer_mode(self):`
  Sistem mendeteksi secara *real-time* dengan memprioritaskan ketersediaan atribut *Foreign Key* atau karakter khusus. Jika ada `self.vendor`, maka itu pasti **Vendor Manifest**. Jika ada `self.flight_no`, maka **Air Freight**, dst. Ini mengizinkan pengguna memilih "Moda Darat" di form Vendor Manifest tanpa merusak klasifikasi *root* manifest tersebut saat fungsi *Update / Edit Form* dipanggil.

### 7.2 Optimalisasi Render Log Pemindaian (Incoming Tracking)
Untuk fitur riwayat logistik (*Tracking* atau *Incoming Destination*):
1. **Tidak Melakukan Iterasi pada Tabel Log (Tracking)**: Karena satu nomor Resi bisa dipindai puluhan kali, me-*looping* langsung *queryset Tracking* akan menciptakan tabel yang menduplikasi baris Resi yang sama.
2. **Reverse Relation (Prefetching)**: Tabel List selalu dibangun dengan melakukan iterasi terhadap *parent* tabel (`Shipment.objects.all()`), namun dengan sisipan `.prefetch_related('tracking_history')`.
3. **Template Logic**: Di dalam iterasi tabel, kita cukup memanggil `{% with latest_scan=item.tracking_history.first %}` (yang sebelumnya sudah diurutkan dari model via `ordering = ['-timestamp']`) untuk merender waktu/lokasi scan terakhir dari tiap paket tanpa menimbulkan duplikasi baris.

### 7.3 Arsitektur POS / Pembuatan Data Resi Terpadu
Modul pembuatan resi (`shipment_form_resi.html` dan turunannya) dibangun menggunakan pendekatan arsitektur *Rich Form Integration* untuk menjembatani CRM dan perhitungan operasional berat volumetrik:

1. **Auto-Fill Dataset Pintar (Frontend Master Integration)**:
   Dropdown pemilihan *Client* di-render, lalu saat event *onchange* terjadi, *Vanilla Javascript* akan memanggil API backend (`/operations/api/get-client-detail/`) untuk mem-*fetch* data master klien secara *real-time*. Hasil tanggapan (JSON) kemudian disuntikkan secara instan ke kolom Shipper/Pengirim (termasuk Alamat, otomatis merender ulang dropdown `Select2` untuk Kota dan Kecamatan). 
   - **HTML Attribute State Preservation**: Untuk mengatasi *race condition* di mana kolom Kecamatan (District) tereset kembali akibat keterlambatan respons AJAX, sistem menyimpan nilai incaran (*intended value*) ke dalam atribut statis (`data-current-val` sebagai HTML attribute, bukan sekadar cache DOM jQuery). Hal ini menjamin nilai autofill tetap persisten dan akurat saat *promise* AJAX terselesaikan.
   - Pendekatan tersentralisasi ini menjamin data operasional selalu *in-sync* dengan Modul Data Master Customer.
2. **Dynamic Pricing & Volumetric Engine**:
   - Algoritma perhitungan tarif terpisah dalam logika *Frontend* dan *Backend* (sebagai validasi mutlak).
   - *Divisor* pembagi volume disuntikkan secara aman melalui JSON (`service_divisors = json.dumps(Shipment.SERVICE_DIVISOR)` di views.py).
   - Sistem akan melakukan komparasi *real-time*: `Chargeable Weight = Max(Aktual, (Panjang × Lebar × Tinggi) / Divisor)`. 
   - Fitur Multi-Colly dijalankan melalui interaksi DOM JavaScript yang membuat form *Item* baru dalam akordion. Saat formulir dikirim (POST), `ShipmentItemFormSet` akan secara otomatis memecah 1 Form Induk (1 Resi Utama) menjadi banyak baris `ShipmentItem` (anak barang) dan membuatkan *Barcode Fisik* berurut (`ShipmentColly`) secara *looping* di dalam `pos_credit` (contoh: `RES-0001-1-01`).
3. **Penyelarasan Edit Resi & Recalculation Lifecycle**:
   - Pada form edit resi (`shipment_update`), sistem secara otomatis menjalankan kalkulasi ulang `volume_weight`, `chargeable_weight`, dan `packing_cost` dari seluruh item anak (`ShipmentItem`) dan koli induk saat data disimpan, menjaga konsistensi data finansial pengiriman.
   - **Safe Context & Template Fallbacks**: Pada form pembuatan resi baru (`pos_cash` dan `pos_credit`), context view mengirimkan `shipment: None` secara eksplisit, dan template `shipment_form_resi.html` menerapkan blok kondisional `{% if shipment %}` dengan fallback aman ke `form.*.value` untuk mencegah exception `VariableDoesNotExist`.

### 7.4 Arsitektur Generator Nomor Resi Berbasis Cabang (Branch-Based)
Sistem penomoran Resi (AWB) tidak lagi menggunakan *prefix* tunggal yang statis. Melainkan bersifat *hybrid* dengan mendeteksi identitas cabang pembuat resi:
1. **Identifikasi Cabang & Klien**: Sistem mengekstrak kode cabang dari profil karyawan yang sedang *login* melalui relasi model `request.user.employee_profile.branch.code`. Jika tidak ditemukan, sistem akan menggunakan *fallback* `BKS`. Selain itu, kode kustomer unik juga diekstrak dari pilihan *Client*.
2. **Kombinasi Logika Tanggal, Klien & Iterasi**: Nomor cabang lalu disambungkan dengan metode POS (seperti CRD untuk *Credit*), format tanggal, ID kustomer, dan iterasi harian. Format barunya adalah: `[KODE_CABANG]-CRD-[TANGGAL]-[KODE_CUSTOMER]-[NOMOR_URUT]`. Contoh: `BKS-CRD-20260831-CUST001-0001`.
3. **Filter Kuat & Akurat**: Validasi iterasi harian (untuk memastikan nomor terakhir urutan) difilter menggunakan query `.filter(resi_number__contains=f"CRD-{date_str}")`, guna menjamin iterasi urutan (0001, 0002, dst) tetap berlanjut presisi meski format UUID kustomernya berubah-ubah pada hari yang sama.

### 7.5 Arsitektur Rendering PDF & Estetika UI (Operasional)
1. **Engine Cetak AWB (`xhtml2pdf`)**: Pembuatan dokumen resi cetak termal/kertas (PDF AWB) menggunakan *library* `xhtml2pdf`. Mengingat *engine* ini rentan terhadap kesalahan *wrapping* dan memiliki batasan CSS, aturan berikut wajib diterapkan:
   - **Tabel Bersarang (Nested Tables)**: *Layout* krusial (Barcode, QR Code, Logo) wajib dibangun sepenuhnya menggunakan struktur tabel bersarang atau baris terikat secara rigid (*side-by-side*) agar tidak *overflow*.
   - **Garis Putus-Putus (Dotted/Dashed Cutting Lines)**: Garis batas seperti jalur gunting antar salinan pada A4 menggunakan elemen `<div style="border-bottom: 1px dashed #444444; height: 1px; margin: 1.5mm 0; font-size: 1px; line-height: 1px;">&nbsp;</div>`. Karakter `&nbsp;` wajib ada di dalam `<div>` agar `xhtml2pdf` memproses dan merender garis potong tersebut.
   - **Kompaktifikasi AWB 3-in-1 Kertas A4**: Untuk format A4 yang menumpuk 3 salinan AWB dalam 1 halaman:
     - `@page { size: a4 portrait; margin: 2mm 4mm; }` disetel minimal.
     - Ketinggian cell tanda tangan dan rincian biaya dibatasi secara ketat agar total tinggi 3 salinan tidak melebihi batas vertikal A4, mencegah salinan ke-3 terdorong ke halaman ke-2.
     - **Tabel Multi-Koli Slicing**: Pada tabel rincian berat dan dimensi, data item dipotong menggunakan filter `|slice:":2"` (maksimal 2 baris teratas) ditambah 1 baris ringkasan `+N Koli` jika jumlah koli > 2. Hal ini menjaga konsistensi tinggi tabel terlepas dari seberapa banyak jumlah koli pengiriman.
   - **Penataan QR Code & Logo ISO**: QR Code dan Logo Sertifikasi ISO diletakkan sejajar secara horizontal di atas tabel rincian biaya dengan `margin-left: 8px` pada logo ISO dan ukuran proporsional (`width="42"` untuk QR dan `width="130"` untuk ISO) agar tampil rapi tanpa bertumpuk (*overlapping*).
   - **Kompaktifikasi Ukuran Kertas Spesifik (100x150, dll)**: Standar ukuran media cetak thermal ditetapkan secara absolut via *directive* `@page` (contoh: `@page { size: 100mm 150mm; }`). Seluruh margin dan padding pada baris *spacer* atau area *footer* disetel minimal (0px - 2px) untuk mencegah konten meluap (*spill over*) ke halaman berikutnya.
2. **Pembersihan String Level Model (Regex Cleaning)**: Menghindari manipulasi *string* kasar di *template* Django. Pembersihan kata imbuhan pada wilayah (seperti "KOTA " atau "KABUPATEN ") yang rentan merusak layout tabel cetak atau mengacaukan pencarian TLC di *database*, dilakukan menggunakan ekspresi reguler (*Regular Expressions* `re.sub`) dengan mode *case-insensitive* `(?i)` yang ditanamkan langsung pada `@property` (`get_city_origin`, `get_city_dest`) model `Shipment` dan `Manifest`. Ini menjamin kekokohan *data rendering*.
3. **Standardisasi Komponen UI Tab (Chrome-Style)**: Penataan antarmuka menu yang menggunakan multi-tab (contoh: Menu Pick Up) membuang arsitektur `nav-tabs` Bootstrap standar, beralih pada implementasi *flat tab design* premium bergaya Google Chrome:
   - **Rata Kiri Presisi**: Kontainer `.nav-tabs-custom` menggunakan `padding: 0 !important` dan `gap: 0 !important` agar garis batas kiri tab pertama jatuh tepat sejajar (`0px offset`) pada garis batas kontainer tabel data di bawahnya.
   - **Penyatuan Warna Tab Aktif & Header Tabel**: Tab aktif dan header tabel (`thead th`) menggunakan warna yang sama (`#f8fafc` dengan garis `#eaedf1`). Garis bawah tab aktif ditutup (`border-bottom: 1px solid #f8fafc`) sehingga tab menyatu mulus langsung ke dalam tabel.
   - **Tab Inaktif Borderless & Garis Pemisah Vertikal**: Tab yang tidak aktif tidak memiliki kotak samping (*borderless*) dan dipisahkan oleh garis pembatas vertikal (`::after` setebal `2px`, tinggi `20px`, warna `#94a3b8`) di antara setiap tab serta pada ujung tab terakhir. Garis ini otomatis disembunyikan di dekat tab aktif atau saat tab di-*hover*.
   - **Vibransi Ikon & Teks**: Seluruh ikon dan font teks tetap tajam dan penuh warna (100% *opacity*) tanpa efek buram (*muted*).

### 7.6 Arsitektur Universal Void
1. **Single Entry Point**: Seluruh proses pembatalan resi disatukan di bawah rute `/operations/void/credit/` (*Universal Void*), mengeliminasi sub-menu bercabang dan menyembunyikan opsi cash yang tidak digunakan.
2. **Pembersihan Istilah AWB**: Istilah "AWB" dihapus dari sidebar, tombol, judul header, dan tag log audit (`[VOID]`) demi standardisasi nomenklatur resi pengiriman di seluruh ERP.
3. **Audit Trail Otomatis**: Setiap eksekusi pembatalan di-handle melalui helper `log_action` di `apps.audit.utils` yang merekam user pelaksana, nomor resi, dan alasan pembatalan secara rinci.

## 8. Arsitektur Dashboard Utama & Peta Tracing Logistik Nasional

Dashboard utama (`templates/dashboard.html` di `apps.core`) dirancang sebagai pusat kendali operasional dan analitik eksekutif dengan struktur multi-slide modul interaktif.

### 8.1 Navigasi Multi-Slide Berbasis Peran (Role-Based Adaptive Dashboard)
1. **Pendaratan Otomatis Sesuai Hak Akses (*Role Landing*)**:
   - Sistem mendeteksi grup dan peran akun pengguna saat login dan otomatis mengaktifkan tab modul utama yang relevan:
     - **Operasional / CS / Driver**: Otomatis mendarat di slide **Operasional** (`#panelSlide-3`).
     - **Sales / CRM**: Otomatis mendarat di slide **Sales** (`#panelSlide-2`).
     - **Finance / Kasir**: Otomatis mendarat di slide **Finance** (`#panelSlide-4`).
     - **Vendor Management (VM)**: Otomatis mendarat di slide **Vendor Management** (`#panelSlide-6`).
     - **HR & GA**: Otomatis mendarat di slide **HRGA** (`#panelSlide-5`).
     - **Superadmin / Direksi**: Memiliki akses penuh ke seluruh slide termasuk slide **Ringkasan Utama** (`#panelSlide-1`).
2. **Standardisasi Penamaan Modul**:
   - Menu dan tab distandardisasi menjadi: `SALES`, `OPERASIONAL`, `FINANCE`, `HRGA`, dan `VENDOR MANAGEMENT`.

### 8.2 Desain Tab Chrome Seragam & Transisi Meluncur (Gliding Motion)
1. **Dimensi Seragam (*Uniform Tab Width*)**:
   - Setiap tombol tab navigasi memiliki lebar tetap yang seragam (`min-width: 175px`), menjaga keseimbangan tata letak baris tab.
2. **Indikator Aktif Meluncur (*Sliding Active Indicator / Gliding Pill*)**:
   - Background tab aktif bergerak meluncur (*glides*) secara dinamis di bawah tab yang dituju menggunakan kalkulasi koordinat `offsetLeft` & `width` dengan kurva `cubic-bezier(0.4, 0, 0.2, 1)` dalam durasi `0.22s`.
3. **Transisi Panel Terarah (*Directional Slide Transition*)**:
   - Konten modul bergeser lembut (*slide-in* sejauh 12px) dari arah yang sesuai dengan posisi tab:
     - Bergeser dari kanan (`dashboardSlideRight`) saat menuju tab di sebelah kanan ($target > previous$).
     - Bergeser dari kiri (`dashboardSlideLeft`) saat menuju tab di sebelah kiri ($target < previous$).
4. **Pembatas Vertikal Ujung-ke-Ujung (*Edge-to-Edge Dividers*)**:
   - Garis pembatas vertikal (`1px`, tinggi `16px`, warna `#94a3b8`) diterapkan di sisi paling kiri sebelum tab pertama (`.nav-item:first-child::before`) dan di sisi kanan setiap tab (`.nav-item::after`).
   - Garis pembatas otomatis memudar (*opacity 0*) saat tab aktif atau di-*hover* untuk memberikan kesan bersih dan rapi.
5. **Penyatuan Visual Tanpa Garis Atas (*Seamless Integration*)**:
   - Aksen garis merah atas pada tab aktif ditiadakan; tab aktif menyatu langsung (*seamless white transition*) dengan kartu konten di bawahnya.

### 8.3 Engine Peta Rute Distribusi & Tracing Logistik Nasional
Peta pelacakan distribusi nasional dibangun di atas Leaflet.js dengan konfigurasi performa tinggi:

1. **Layer Tile ArcGIS Bebas Watermark & Bebas Blokir (*Watermark-Free*)**:
   - Menggunakan layer **ArcGIS Canvas Dark Gray (Base + Reference)** (`server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}` dan `World_Dark_Gray_Reference`) yang 100% stabil untuk akses web publik tanpa batasan *tile usage policy* dan tanpa permintaan *API Key*.
2. **Filter Warna Biru Midnight (*Sidebar Navy Blue Tint*)**:
   - Mengaplikasikan filter kromatik CSS pada pane tile peta:
     ```css
     #indoMap .leaflet-tile-pane {
         filter: sepia(100%) hue-rotate(185deg) saturate(380%) brightness(88%) contrast(115%);
     }
     ```
   - Transformasi ini menghasilkan warna lautan dan daratan bernuansa *Deep Midnight Navy* yang serasi dengan palet warna sidebar ERP (`#1a1a2e` s/d `#16213e`).
3. **Presisi Titik, Vektor Normal Geodesik & Corridor Track Offset**:
   - **CircleMarker Layering (`pane: 'markerPane'`)**: Titik kota asal (*Origin*) dan tujuan (*Destination*) dirender menggunakan `L.circleMarker` (`radius: 7`, `weight: 2.5`, `color: #ffffff`) dan dimasukkan ke dalam `markerPane` Leaflet ($z\text{-index } 600$). Hal ini memastikan lingkaran penanda kota selalu berada rapi di atas garis rute (*polylines* di `overlayPane` $z\text{-index } 400$) sehingga tidak ada ujung garis (*stroke-linecap*) yang menembus keluar.
   - **Algoritma Vektor Normal Geodesik & Pemisahan Busur Paralel**:
     Untuk rute antara dua titik koordinat $(lat_1, lng_1)$ dan $(lat_2, lng_2)$, vektor jarak dihitung:
     $$\Delta lat = lat_2 - lat_1, \quad \Delta lng = lng_2 - lng_1, \quad dist = \sqrt{\Delta lat^2 + \Delta lng^2}$$
     Vektor normal satuan yang tegak lurus terhadap arah lintasan:
     $$normLat = -\frac{\Delta lng}{dist}, \quad normLng = \frac{\Delta lat}{dist}$$
     Tinggi busur disesuaikan dengan indeks status pada koridor yang sama ($curveOffset$):
     $$totalHeight = \min(dist \cdot 0.12, 1.8) + (curveOffset \cdot 0.4)$$
     Titik kurva untuk $t \in [0, 1]$ dihitung sebagai:
     $$lat_t = lat_1 + \Delta lat \cdot t + normLat \cdot \sin(t \cdot \pi) \cdot totalHeight$$
     $$lng_t = lng_1 + \Delta lng \cdot t + normLng \cdot \sin(t \cdot \pi) \cdot totalHeight$$
     Karena $\sin(0) = 0$ dan $\sin(\pi) = 0$, seluruh garis rute paralel selalu berawal dan berakhir presisi di pusat titik kota tanpa pergeseran. Jika dalam satu koridor terdapat status ganda (misal `PENDING` dan `PICKUP`), garis akan terpisah melengkung berdampingan sehingga warna tidak bercampur (*color-mixing prevention*).
4. **Interaktivitas Daftar Resi & Navigasi Cepat (Interactive Payload)**:
   - Payload JSON dari backend (`apps.core.views.dashboard_view`) memuat daftar resi aktif (`resis`) per rute.
   - Mengklik garis rute membuka popup dengan daftar resi, tipe layanan, rute pengirim $\rightarrow$ penerima, jumlah koli, dan berat barang yang terhubung langsung ke `/operations/shipments/<pk>/`.
   - Mengklik titik kota menampilkan ringkasan resi asal atau resi tujuan pengiriman.
5. **Kontrol Header Terpadu & Minimalis**:
   - Menghilangkan widget melayang (HUD) yang memakan ruang peta.
   - Filter status (*Semua, Pending, Outgoing, Transit, Incoming, Delivery*), badge total rute aktif, dan input pencarian kota (*Fly-to*) terintegrasi rapi pada *card header* peta.

## 9. Arsitektur Pusat Laporan Operasional (Reporting Center)

1. **Standardisasi Label Aksi**:
   - Seluruh modul laporan (SLA Report, Manifest Report, Delivery Report, dll.) menggunakan label aksi terstandarisasi **"Preview"** pada tombol filter data.
2. **Robust SLA Resolution & Data Fallbacks**:
   - View laporan SLA (`apps/operations/views.py` -> `shipment_sla_report`) memproses data kalkulasi durasi SLA pengiriman dengan penanganan aman terhadap relasi master coverage dan penamaan label kota yang fleksibel.
3. **Penyelarasan Tampilan Filter**:
   - Form filter laporan menggunakan tata letak *inline card* yang ringkas, dengan field pilihan Asal, Tujuan, Layanan, Pembayaran, Status, dan Rentang Tanggal yang seragam lintas modul.

## 10. Standar Modul Finance & Cetak Dokumen Invoice PDF

Sistem cetak faktur penagihan (*Invoice*) dibangun menggunakan kerangka kerja `xhtml2pdf` (PISA Engine) dengan spesifikasi presisi A4 portrait (`@page { size: a4 portrait; margin: 10mm 15mm 10mm 15mm; }`) yang dirancang untuk kepatuhan ketat 1 halaman utuh (*zero unnecessary spillover*).

### 10.1 Arsitektur Layout Header & Status Visual
1. **Header Presisi 3-Kolom**:
   - Kolom kiri (38%): Memuat logo surat resmi (`static/img/logo-surat.png`) dan profil legal perusahaan (`PT. Amanah Cargo Jaya Mandiri`, alamat, dan kontak).
   - Kolom tengah (27%): Memuat judul dokumen yang sejajar vertikal dengan bagian atas logo.
   - Kolom kanan (35%): Memuat *Info Box* metadata invoice (No. Invoice, Tanggal Cetak, Sales, dll.) dengan border `#aaaaaa` yang rapat ke baris identitas klien di bawahnya.
2. **Badge Status DRAFT Bertumpuk (*Stacked DRAFT Title*)**:
   - Ketika status invoice masih `DRAFT`, template menampilkan label `DRAFT` (10pt, warna `#888888`, letter-spacing 1px) bertumpuk tepat di atas judul `INVOICE` (16pt, bold).
   - Ketika status telah `APPROVED` / disetujui, label draft otomatis hilang dan hanya menyisakan judul `INVOICE` tunggal yang tegas.

### 10.2 Tabel Rincian Biaya & Kotak Terbilang
1. **Harmonisasi Garis & Outline**:
   - Seluruh border pada tabel keterangan (`.items-table`) dan kotak terbilang (`.terbilang-box`) menggunakan warna abu seragam `#aaaaaa` dengan ketebalan `0.5px`.
   - Kotak terbilang menggunakan `border-top: none` dan `margin-top: 0px` sehingga garis luarnya menyatu langsung ke baris *Grand Total* tabel di atasnya tanpa celah ganda.
   - Kolom label "Terbilang" dan teks nilai terbilang dipisahkan oleh garis vertikal `#aaaaaa` yang rapi.

### 10.3 Rekening Bank, Tanda Tangan & Footer
1. **Tabel Rekening Bank 1-Baris**:
   - Kolom BANK dialokasikan selebar 68% dan NOMOR REKENING 32% pada kontainer bank (62% dari lebar halaman), memastikan nama bank resmi dan nomor rekening tampil rapi dalam 1 baris tanpa terpotong (*text collision prevention*).
2. **Hierarki Tanda Tangan & Referensi**:
   - Penandatangan `(DPT. KEUANGAN)` dipertegas dengan ukuran font 9pt dan garis bawah (`<u>`).
   - Teks `Referensi / Reference` diperbesar menjadi 9.5pt untuk kemudahan pelacakan bukti pembayaran.
3. **Presisi Batas Bawah Footer Copyright**:
   - Elemen footer copyright diberi margin atas presisi `100px` dengan border pemisah `#d0d5dd`, memastikan posisinya menempel pas di batas bawah halaman A4 tanpa tumpah ke halaman kedua.

### 10.4 Penanganan Nama File Unduhan & Judul Tab Browser
1. **Sanitasi Karakter Garis Miring (`/`)**:
   - Nomor invoice umumnya mengandung karakter slash (misal `INV/2026/09/0001`). Karena karakter `/` dan `\` tidak valid dalam header HTTP `Content-Disposition`, backend (`apps/finance/views.py` -> `invoice_pdf`) otomatis menggantinya dengan `-` (`Invoice_INV-2026-09-0001.pdf`).
   - Mencegah browser (Chrome, Edge, Firefox) dan Windows mengabaikan nama file dan menamai file unduhan sebagai `pdf` atau `pdf.pdf`.
2. **Metadata Title Tag & Named URL**:
   - Tag `<title>Invoice {{ invoice.invoice_number }}</title>` disematkan pada `<head>` dokumen PDF agar terbaca sebagai metadata judul dokumen pada tab browser dan Adobe Acrobat viewer.
   - Tersedia rute named PDF URL `path('invoices/<int:invoice_id>/pdf/<str:filename>', invoice_pdf, name='invoice_pdf_named')` di `apps/finance/urls.py` untuk kompatibilitas tautan langsung.

## 11. Arsitektur Keamanan & Standarisasi OWASP

Sistem ERP Paketin mengimplementasikan pertahanan keamanan berlapis (*defense-in-depth*) yang memenuhi standar OWASP Top 10:

### 11.1 Perlindungan dari SQL Injection (SQLi)
- Seluruh manipulasi basis data dilakukan melalui **Django ORM Parameterized Queries** (`filter()`, `select_related()`, `prefetch_related()`).
- Nilai input pengguna dipisahkan secara ketat dari kompilasi query SQL sehingga kebal dari teknik injeksi SQL.

### 11.2 Proteksi Autentikasi & Brute-Force Rate Limiting
- **CustomLoginView**: Diimplementasikan pada `apps/core/security.py` dengan mekanisme *cache rate-limiting* otomatis.
- **Batas Percobaan**: Maksimal 10 percobaan gagal per IP/Username dalam jendela waktu 5 menit. Jika terlampaui, request ditolak secara aman dengan pesan error protektif.
- **Password Complexity**: Kebijakan sandi minimal 8 karakter dengan pencegahan kesamaan atribut pengguna, password umum, dan numerik murni.

### 11.3 Manajemen Token JWT & Keamanan Sesi
- **Access Token Lifetime**: Diatur menjadi **60 menit** (dari sebelumnya 7 hari) untuk memitigasi risiko pembajakan token pada perangkat klien.
- **Token Rotation**: `ROTATE_REFRESH_TOKENS = True` memperbarui refresh token secara berkala.
- **Security Headers & Cookie**: Mengaktifkan `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS = 'SAMEORIGIN'`, serta `SESSION_COOKIE_SECURE` dan `CSRF_COOKIE_SECURE` saat mode produksi.

### 11.4 Halaman Error Terisolasi (No Stacktrace Leakage)
- Template khusus `templates/404.html` dan `templates/500.html` menyajikan antarmuka ramah pengguna berdesain brand Paketin tanpa membocorkan trace error internal aplikasi.

---

## 12. Standar Penyimpanan Aset & Sanitasi Input

### 12.1 Manajemen Aset Statis & Dinamis
1. **Static Files**:
   - `STATIC_URL = '/static/'` dan `STATICFILES_DIRS = [BASE_DIR / 'static']`.
   - `STATIC_ROOT = BASE_DIR / 'staticfiles'` sebagai target kompilasi produksi via `python manage.py collectstatic`.
2. **Media Files (User Uploads)**:
   - `MEDIA_URL = '/media/'` dan `MEDIA_ROOT = BASE_DIR / 'media'`.
   - Partisi subfolder domain: `payment_proofs/`, `pod_media/%Y/%m/`, `pod_failed/`, `pickup_docs/`, `contracts/%Y/%m/`, `employee_docs/`.
3. **File Upload Validator (`apps/core/validators.py`)**:
   - Membatasi ukuran berkas maksimal 5 MB untuk gambar dan 10 MB untuk dokumen.
   - Whitelist ekstensi yang diizinkan (`.pdf`, `.jpg`, `.jpeg`, `.png`, `.webp`, `.docx`, `.xlsx`).
   - Limit memori `FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB` di `settings.py`.

### 12.2 Global Input Masking (`static/js/paketin-masking.js`)
- **NPWP**: Format otomatis `XX.XXX.XXX.X-XXX.XXX` pada input NPWP klien/vendor/karyawan.
- **Nomor Telepon / WhatsApp**: Sanitasi otomatis karakter non-angka dengan dukungan prefiks `+`.
- **Nomor Rekening Bank**: Sanitasi hanya mengizinkan karakter numerik murni.

---

## 13. Arsitektur Sentralisasi Template & Siklus Modul Finance

### 13.1 Sentralisasi Folder Template (`/templates/`)
Untuk menghindari duplikasi dan konflik prioritas Django Template Loader (`DIRS` vs `APP_DIRS`), seluruh file template UI dan cetak dokumen disentralisasi ke dalam direktori induk [`/templates/`](file:///c:/Users/dell/code/erp-paketin/templates/):
* **`templates/operations/`**: Seluruh antarmuka operasional, cetak resi AWB (thermal 100x100, 100x150, A4 reguler, bulky), manifest (outbound, linehaul, bag tag), scan barcode, run sheet, dan e-POD.
* **`templates/finance/`**: Invoice list, invoice detail, invoice form entry, invoice PDF, LDP batching, worksheet, dan laporan keuangan.
* **`templates/master/`**: Master customer, vendor, tarif/price import, dan coverage area.
* **`templates/crm/`**, **`templates/organizations/`**, **`templates/employees/`**, **`templates/accounts/`**, **`templates/attendance/`**, **`templates/leave/`**, **`templates/audit/`**: Modul fungsional pendukung.

### 13.2 Siklus Hidup & Filter Status Invoice (Finance Lifecycle)
1. **Pemisahan Invoice Aktif vs Invoice Selesai**:
   - Menu **Invoice & Billing** ([`/finance/invoices/`](file:///c:/Users/dell/code/erp-paketin/apps/finance/views.py#L29-L75)) hanya memuat dan menghitung invoice yang masih berjalan (`DRAFT`, `SENT`, `PARTIAL`).
   - Invoice yang telah berstatus **`PAID` (Lunas)** secara otomatis disaring keluar dari list aktif dan dialihkan ke arsip terpusat pada menu **Invoice Process $\rightarrow$ Riwayat Selesai** ([`/finance/invoice-process/?tab=completed`](file:///c:/Users/dell/code/erp-paketin/apps/finance/views.py#L240-L280)).
2. **Kalkulasi Biaya, Pajak & Materai**:
   - **Subtotal**: `Biaya Kirim - Diskon + Biaya Tambahan (Surcharge/Handling) + Biaya Kemasan + Biaya Lain`.
   - **PPN**: 1.1% dari Subtotal.
   - **Bea Materai**: Rp 10.000 otomatis jika `(Subtotal + PPN) > Rp 5.000.000` (atau Rp 0 jika $\le$ Rp 5.000.000).
   - **Grand Total**: `Subtotal + PPN + Materai + Premi Asuransi`.
   - **Worksheet Auto-Sync**: Setiap kali invoice dibuat atau disetujui, rincian per-resi otomatis disinkronkan ke sheet database utama `KPI Finance 2026`.


