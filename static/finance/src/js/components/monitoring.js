/**
 * MONITORING MANAGER v3.2 (Supervisor Panel)
 * Panel monitoring khusus Admin/Supervisor dengan 3 sub-menu:
 * - Dashboard: Stats cards + AI Executive Summary
 * - Kinerja PIC: Leaderboard produktivitas Akurat berdasarkan Akun Staff Kantor
 * - Deteksi Anomali: Daftar pengiriman merugi (profit < 0)
 *
 * CHANGELOG v3.2:
 * [FIX #1] Hanya role 'pic' yang tampil di leaderboard — admin tidak masuk.
 * [FIX #2] Daftar PIC diambil dinamis dari DB (tabel profiles), bukan hardcoded.
 * [FIX #3] Matching PIC via email (created_by) UTAMA, fallback ke nama display
 *          (updated_by). Data tak dikenal masuk 'Tidak Diketahui', tidak mencemari PIC lain.
 * [FIX #4] Revenue & Profit dibaca langsung dari nilai tersimpan di DB (parseFloat
 *          murni) — TANPA kalkulasi ulang. Nilai 0 = memang belum diisi, bukan bug.
 * [FIX #5] Filter data: buang baris kosong dan config internal saja, tidak filter
 *          berdasarkan sheet_id agar semua sheet dalam file tahunan ikut terhitung.
 * [FIX #6] Label card "Total Entri" (bukan "Hari Ini").
 */
class MonitoringManager {
    constructor() {
        this.initialized = false;
        this.yearlyData = [];
        this.activeTab = 'dashboard';
        this.retryCount = 0;
        this.picProfiles = []; // [{ email, name }] — hanya role 'pic'
    }

    // ─── Helpers ────────────────────────────────────────────────────────────────

    _fmt(val) {
        return window.Formatter
            ? window.Formatter.currency(val)
            : 'Rp ' + new Intl.NumberFormat('id-ID').format(val || 0);
    }

    _parseFloat(val) {
        if (val === null || val === undefined || val === '' || val === '—' || val === '-') return 0;
        if (typeof val === 'number') return isNaN(val) ? 0 : val;
        return window.Formatter
            ? window.Formatter.parseLocaleFloat(val)
            : (parseFloat(String(val).replace(/[^\d.-]/g, '')) || 0);
    }

    _formatDate(dateStr) {
        if (!dateStr || dateStr === 'null') return '—';
        const match = dateStr.match(/^(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
        if (match) {
            const [_, y, m, d] = match;
            return `${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`;
        }
        return dateStr;
    }

    /**
     * Tentukan nama PIC canonical dari sebuah row.
     * Prioritas 1 : email exact match  (created_by  → email PIC di DB)
     * Prioritas 2 : nama exact match   (updated_by  → name PIC di DB, case-insensitive)
     * Prioritas 3 : nama partial match (substring dua arah)
     * Gagal semua → return null  (masuk bucket 'Tidak Diketahui')
     */
    _resolvePicName(row, emailToName, nameLowerToName) {
        const createdBy = String(row.created_by || '').trim().toLowerCase();
        const updatedBy = String(row.updated_by || '').trim();

        // Prioritas 1: email exact
        if (createdBy && emailToName[createdBy]) return emailToName[createdBy];

        // Prioritas 2 & 3: nama display
        if (updatedBy) {
            const lower = updatedBy.toLowerCase();
            if (nameLowerToName[lower]) return nameLowerToName[lower];
            for (const [nameLower, canonical] of Object.entries(nameLowerToName)) {
                if (lower.includes(nameLower) || nameLower.includes(lower)) return canonical;
            }
        }

        return null;
    }

    // ─── Init & Data ────────────────────────────────────────────────────────────

    async init() {
        if (typeof authManager !== 'undefined' && !authManager.isAdmin()) return;

        console.log('[MonitoringManager] Init, loading data...');
        await this._loadPicProfiles();
        await this._loadData();

        if (this.yearlyData.length === 0 && this.retryCount < 4) {
            this.retryCount++;
            console.log(`[MonitoringManager] Data kosong, retry ${this.retryCount}/4...`);
            setTimeout(() => this.init(), 800);
            return;
        }

        this.retryCount = 0;
        this.renderStats();
        this.renderPicLeaderboard();
        this.renderAnomalyTable();
        this.switchTab(this.activeTab);
        this.initialized = true;
    }

    /**
     * [FIX] Ambil PIC dari DB — semua user yang BUKAN admin.
     * Filter explicit untuk membuang email admin aktif agar tidak masuk leaderboard.
     */
    async _loadPicProfiles() {
        this.picProfiles = [];
        
        // Ambil email admin yang sedang login untuk di-exclude
        const adminEmail = (typeof authManager !== 'undefined' && authManager.isAdmin() && authManager.currentUser?.email)
            ? authManager.currentUser.email.toLowerCase().trim()
            : null;

        try {
            if (typeof databaseManager !== 'undefined' &&
                typeof databaseManager.fetchUserConfigs === 'function') {

                const profiles = await databaseManager.fetchUserConfigs();
                this.picProfiles = (profiles || [])
                    .filter(p => p.role !== 'admin')          // ← kecualikan role admin
                    .filter(p => !adminEmail || (p.email || '').toLowerCase().trim() !== adminEmail)
                    .map(p => ({
                        email: (p.email || '').toLowerCase().trim(),
                        name: (p.name || p.email || '').trim().toUpperCase()
                    }))
                    .filter(p => p.name);                   // buang entri kosong

                console.log(`[MonitoringManager] ${this.picProfiles.length} PIC dari DB:`,
                    this.picProfiles.map(p => `${p.name} <${p.email}>`).join(' | '));
            }
        } catch (e) {
            console.warn('[MonitoringManager] Gagal load PIC dari DB:', e.message);
        }

        // Fallback ke USER_ROLES hardcoded jika DB belum bisa diakses
        if (this.picProfiles.length === 0 && typeof USER_ROLES !== 'undefined') {
            this.picProfiles = Object.entries(USER_ROLES)
                .filter(([, cfg]) => cfg.role !== 'admin')
                .filter(([email]) => !adminEmail || email.toLowerCase().trim() !== adminEmail)
                .map(([email, cfg]) => ({
                    email: email.toLowerCase().trim(),
                    name: (cfg.name || email).trim().toUpperCase()
                }));
            console.log(`[MonitoringManager] Fallback USER_ROLES: ${this.picProfiles.length} PIC`);
        }
    }

    async _loadData() {
        try {
            const fileId = window.yearlyFileManager?.activeFileId ?? null;
            let rawData = [];

            // Sumber 1: fetchYearlyData (semua sheet dalam file)
            if (fileId && typeof databaseManager !== 'undefined') {
                rawData = await databaseManager.fetchYearlyData(fileId) || [];
            }
            // Sumber 2: fetchAllDataForFile (fallback)
            if (!rawData.length && fileId &&
                typeof databaseManager?.fetchAllDataForFile === 'function') {
                rawData = await databaseManager.fetchAllDataForFile(fileId) || [];
            }
            
            // [FIX] SINKRONISASI WORKSHEET AKTIF
            // Timpa data DB dengan data memori (worksheet aktif di layar) yang berisi kalkulasi ter-update atau belum di-save
            if (typeof tableManager !== 'undefined' && tableManager.currentData && tableManager.currentData.length > 0) {
                const activeData = tableManager.currentData;
                if (rawData.length > 0) {
                    const memMap = {};
                    activeData.forEach(row => { if (row && row.id) memMap[row.id] = row; });
                    
                    // Gantikan baris dari DB dengan versi terbaru dari memori
                    rawData = rawData.map(row => (row && memMap[row.id]) ? memMap[row.id] : row);
                    
                    // Tambahkan baris baru yang mungkin belum masuk ke database
                    const dbIds = new Set(rawData.map(r => r ? r.id : null));
                    activeData.forEach(row => {
                        if (row && row.id && !dbIds.has(row.id)) {
                            rawData.push(row);
                        }
                    });
                } else {
                    rawData = [...activeData];
                }
            }

            // [FIX #5] Filter: buang baris kosong & config internal saja
            this.yearlyData = (rawData || []).filter(row => {
                if (!row || !row.id) return false;
                if (row.nama === '__SHEET_CONFIG__') return false;
                return true;
            });

            console.log(`[MonitoringManager] ${this.yearlyData.length} records dimuat.`);
        } catch (e) {
            console.error('[MonitoringManager] Load data gagal:', e);
            this.yearlyData = [];
        }
    }

    // ─── Tab ────────────────────────────────────────────────────────────────────

    switchTab(tabId) {
        this.activeTab = tabId;

        document.querySelectorAll('#page-monitoring .recap-menu-btn').forEach(btn =>
            btn.classList.remove('active'));
        document.getElementById(`monitoringMenuBtn-${tabId}`)?.classList.add('active');

        ['dashboard', 'pic', 'anomaly'].forEach(p => {
            const el = document.getElementById(`monitoringPanel-${p}`);
            if (el) el.style.display = p === tabId ? 'flex' : 'none';
        });

        const titles = {
            dashboard: {
                icon: 'fa-chart-pie', title: 'Dashboard Overview',
                sub: 'Ringkasan analitik tingkat tinggi dan monitoring kinerja operasional.'
            },
            pic: {
                icon: 'fa-users', title: 'Kinerja PIC',
                sub: 'Leaderboard produktivitas dan performa finansial per PIC Kantor.'
            },
            anomaly: {
                icon: 'fa-exclamation-triangle', title: 'Deteksi Anomali',
                sub: 'Daftar pengiriman dengan profit negatif yang perlu dievaluasi.'
            }
        };
        const t = titles[tabId] || titles.dashboard;
        const titleEl = document.getElementById('monitoringPageTitle');
        const subtitleEl = document.getElementById('monitoringPageSubtitle');
        if (titleEl) titleEl.innerHTML = `<i class="fas ${t.icon}" style="color:var(--red);margin-right:8px;"></i>${t.title}`;
        if (subtitleEl) subtitleEl.textContent = t.sub;
    }

    // ─── Render Stats Dashboard ─────────────────────────────────────────────────

    renderStats() {
        const data = this.yearlyData;

        // [FIX #6] Label "Total Entri"
        const elEntries = document.getElementById('monitorEntriesToday');
        if (elEntries) elEntries.textContent = data.length.toLocaleString('id-ID');
        const elLabel = document.getElementById('monitorEntriesTodayLabel');
        if (elLabel) elLabel.textContent = 'Total Entri';

        // [FIX #4] Baca langsung dari DB — nilai 0 = memang belum diisi
        let totalRevenue = 0, totalProfit = 0, minusCount = 0;
        data.forEach(r => {
            const rev = this._parseFloat(r.penjualan);
            const prof = this._parseFloat(r.profit);
            totalRevenue += rev;
            totalProfit += prof;
            if (prof < 0) minusCount++;
        });

        const elMinus = document.getElementById('monitorMinusCount');
        if (elMinus) elMinus.textContent = minusCount.toLocaleString('id-ID');

        const elRevenue = document.getElementById('monitorTotalRevenue');
        if (elRevenue) elRevenue.textContent = this._fmt(totalRevenue);

        const elProfit = document.getElementById('monitorTotalProfit');
        if (elProfit) {
            elProfit.textContent = this._fmt(totalProfit);
            elProfit.style.color = totalProfit >= 0 ? '#16a34a' : '#dc2626';
        }

        const elAudit = document.getElementById('monitorAuditTop');
        if (elAudit) {
            elAudit.textContent = '...';
            if (typeof databaseManager?.getAuditLogs === 'function') {
                databaseManager.getAuditLogs(500)
                    .then(logs => { elAudit.textContent = (logs?.length ?? 0).toLocaleString('id-ID'); })
                    .catch(() => { elAudit.textContent = '0'; });
            } else {
                elAudit.textContent = '0';
            }
        }
    }

    // ─── Render Leaderboard PIC ─────────────────────────────────────────────────

    renderPicLeaderboard() {
        const data = this.yearlyData;
        const tbody = document.getElementById('monitoringPicTableBody');
        if (!tbody) return;

        // Build lookup maps
        const emailToName = {};
        const nameLowerToName = {};
        this.picProfiles.forEach(p => {
            if (p.email) emailToName[p.email] = p.name;
            if (p.name) nameLowerToName[p.name.toLowerCase()] = p.name;
        });

        // Inisialisasi bucket per PIC (terdaftar)
        const picStats = {};
        this.picProfiles.forEach(p => {
            picStats[p.name] = { count: 0, revenue: 0, profit: 0, registered: true };
        });

        // Ambil nama admin yang sedang login untuk dieksklusi dari leaderboard
        const adminName = (typeof authManager !== 'undefined' && authManager.isAdmin() && authManager.currentUser?.config?.name)
            ? authManager.currentUser.config.name.toUpperCase().trim()
            : null;
        const adminEmail = (typeof authManager !== 'undefined' && authManager.isAdmin() && authManager.currentUser?.email)
            ? authManager.currentUser.email.toLowerCase().trim()
            : null;

        // Grand total akumulasi SEMUA baris (= total worksheet)
        let grandCount = 0, grandRevenue = 0, grandProfit = 0;

        data.forEach(row => {
            const rev = this._parseFloat(row.penjualan);
            const profit = this._parseFloat(row.profit);

            grandCount += 1;
            grandRevenue += rev;
            grandProfit += profit;

            let picName = this._resolvePicName(row, emailToName, nameLowerToName);
            
            // Ekstraksi dinamis jika tidak ada di profil terdaftar
            if (!picName) {
                const rawName = String(row.created_by || row.updated_by || '').trim();
                const cleanName = rawName.includes('@') ? rawName.split('@')[0] : rawName;
                if (cleanName) {
                    picName = cleanName.toUpperCase();
                }
            }

            // Abaikan jika baris ini milik admin
            if (!picName || picName === adminName || (row.created_by && row.created_by.toLowerCase() === adminEmail)) {
                return; // Tidak dimasukkan ke leaderboard PIC, tapi sudah masuk Grand Total
            }

            if (!picStats[picName]) {
                picStats[picName] = { count: 0, revenue: 0, profit: 0, registered: false };
            }

            picStats[picName].count += 1;
            picStats[picName].revenue += rev;
            picStats[picName].profit += profit;
        });

        // Sort PIC by count desc — gabungkan PIC terdaftar dan dinamis
        const sortedPics = Object.keys(picStats)
            .map(name => ({ pic: name, ...picStats[name] }))
            // Hanya tampilkan jika count > 0 ATAU mereka adalah PIC terdaftar
            .filter(s => s.count > 0 || s.registered)
            .sort((a, b) => b.count - a.count);

        // Summary cards
        const activePicCount = sortedPics.filter(s => s.count > 0).length;

        const elTotal = document.getElementById('monitorPicTotal');
        const elTop = document.getElementById('monitorPicTop');
        const elAvg = document.getElementById('monitorPicAvg');
        const elCount = document.getElementById('monitorPicCountLabel');

        if (elTotal) elTotal.textContent = activePicCount;
        if (elTop) {
            const top = sortedPics.find(s => s.count > 0);
            elTop.textContent = top ? top.pic : '—';
        }
        if (elAvg) elAvg.textContent = activePicCount > 0
            ? Math.round(data.length / activePicCount) : '0';
        if (elCount) elCount.textContent = `${activePicCount} PIC`;

        // Render rows — hanya baris PIC terdaftar
        let html = '';

        sortedPics.forEach((stat, idx) => {
            const margin = stat.revenue > 0 ? (stat.profit / stat.revenue) * 100 : 0;
            const profitColor = stat.profit >= 0 ? '#16a34a' : '#dc2626';
            const marginColor = margin >= 0 ? '#16a34a' : '#dc2626';

            html += `
                <tr>
                    <td style="text-align:center;font-weight:700;color:var(--red);">${idx + 1}</td>
                    <td style="font-weight:700;color:var(--text-primary);text-align:left;">${stat.pic}</td>
                    <td style="text-align:center;font-weight:700;color:var(--text-secondary);">${stat.count.toLocaleString('id-ID')}</td>
                    <td style="text-align:right;font-weight:600;color:var(--text-primary);">${this._fmt(stat.revenue)}</td>
                    <td style="text-align:right;font-weight:700;color:${profitColor};">${this._fmt(stat.profit)}</td>
                    <td style="text-align:right;font-weight:700;color:${marginColor};">${margin.toFixed(1)}%</td>
                </tr>`;
        });

        const grandMargin = grandRevenue > 0 ? (grandProfit / grandRevenue) * 100 : 0;
        const grandProfitColor = grandProfit >= 0 ? '#16a34a' : '#dc2626';

        html += `
            <tr style="background:rgba(204,0,0,0.05);border-top:2px solid var(--red);">
                <td colspan="2" style="text-align:right;font-weight:800;color:var(--text-primary);font-size:0.85rem;padding:14px 12px;">GRAND TOTAL:</td>
                <td style="text-align:center;font-weight:800;color:var(--text-secondary);font-size:0.85rem;padding:14px 12px;">${grandCount.toLocaleString('id-ID')}</td>
                <td style="text-align:right;font-weight:800;color:var(--text-primary);font-size:0.85rem;padding:14px 12px;">${this._fmt(grandRevenue)}</td>
                <td style="text-align:right;font-weight:900;color:${grandProfitColor};font-size:0.9rem;padding:14px 12px;">${this._fmt(grandProfit)}</td>
                <td style="text-align:right;font-weight:800;color:${grandProfitColor};font-size:0.85rem;padding:14px 12px;">${grandMargin.toFixed(1)}%</td>
            </tr>`;

        tbody.innerHTML = html;
    }

    // ─── Render Anomali ─────────────────────────────────────────────────────────

    renderAnomalyTable() {
        const data = this.yearlyData;
        const tbody = document.getElementById('monitoringAnomalyTableBody');
        if (!tbody) return;

        // [FIX #4] Gunakan nilai DB langsung
        const anomalies = data
            .filter(r => this._parseFloat(r.profit) < 0)
            .sort((a, b) => this._parseFloat(a.profit) - this._parseFloat(b.profit));

        let html = '';
        anomalies.forEach((row, idx) => {
            const rev = this._parseFloat(row.penjualan);
            const cost = this._parseFloat(row.total_biaya);
            const profit = this._parseFloat(row.profit);
            html += `
                <tr>
                    <td style="text-align:center;font-weight:700;color:var(--red);">${idx + 1}</td>
                    <td style="text-align:center;color:var(--text-secondary);">${this._formatDate(row.tanggal_pickup)}</td>
                    <td style="font-weight:700;color:var(--text-primary);text-align:left;">${row.nama || '—'}</td>
                    <td style="font-weight:600;color:var(--text-secondary);text-align:left;">${row.pengirim || '—'}</td>
                    <td style="text-align:right;font-weight:600;color:var(--text-primary);">${this._fmt(rev)}</td>
                    <td style="text-align:right;font-weight:600;color:#ea580c;">${this._fmt(cost)}</td>
                    <td style="text-align:right;font-weight:700;color:#dc2626;">${this._fmt(profit)}</td>
                </tr>`;
        });

        if (!html) {
            html = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-secondary);opacity:0.7;">
                <i class="fas fa-check-circle" style="color:#16a34a;margin-right:8px;"></i>
                Tidak ada pengiriman dengan profit negatif.
            </td></tr>`;
        }

        tbody.innerHTML = html;
    }

    // ─── AI Summary ─────────────────────────────────────────────────────────────

    generateAiSummary() {
        const btn = event.currentTarget;
        const resultEl = document.getElementById('monitoringAiSummary');
        if (!btn || !resultEl) return;

        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        btn.disabled = true;

        if (!this.yearlyData.length) {
            resultEl.innerHTML = 'Maaf, belum ada data transaksi yang valid untuk dianalisis.';
            this._resetBtn(btn);
            return;
        }

        if (window.chatManager?.queryGeminiAPI) {
            window.chatManager.queryGeminiAPI(
                'Sebagai Virtual CFO, berikan ringkasan eksekutif mengenai performa finansial.',
                JSON.stringify(this.yearlyData)
            )
                .then(res => {
                    resultEl.innerHTML = res
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n/g, '<br>');
                    this._resetBtn(btn);
                })
                .catch(err => {
                    resultEl.innerHTML = `<span style="color:#dc2626;">Gagal: ${err.message}</span>`;
                    this._resetBtn(btn);
                });
        } else {
            this._resetBtn(btn);
        }
    }

    _resetBtn(btn) {
        btn.innerHTML = '<i class="fas fa-bolt"></i> Generate';
        btn.disabled = false;
    }
}

// ─── Instance & Listeners ───────────────────────────────────────────────────────

window.monitoringManager = new MonitoringManager();

document.addEventListener('DOMContentLoaded', () => {
    window.monitoringManager?.init();
});
window.addEventListener('yearlyFileActivated', () => {
    window.monitoringManager?.init();
});
window.addEventListener('worksheetDataLoaded', () => {
    window.monitoringManager?.init();
});