# Rekonstruksi Workflow Modul Pick Up Operational

> **Status:** ✅ *Completed (Diimplementasikan pada 27 Agustus 2026)*  
> **Versi:** 1.4.0-alpha
## Konsep Dasar
Pemilahan yang jelas antara **Permintaan Pick Up (Request)** dan **Dokumen Penugasan (Manifest)**. Desain ini bertujuan untuk mempercepat proses alokasi armada oleh tim Customer Service (CS) dan tetap mengakomodasi input mandiri dari sisi Customer.

## 1. Struktur Tab (Sub-Table) pada Menu Pick Up

Menu Pick Up akan diringkas menjadi **3 Tab Utama** yang lebih *action-oriented*:

### Tab 1: Menunggu Penugasan (Pending Requests)
- **Fungsi**: Menampung **SEMUA** permintaan Pick Up yang masuk dan belum di-assign ke supir.
- **Karakteristik**:
  - Terdapat kolom **Sumber (Source)** berbentuk *badge* (misal: `CS Internal` vs `Customer App`) untuk membedakan asal order.
  - Berisi list data order per baris.
- **Fitur Action**: 
  - Tersedia **Checkbox 1-by-1 atau Checkbox Full (Select All)** di setiap baris.
  - CS dapat mencentang beberapa orderan sekaligus (bulk) lalu klik tombol **"Assign to Driver"** di atas tabel.
  - Setelah diklik, CS akan diarahkan ke form pop-up/halaman untuk memilih **Armada dan Driver**.

### Tab 2: Pick Up Manifest (Sedang Berjalan)
- **Fungsi**: Berisi dokumen penugasan (*Runsheet*) resmi untuk supir.
- **Karakteristik**:
  - Satu dokumen Manifest bisa berisi gabungan beberapa order Pick Up hasil seleksi checkbox di Tab 1.
- **Fitur Action**:
  - Cetak (Print) dokumen Surat Jalan/Manifest.
  - Update status *tracking* armada (misal: Menuju Lokasi, Sedang Pick Up).

### Tab 3: Riwayat (Completed / Failed)
- **Fungsi**: Menyimpan data order yang statusnya sudah Selesai (barang sukses diambil dan tiba di gudang) atau Batal (Customer cancel, toko tutup, dsb).
- **Tujuan**: Memastikan Tab 1 dan Tab 2 tetap bersih dan hanya menampilkan tugas yang masih *active/pending*.

---

## 2. Standarisasi Tombol "Buat Baru" (Create Request)

- **Satu Form Universal**: Tidak perlu memisahkan tombol "Pick Up Order" dan "Pick Up By Customer". Cukup gunakan satu tombol **"Buat Pick Up"**.
- **Logika Sistem (Role Based)**:
  - **Jika yang login CS Internal**: Form akan menampilkan dropdown pencarian `Customer`. CS menginput data *atas nama* customer.
  - **Jika yang login Customer**: Field `Customer` disembunyikan/di-*disable* dan otomatis terisi atas nama akun customer yang login.

---

## 3. Alur / User Journey (End-to-End)

1. **Input Permintaan**: Order masuk via CS (lewat sistem operasional) atau via Customer (lewat portal customer).
2. **Antrean**: Order tersebut otomatis masuk ke antrean di **Tab 1: Menunggu Penugasan**.
3. **Assignment (Routing)**: 
   - Tim Operasional (CS / Dispatcher) mengecek Tab 1.
   - Mereka melihat pesanan mana yang searah/satu rute.
   - Mencentang pesanan-pesanan tersebut, lalu menekan **"Assign to Driver"** dan memilih Supir X.
4. **Manifest Creation**: Sistem memindahkan pesanan tersebut dari Tab 1, lalu membuat 1 dokumen penugasan baru di **Tab 2: Pick Up Manifest** atas nama Supir X.
5. **Execution**: Supir X membawa dokumen manifest, mengambil barang di lokasi.
6. **Completion**: Setelah barang sampai di gudang asal dan tervalidasi, status berubah menjadi Success, lalu data diarsipkan ke **Tab 3: Riwayat**.
