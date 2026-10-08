// js/config.js

const SUPABASE_CONFIG = {
    url: 'https://fjprqmgzouizqbopmvia.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqcHJxbWd6b3VpenFib3BtdmlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1MzMzMjEsImV4cCI6MjA5MzEwOTMyMX0.P217IMPJZ6t_PKkcKuvwNsuwtZw-wbCatZ5Ka3_emPk'
};

const AI_CONFIG = {
    // Masukkan API Key Gemini Anda di sini agar terkonfigurasi secara global untuk seluruh website.
    // Jika dikosongkan, AI tidak akan bisa memproses data.
    GEMINI_API_KEY: ''
};


// Tab-isolated storage: setiap tab punya session sendiri
if (!window.name || !window.name.startsWith('pcf_tab_')) {
    window.name = 'pcf_tab_' + Math.random().toString(36).substr(2, 12);
}
const TAB_ID = window.name;

const tabStorage = {
    getItem: (key) => { try { return sessionStorage.getItem(TAB_ID + '::' + key); } catch (e) { return null; } },
    setItem: (key, value) => { try { sessionStorage.setItem(TAB_ID + '::' + key, value); } catch (e) { } },
    removeItem: (key) => { try { sessionStorage.removeItem(TAB_ID + '::' + key); } catch (e) { } }
};

const USER_ROLES = {
    'dhafinshabir610@gmail.com': {
        name: 'Dhafin Shabir Alfatih',
        picId: 0,
        role: 'admin',
        canEditAll: true,
        allowedColumns: null
    }
    /* 
    TEMPLATE PENAMBAHAN PIC:
    
    'email_user@gmail.com': {
        name: 'Nama Lengkap PIC',
        picId: 3,
        role: 'pic',
        canEditAll: false,
        allowedColumns: []
    },
    */
};

const EDITABLE_COLUMNS = [
    { field: 'tanggal_pickup', label: 'Tanggal Pickup', category: 'Info Pengiriman' },
    { field: 'nama', label: 'IP Perusahaan', category: 'Info Pengiriman' },
    { field: 'awb', label: 'AWB', category: 'Info Pengiriman' },
    { field: 'awb_sistem', label: 'AWB Sistem', category: 'Info Pengiriman' },
    { field: 'pengirim', label: 'Customer', category: 'Info Pengiriman' },
    { field: 'sales', label: 'Sales', category: 'Info Pengiriman' },
    { field: 'penerima', label: 'Penerima', category: 'Info Pengiriman' },
    { field: 'service', label: 'Service', category: 'Detail Barang' },
    { field: 'via', label: 'Via', category: 'Detail Barang' },
    { field: 'aktual', label: 'Aktual', category: 'Detail Barang' },
    { field: 'vol', label: 'Vol', category: 'Detail Barang' },
    { field: 'unit', label: 'Unit', category: 'Detail Barang' },
    { field: 'kubik', label: 'Kubik', category: 'Detail Barang' },
    { field: 'p', label: 'P (Panjang)', category: 'Detail Barang' },
    { field: 'l', label: 'L (Lebar)', category: 'Detail Barang' },
    { field: 't', label: 'T (Tinggi)', category: 'Detail Barang' },
    { field: 'koil', label: 'Koil', category: 'Detail Barang' },
    { field: 'harga', label: 'Harga', category: 'Keuangan' },
    { field: 'surcharge', label: 'Surcharge', category: 'Keuangan' },
    { field: 'packing', label: 'Packing', category: 'Keuangan' },
    { field: 'handling', label: 'Handling', category: 'Keuangan' },
    { field: 'asal_pickup', label: 'Asal Pick Up', category: 'Detail Barang' },
    { field: 'jenis_barang', label: 'Jenis Barang', category: 'Detail Barang' },
    { field: 'tujuan', label: 'Tujuan', category: 'Detail Barang' },
    { field: 'penjualan', label: 'Penjualan', category: 'Keuangan' },
    { field: 'nilai_barang', label: 'Nilai Barang', category: 'Keuangan' },
    { field: 'nama_vendor', label: 'Nama Vendor I', category: 'Keuangan' },
    { field: 'nama_vendor_ii', label: 'Nama Vendor II', category: 'Keuangan' },
    { field: 'nama_vendor_iii', label: 'Nama Vendor III', category: 'Keuangan' },
    { field: 'nama_vendor_iv', label: 'Nama Vendor IV', category: 'Keuangan' },
    { field: 'vendor_i', label: 'Harga Vendor I', category: 'Keuangan' },
    { field: 'vendor_ii', label: 'Harga Vendor II', category: 'Keuangan' },
    { field: 'vendor_iii', label: 'Harga Vendor III', category: 'Keuangan' },
    { field: 'vendor_iv', label: 'Harga Vendor IV', category: 'Keuangan' },
    { field: 'ops', label: 'OPS', category: 'Keuangan' },
    { field: 'total_biaya', label: 'Total Biaya', category: 'Keuangan' },
    { field: 'profit', label: 'Profit', category: 'Keuangan' },
    { field: 'idx_profit', label: 'IDX Profit', category: 'Keuangan' },
    { field: 'asuransi', label: 'Asuransi', category: 'Keuangan' },
    { field: 'asuransi_jasindo', label: 'Asuransi Jasindo', category: 'Keuangan' }
];

const COLUMN_CATEGORIES = [
    { key: 'Info Pengiriman', label: 'Info Pengiriman', icon: 'fa-info-circle' },
    { key: 'Detail Barang', label: 'Detail Barang', icon: 'fa-box' },
    { key: 'Keuangan', label: 'Keuangan', icon: 'fa-coins' }
];

const REALTIME_CHANNEL = 'kpi-updates';