/**
 * AI CHAT MANAGER v3.0 — Hybrid Visual + Database Context
 * 
 * Strategi: AI menerima data dari 2 sumber:
 * 1. Visual Context — Data yang sudah ter-render di website (KPI cards, recap tables, charts)
 * 2. Database Context — Data mentah dari database dengan SEMUA kolom
 * 
 * Ini memastikan AI bisa menjawab pertanyaan tentang "total pengiriman", "POD per customer",
 * dan data lainnya yang dihitung secara visual tapi tidak ada di kolom database.
 */
class AIChatManager {
    constructor() {
        this.isOpen = false;
        this.isExpanded = false;
        this.conversationHistory = []; // Store conversation for multi-turn context

        this.widget = document.getElementById('aiChatWidget');
        this.fab = document.getElementById('aiChatFab');
        this.messagesContainer = document.getElementById('aiChatMessages');
        this.input = document.getElementById('aiChatInput');
        this.sendBtn = document.getElementById('aiChatSendBtn');
        this.expandBtn = document.getElementById('aiChatExpandBtn');
        this.closeBtn = document.getElementById('aiChatCloseBtn');
        this.header = document.querySelector('.ai-chat-header');
        this.contextIndicator = document.getElementById('aiContextIndicator');

        // Check if AI is enabled (admin toggle)
        this._checkAIEnabled();

        this.initEventListeners();
        this.initDraggable();
        this.updateContext();

        // Listen for tab changes to update context
        window.addEventListener('hashchange', () => this.updateContext());

        // Hide on login page
        this._checkLoginVisibility();
        const observer = new MutationObserver(() => this._checkLoginVisibility());
        const loginSection = document.getElementById('loginSection');
        if (loginSection) observer.observe(loginSection, { attributes: true, attributeFilter: ['style'] });
        const dashboardContainer = document.getElementById('dashboardContainer');
        if (dashboardContainer) observer.observe(dashboardContainer, { attributes: true, attributeFilter: ['style'] });
    }

    _checkLoginVisibility() {
        // Jika AI dimatikan dari panel admin, sembunyikan secara permanen
        if (this._aiDisabled) {
            if (this.fab) this.fab.style.display = 'none';
            if (this.widget) {
                this.widget.classList.add('collapsed');
                this.widget.style.display = 'none';
                this.isOpen = false;
            }
            return;
        }

        const dashboard = document.getElementById('dashboardContainer');
        const isLoggedIn = dashboard && dashboard.style.display !== 'none';

        if (this.fab) this.fab.style.display = isLoggedIn ? '' : 'none';
        if (this.widget) {
            if (!isLoggedIn) {
                this.widget.classList.add('collapsed');
                this.widget.style.display = 'none';
                this.isOpen = false;
            } else {
                this.widget.style.display = '';
            }
        }
    }

    /**
     * Admin toggle: Check if AI feature is enabled
     */
    _checkAIEnabled() {
        const isEnabled = localStorage.getItem('ai_assistant_enabled');
        // Default: enabled (null means not set yet = enabled)
        if (isEnabled === 'false') {
            if (this.fab) this.fab.style.display = 'none';
            if (this.widget) this.widget.style.display = 'none';
            this._aiDisabled = true;
        } else {
            this._aiDisabled = false;
        }
    }

    /**
     * Toggle AI on/off from admin panel
     */
    static toggleAIFeature(enabled) {
        localStorage.setItem('ai_assistant_enabled', enabled ? 'true' : 'false');
        if (window.aiChatManager) {
            window.aiChatManager._aiDisabled = !enabled;
            window.aiChatManager._checkLoginVisibility();
        }
    }

    // ======================================================================
    //  VISUAL CONTEXT COLLECTORS — Scrape data dari DOM/managers
    // ======================================================================

    /**
     * Collect KPI summary from Dashboard stat cards
     * (Total Revenue, Total Profit, Total Pengiriman)
     */
    _collectDashboardSummary() {
        const summary = {};

        // From stat cards
        const revEl = document.getElementById('totalRevenue');
        const profEl = document.getElementById('totalProfit');
        const shipEl = document.getElementById('totalShipments');

        if (revEl) summary.totalRevenue = revEl.textContent.trim();
        if (profEl) summary.totalProfit = profEl.textContent.trim();
        if (shipEl) summary.totalPengiriman = shipEl.textContent.trim();

        // Year context
        const displayYear = document.getElementById('displayYear');
        if (displayYear) summary.tahun = displayYear.textContent.trim();

        // Monthly detail if open
        const monthlyRevEl = document.getElementById('monthlyRevenue');
        const monthlyProfEl = document.getElementById('monthlyProfit');
        const monthlyCostEl = document.getElementById('monthlyCost');
        const monthlyMarginEl = document.getElementById('monthlyMargin');
        const monthlyShipEl = document.getElementById('monthlyShipments');

        if (monthlyRevEl && monthlyRevEl.textContent !== 'Rp 0') {
            summary.bulanDetail = {
                revenue: monthlyRevEl.textContent.trim(),
                profit: monthlyProfEl ? monthlyProfEl.textContent.trim() : null,
                totalBiaya: monthlyCostEl ? monthlyCostEl.textContent.trim() : null,
                margin: monthlyMarginEl ? monthlyMarginEl.textContent.trim() : null,
                pengiriman: monthlyShipEl ? monthlyShipEl.textContent.trim() : null
            };
        }

        return Object.keys(summary).length > 0 ? summary : null;
    }

    /**
     * Collect monthly breakdown from chart data
     */
    _collectMonthlyBreakdown() {
        if (!window.chartsManager || !window.chartsManager.cachedYearlyData) return null;

        const data = window.chartsManager.cachedYearlyData;
        const year = window.chartsManager.selectedYear;
        const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];

        const breakdown = [];
        for (let i = 1; i <= 12; i++) {
            const mSummary = window.formulaEngine.compute('monthly_summary', data, {
                year: year, month: i
            });
            if (mSummary.count > 0) {
                breakdown.push({
                    bulan: months[i - 1],
                    revenue: Math.round(mSummary.totalRevenue),
                    profit: Math.round(mSummary.totalProfit),
                    biaya: Math.round(mSummary.totalCost),
                    jumlahPengiriman: mSummary.count,
                    margin: mSummary.totalRevenue > 0 ?
                        (mSummary.totalProfit / mSummary.totalRevenue * 100).toFixed(1) + '%' : '0%'
                });
            }
        }
        return breakdown.length > 0 ? breakdown : null;
    }

    _collectCustomerSummary() {
        let rawData = null;
        if (typeof databaseManager !== 'undefined' && window.chartsManager && window.chartsManager.cachedYearlyData && window.chartsManager.cachedYearlyData.length > 0) {
            rawData = window.chartsManager.cachedYearlyData;
        } else if (window.recapPageManager && window.recapPageManager.filteredData && window.recapPageManager.filteredData.length > 0) {
            rawData = window.recapPageManager.filteredData;
        } else if (window.tableManager && window.tableManager.currentData) {
            rawData = window.tableManager.currentData;
        }

        if (rawData && rawData.length > 0) {
            const agg = {};
            rawData.forEach(row => {
                if (!row || row.nama === '__SHEET_CONFIG__') return;
                let customer = (row.pengirim || '').trim();
                if (!customer || customer === '-' || customer === '—') {
                    customer = '(Transaksi Tanpa Nama Customer)';
                }
                if (!agg[customer]) {
                    agg[customer] = { nama: customer, pods: 0, revenue: 0, profit: 0, perusahaan: new Set() };
                }
                agg[customer].pods++;
                const rev = window.Formatter ? window.Formatter.parseLocaleFloat(row.penjualan) : (parseFloat(row.penjualan) || 0);
                const profit = window.Formatter ? window.Formatter.parseLocaleFloat(row.profit) : (parseFloat(row.profit) || 0);
                agg[customer].revenue += rev;
                agg[customer].profit += profit;
                if (row.nama) agg[customer].perusahaan.add(row.nama);
            });

            const sorted = Object.values(agg)
                .map(c => ({
                    nama: c.nama,
                    totalPOD: c.pods,
                    totalRevenue: Math.round(c.revenue),
                    totalProfit: Math.round(c.profit),
                    perusahaan: [...c.perusahaan].join(', ')
                }))
                .sort((a, b) => b.totalRevenue - a.totalRevenue)
                .slice(0, 30); // Top 30 customers

            return sorted.length > 0 ? sorted : null;
        }

        // Source 2: From dashboard recent table DOM
        const recentBody = document.getElementById('recentTableBody');
        if (recentBody && recentBody.rows.length > 0) {
            const customers = [];
            for (const row of recentBody.rows) {
                if (row.cells.length >= 5) {
                    customers.push({
                        nama: row.cells[2]?.textContent?.trim(),
                        perusahaan: row.cells[1]?.textContent?.trim(),
                        omset: row.cells[3]?.textContent?.trim(),
                        totalPOD: row.cells[4]?.textContent?.trim(),
                        totalRevenue: row.cells[5]?.textContent?.trim(),
                        totalProfit: row.cells[6]?.textContent?.trim()
                    });
                }
            }
            return customers.length > 0 ? customers : null;
        }

        return null;
    }

    /**
     * Collect Sales Performance Aggregation (POD, Revenue, Unique Customers per Month)
     */
    _collectSalesSummary() {
        let rawData = null;

        // Selalu prioritaskan data tahunan penuh agar AI fleksibel menjawab bulan apa saja
        if (typeof databaseManager !== 'undefined' && window.chartsManager && window.chartsManager.cachedYearlyData && window.chartsManager.cachedYearlyData.length > 0) {
            rawData = window.chartsManager.cachedYearlyData;
        } else if (window.tableManager && window.tableManager.currentData) {
            rawData = window.tableManager.currentData;
        }


        if (!rawData || rawData.length === 0) return null;

        const salesAgg = {};
        const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"];

        rawData.forEach(row => {
            if (!row || !row.sales || row.nama === '__SHEET_CONFIG__') return;
            const s = row.sales.trim();
            if (!s) return;

            // Get Month
            let mStr = "Lainnya";
            if (row.tanggal_pickup) {
                try {
                    const d = window.formulaEngine ? window.formulaEngine._parseDate(row.tanggal_pickup) : new Date(row.tanggal_pickup);
                    if (d && !isNaN(d.getTime())) {
                        mStr = monthNames[d.getMonth()];
                    }
                } catch (e) { }
            }

            const key = s + '_' + mStr;
            if (!salesAgg[key]) {
                salesAgg[key] = { sales: s, bulan: mStr, pods: 0, revenue: 0, profit: 0, customers: new Set() };
            }
            salesAgg[key].pods++;

            const getVal = (v) => window.Formatter ? window.Formatter.parseLocaleFloat(v) : (parseFloat(v) || 0);
            salesAgg[key].revenue += getVal(row.penjualan);
            salesAgg[key].profit += getVal(row.profit);
            if (row.pengirim) salesAgg[key].customers.add(row.pengirim.trim());
        });

        const results = Object.values(salesAgg).map(x => ({
            sales: x.sales,
            bulan: x.bulan,
            totalPOD: x.pods,
            totalRevenue: Math.round(x.revenue),
            totalProfit: Math.round(x.profit),
            jumlahCustomerUnik: x.customers.size
        })).sort((a, b) => b.totalRevenue - a.totalRevenue);

        return results.length > 0 ? results : null;
    }

    _collectVendorSummary() {
        let rawData = null;
        if (typeof databaseManager !== 'undefined' && window.chartsManager && window.chartsManager.cachedYearlyData && window.chartsManager.cachedYearlyData.length > 0) {
            rawData = window.chartsManager.cachedYearlyData;
        } else if (window.tableManager && window.tableManager.currentData) {
            rawData = window.tableManager.currentData;
        }

        if (!rawData || rawData.length === 0) return null;

        const vendorAgg = {};
        const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"];

        rawData.forEach(row => {
            if (!row || !row.nama || row.nama === '__SHEET_CONFIG__') return;
            const v = row.nama.trim();

            let mStr = "Lainnya";
            if (row.tanggal_pickup) {
                try {
                    const d = window.formulaEngine ? window.formulaEngine._parseDate(row.tanggal_pickup) : new Date(row.tanggal_pickup);
                    if (d && !isNaN(d.getTime())) {
                        mStr = monthNames[d.getMonth()];
                    }
                } catch (e) { }
            }

            const key = v + '_' + mStr;
            if (!vendorAgg[key]) {
                vendorAgg[key] = { vendor: v, bulan: mStr, pods: 0, revenue: 0, profit: 0, cost: 0 };
            }
            vendorAgg[key].pods++;

            const getVal = (val) => window.Formatter ? window.Formatter.parseLocaleFloat(val) : (parseFloat(val) || 0);
            vendorAgg[key].revenue += getVal(row.penjualan);
            vendorAgg[key].profit += getVal(row.profit);
            vendorAgg[key].cost += getVal(row.total_biaya);
        });

        const results = Object.values(vendorAgg).map(x => ({
            vendor: x.vendor,
            bulan: x.bulan,
            totalPengiriman: x.pods,
            totalRevenue: Math.round(x.revenue),
            totalProfit: Math.round(x.profit)
        })).sort((a, b) => b.totalRevenue - a.totalRevenue);

        return results.length > 0 ? results : null;
    }

    /**
     * Collect enriched raw data with ALL columns (not just 7)
     */
    _collectEnrichedRawData() {
        let rawData = null;

        // Source 1: Selalu prioritaskan data tahunan penuh (Global Awareness)
        if (typeof databaseManager !== 'undefined' && window.yearlyFileManager && window.yearlyFileManager.activeFileId) {
            if (window.chartsManager && window.chartsManager.cachedYearlyData && window.chartsManager.cachedYearlyData.length > 0) {
                rawData = window.chartsManager.cachedYearlyData;
            }
        }

        // Source 2: Fallback to tableManager current data (worksheet)
        if (!rawData || rawData.length === 0) {
            if (window.tableManager && window.tableManager.currentData) {
                rawData = window.tableManager.currentData;
            }
        }

        if (!rawData || rawData.length === 0) return null;

        // Filter empty rows
        const validRows = rawData.filter(row => row && row.id &&
            (row.nama || row.tanggal_pickup || row.pengirim) &&
            row.nama !== '__SHEET_CONFIG__');

        const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"];

        // Send up to 3000 rows with ALL important columns
        return validRows.slice(0, 3000).map(row => {
            const getVal = (v) => window.formulaEngine ? window.formulaEngine._getCellValueByA1_Logic(v) : (parseFloat(v) || 0);

            // Format date
            let dateStr = row.tanggal_pickup;
            if (dateStr) {
                try {
                    const d = window.formulaEngine ? window.formulaEngine._parseDate(dateStr) : new Date(dateStr);
                    if (d && !isNaN(d.getTime())) {
                        dateStr = `${d.getDate()} ${monthNames[d.getMonth()]} ${d.getFullYear()}`;
                    }
                } catch (e) { }
            }

            return {
                tgl: dateStr,
                perusahaan: row.nama,
                awb: row.awb || row.awb_sistem || '',
                customer: row.pengirim,
                sales: row.sales,
                penerima: row.penerima,
                service: row.service,
                via: row.via,
                aktual_kg: getVal(row.aktual),
                vol_kg: getVal(row.vol),
                harga_perkilo: getVal(row.harga),
                surcharge: getVal(row.surcharge),
                packing: getVal(row.packing),
                handling: getVal(row.handling),
                revenue: getVal(row.penjualan),
                total_biaya: getVal(row.total_biaya),
                profit: getVal(row.profit),
                asal: row.asal_pickup,
                tujuan: row.tujuan,
                jenis_barang: row.jenis_barang,
                vendor: row.nama_vendor,
                asuransi: getVal(row.asuransi),
                nilai_barang: getVal(row.nilai_barang),
            };
        });
    }

    /**
     * Collect recap panel visual summary (already filtered/rendered data)
     */
    _collectRecapSummary() {
        if (!window.recapPageManager) return null;

        const recap = {};
        const filteredData = window.recapPageManager.filteredData || [];

        if (filteredData.length === 0) return null;

        const getVal = (v) => window.Formatter ? window.Formatter.parseLocaleFloat(v) : (parseFloat(v) || 0);

        // Total stats
        let totalRevenue = 0, totalCost = 0, totalProfit = 0;
        const customerSet = new Set();
        const salesSet = new Set();
        const serviceSet = new Set();
        const perusahaanSet = new Set();

        filteredData.forEach(row => {
            totalRevenue += getVal(row.penjualan);
            totalCost += getVal(row.total_biaya);
            totalProfit += getVal(row.profit);
            if (row.pengirim) customerSet.add(row.pengirim);
            if (row.sales) salesSet.add(row.sales);
            if (row.service) serviceSet.add(row.service);
            if (row.nama) perusahaanSet.add(row.nama);
        });

        recap.totalTransaksi = filteredData.length;
        recap.totalPengiriman = filteredData.length; // Each row = 1 pengiriman/POD
        recap.totalRevenue = Math.round(totalRevenue);
        recap.totalBiaya = Math.round(totalCost);
        recap.totalProfit = Math.round(totalProfit);
        recap.marginRataRata = totalRevenue > 0 ? (totalProfit / totalRevenue * 100).toFixed(1) + '%' : '0%';
        recap.jumlahCustomer = customerSet.size;
        recap.jumlahSales = salesSet.size;
        recap.daftarService = [...serviceSet].join(', ');
        recap.daftarPerusahaan = [...perusahaanSet].join(', ');

        // Active filters
        const yearSelect = document.getElementById('recapFilterYear');
        const monthSelect = document.getElementById('recapFilterMonth');
        if (yearSelect) recap.filterTahun = yearSelect.value;
        if (monthSelect) {
            const monthNames = ['Semua Bulan', 'Januari', 'Februari', 'Maret', 'April', 'Mei',
                'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
            recap.filterBulan = monthNames[parseInt(monthSelect.value)] || 'Semua Bulan';
        }

        return recap;
    }

    /**
     * MASTER: Build complete AI context from all sources
     */
    _buildAIContext() {
        const context = {
            dashboardSummary: this._collectDashboardSummary(),
            monthlyBreakdown: this._collectMonthlyBreakdown(),
            customerSummary: this._collectCustomerSummary(),
            salesSummary: this._collectSalesSummary(),
            vendorSummary: this._collectVendorSummary(),
            recapSummary: null // Always global now
        };

        // Enriched raw data (large, so we handle separately for token optimization)
        const rawData = this._collectEnrichedRawData();

        // Determine active panel for context awareness
        const activePage = document.querySelector('.page-content[style*="display: block"], .page-content:not([style*="display: none"]):not([style*="display:none"])');
        if (activePage) {
            context.activePanel = activePage.id?.replace('page-', '') || 'unknown';
        }

        return { context, rawData };
    }

    // ======================================================================
    //  UI METHODS
    // ======================================================================

    initDraggable() {
        // --- 1. Dragging untuk FAB (Icon AI) - Snap to Edge ---
        if (this.fab) {
            let isDragging = false;
            let startX, startY, initialLeft, initialTop;

            const onFabDown = (e) => {
                if (e.target.closest('button')) return;
                isDragging = false;

                const rect = this.fab.getBoundingClientRect();
                initialLeft = rect.left;
                initialTop = rect.top;

                startX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
                startY = e.type.includes('mouse') ? e.clientY : e.touches[0].clientY;

                this.fab.style.transition = 'none';

                document.addEventListener('mousemove', onFabMove);
                document.addEventListener('mouseup', onFabUp);
                document.addEventListener('touchmove', onFabMove, { passive: false });
                document.addEventListener('touchend', onFabUp);
            };

            const onFabMove = (e) => {
                const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
                const clientY = e.type.includes('mouse') ? e.clientY : e.touches[0].clientY;

                const dx = clientX - startX;
                const dy = clientY - startY;

                if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                    isDragging = true;
                }

                if (isDragging) {
                    e.preventDefault();
                    let newLeft = initialLeft + dx;
                    let newTop = initialTop + dy;

                    const rect = this.fab.getBoundingClientRect();
                    const maxX = window.innerWidth - rect.width;
                    const maxY = window.innerHeight - rect.height;

                    newLeft = Math.max(0, Math.min(newLeft, maxX));
                    newTop = Math.max(0, Math.min(newTop, maxY));

                    this.fab.style.left = newLeft + 'px';
                    this.fab.style.top = newTop + 'px';
                    this.fab.style.bottom = 'auto';
                    this.fab.style.right = 'auto';
                }
            };

            const onFabUp = (e) => {
                document.removeEventListener('mousemove', onFabMove);
                document.removeEventListener('mouseup', onFabUp);
                document.removeEventListener('touchmove', onFabMove);
                document.removeEventListener('touchend', onFabUp);

                if (isDragging) {
                    this.fab.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
                    const rect = this.fab.getBoundingClientRect();
                    const centerX = rect.left + (rect.width / 2);

                    if (centerX < window.innerWidth / 2) {
                        this.fab.style.left = '20px';
                        this.fab.style.right = 'auto';
                    } else {
                        this.fab.style.left = 'auto';
                        this.fab.style.right = '20px';
                    }
                    this.fab.style.top = rect.top + 'px';
                    this.fab.style.bottom = 'auto';

                    if (this.widget) {
                        this.widget.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
                        if (centerX < window.innerWidth / 2) {
                            this.widget.style.left = '20px';
                            this.widget.style.right = 'auto';
                        } else {
                            this.widget.style.left = 'auto';
                            this.widget.style.right = '20px';
                        }
                        const widgetRect = this.widget.getBoundingClientRect();
                        const newWidgetTop = rect.top - widgetRect.height - 20;
                        this.widget.style.top = Math.max(20, newWidgetTop) + 'px';
                        this.widget.style.bottom = 'auto';
                    }
                }
            };

            this.fab.addEventListener('mousedown', onFabDown);
            this.fab.addEventListener('touchstart', onFabDown, { passive: false });

            this.fab.addEventListener('click', (e) => {
                if (isDragging) {
                    e.stopImmediatePropagation();
                    e.preventDefault();
                }
            }, true);
        }

        // --- 2. Dragging untuk Widget Chat melalui Header ---
        if (this.header && this.widget) {
            let isWidgetDragging = false;
            let startX, startY, initialLeft, initialTop;

            this.header.style.cursor = 'move';

            const onHeaderDown = (e) => {
                if (e.target.closest('button')) return;
                isWidgetDragging = true;

                const rect = this.widget.getBoundingClientRect();
                initialLeft = rect.left;
                initialTop = rect.top;

                startX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
                startY = e.type.includes('mouse') ? e.clientY : e.touches[0].clientY;

                this.widget.style.transition = 'none';

                document.addEventListener('mousemove', onHeaderMove);
                document.addEventListener('mouseup', onHeaderUp);
                document.addEventListener('touchmove', onHeaderMove, { passive: false });
                document.addEventListener('touchend', onHeaderUp);
            };

            const onHeaderMove = (e) => {
                if (!isWidgetDragging) return;
                e.preventDefault();

                const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
                const clientY = e.type.includes('mouse') ? e.clientY : e.touches[0].clientY;

                const dx = clientX - startX;
                const dy = clientY - startY;

                let newLeft = initialLeft + dx;
                let newTop = initialTop + dy;

                const rect = this.widget.getBoundingClientRect();
                const maxX = window.innerWidth - rect.width;
                const maxY = window.innerHeight - rect.height;

                newLeft = Math.max(0, Math.min(newLeft, maxX));
                newTop = Math.max(0, Math.min(newTop, maxY));

                this.widget.style.left = newLeft + 'px';
                this.widget.style.top = newTop + 'px';
                this.widget.style.bottom = 'auto';
                this.widget.style.right = 'auto';
            };

            const onHeaderUp = () => {
                isWidgetDragging = false;
                this.widget.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
                document.removeEventListener('mousemove', onHeaderMove);
                document.removeEventListener('mouseup', onHeaderUp);
                document.removeEventListener('touchmove', onHeaderMove);
                document.removeEventListener('touchend', onHeaderUp);
            };

            this.header.addEventListener('mousedown', onHeaderDown);
            this.header.addEventListener('touchstart', onHeaderDown, { passive: false });
        }
    }

    initEventListeners() {
        if (!this.widget) return;

        if (this.fab) {
            this.fab.addEventListener('click', () => {
                this.toggleOpen();
            });
        }

        this.header.addEventListener('click', (e) => {
            if (e.target.closest('button')) return;
        });

        this.closeBtn.addEventListener('click', () => {
            this.isOpen = false;
            this.updateWidgetState();
        });

        this.expandBtn.addEventListener('click', () => {
            this.isExpanded = !this.isExpanded;
            this.updateWidgetState();
            this.expandBtn.innerHTML = this.isExpanded ? '<i class="fas fa-compress-alt"></i>' : '<i class="fas fa-expand-alt"></i>';
        });

        this.sendBtn.addEventListener('click', () => this.sendMessage());

        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggleOpen() {
        if (this._aiDisabled) return;
        this.isOpen = !this.isOpen;
        this.updateWidgetState();
        if (this.isOpen) {
            setTimeout(() => this.input.focus(), 300);
        }
    }

    updateWidgetState() {
        if (this.isOpen) {
            this.widget.classList.remove('collapsed');
            if (this.isExpanded) {
                this.widget.classList.add('expanded');
            } else {
                this.widget.classList.remove('expanded');
            }
        } else {
            this.widget.classList.add('collapsed');
            this.widget.classList.remove('expanded');
        }
    }

    updateContext() {
        if (!this.contextIndicator) return;

        // Show data sources being monitored
        const sources = [];
        if (window.chartsManager?.cachedYearlyData) sources.push('Dashboard');
        if (window.tableManager?.currentData?.length) sources.push('Worksheet');
        if (window.recapPageManager?.filteredData?.length) sources.push('Recap');

        const contextText = sources.length > 0 ? sources.join(' + ') : 'Menunggu data...';
        this.contextIndicator.innerHTML = `<i class="fas fa-database"></i> Sumber: ${contextText}`;
    }

    addMessage(text, sender = 'user', isHtml = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-msg ${sender}`;

        if (isHtml) {
            msgDiv.innerHTML = text;
        } else {
            msgDiv.textContent = text;
        }

        this.messagesContainer.appendChild(msgDiv);
        this.scrollToBottom();
        return msgDiv;
    }

    scrollToBottom() {
        const body = document.querySelector('.ai-chat-body');
        body.scrollTop = body.scrollHeight;
    }

    // ======================================================================
    //  SEND MESSAGE — Main AI interaction
    // ======================================================================

    async sendMessage() {
        const text = this.input.value.trim();
        if (!text) return;

        this.input.value = '';
        this.input.disabled = true;
        this.sendBtn.disabled = true;

        this.addMessage(text, 'user');

        const loadingMsg = this.addMessage('<i class="fas fa-spinner fa-spin"></i> AI sedang menganalisa semua data...', 'loading', true);

        try {
            // ===== COLLECT ALL CONTEXT =====
            const { context, rawData } = this._buildAIContext();

            console.log('[AI Chat v3] Context collected:', {
                dashboard: !!context.dashboardSummary,
                monthly: context.monthlyBreakdown?.length || 0,
                customers: context.customerSummary?.length || 0,
                sales: context.salesSummary?.length || 0,
                recap: !!context.recapSummary,
                rawRows: rawData?.length || 0,
                activePanel: context.activePanel
            });

            // ===== BUILD SYSTEM PROMPT =====
            const systemPrompt = this._buildSystemPrompt(context, rawData);

            // ===== SEND TO GEMINI =====
            // Build conversation contents for multi-turn
            const contents = [];

            // Add conversation history (last 6 turns max for token efficiency)
            const recentHistory = this.conversationHistory.slice(-6);
            recentHistory.forEach(turn => {
                contents.push(turn);
            });

            // Add current user message
            contents.push({ role: 'user', parts: [{ text: text }] });

            let result;

            try {
                // 1. Try Vercel Serverless Proxy first (Secure)
                const response = await fetch('/api/ai-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        systemInstruction: { parts: [{ text: systemPrompt }] },
                        contents: contents
                    })
                });

                // If proxy doesn't exist (e.g. running locally without Vercel CLI) or returns HTML from SPA fallback
                const contentType = response.headers.get("content-type");
                if (response.status === 404 || (contentType && contentType.includes("text/html"))) {
                    throw new Error("Proxy Endpoint Not Found");
                }

                result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || 'Terjadi kesalahan pada server proxy AI');
                }
            } catch (proxyError) {
                console.warn('[AI Chat] Secure proxy unavailable or failed:', proxyError.message);

                // Jika errornya karena Rate Limit (429) dari server
                if (proxyError.message.toLowerCase().includes('quota') || proxyError.message.toLowerCase().includes('rate limit') || proxyError.message.includes('429')) {
                    throw new Error('Mohon maaf, layanan AI sedang memproses terlalu banyak antrean permintaan. Mohon tunggu sekitar 1 menit sebelum mengirim pesan lagi.');
                }

                // 2. Fallback to client-side API Key (Less Secure)
                const apiKey = typeof AI_CONFIG !== 'undefined' ? AI_CONFIG.GEMINI_API_KEY : null;
                if (!apiKey) {
                    throw new Error('Mohon maaf, layanan AI sedang sibuk atau limit tercapai. Silakan tunggu 1 menit lalu coba lagi.');
                }

                const fallbackResponse = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=${apiKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        systemInstruction: { parts: [{ text: systemPrompt }] },
                        contents: contents
                    })
                });

                result = await fallbackResponse.json();

                if (!fallbackResponse.ok) {
                    if (fallbackResponse.status === 429 || (result.error && result.error.message && result.error.message.toLowerCase().includes('quota'))) {
                        throw new Error('Mohon maaf, layanan AI sedang memproses terlalu banyak antrean permintaan. Mohon tunggu sekitar 1 menit sebelum mencoba lagi.');
                    }
                    throw new Error(result.error?.message || 'Gagal mengambil respons dari Gemini (Fallback)');
                }
            }

            loadingMsg.remove();

            let aiText = result.candidates[0].content.parts[0].text;

            // Save to conversation history
            this.conversationHistory.push({ role: 'user', parts: [{ text: text }] });
            this.conversationHistory.push({ role: 'model', parts: [{ text: aiText }] });

            // Parse Markdown
            aiText = aiText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            aiText = aiText.replace(/\n/g, '<br>');

            this.addMessage(aiText, 'ai', true);

            // Update context indicator
            this.updateContext();

        } catch (e) {
            console.error(e);
            loadingMsg.remove();
            this.addMessage('Maaf, terjadi kesalahan: ' + e.message, 'system');
        } finally {
            this.input.disabled = false;
            this.sendBtn.disabled = false;
            this.input.focus();
        }
    }

    /**
     * Build comprehensive system prompt with all available data
     */
    _buildSystemPrompt(context, rawData) {
        let prompt = `Anda adalah "AI Assistant", Asisten AI Keuangan Senior (Virtual CFO) dan Analis Ahli Supply Chain/Logistik di "Paketin Cargo".
Tugas utama Anda adalah memberikan *strategic advisory* kepada tim manajemen, direksi, dan admin melalui analisa mendalam terhadap data keuangan, performa sales, efisiensi vendor, dan tren operasional.

### PANDUAN KARAKTER & GAYA BAHASA (EXECUTIVE COMMUNICATION)
1. **Otoritatif & Solutif:** Berbicaralah layaknya seorang CFO berpengalaman. Jangan hanya menjadi kalkulator yang membaca angka. Anda harus menafsirkan angka tersebut menjadi kesimpulan bisnis. Gunakan kalimat seperti "Data menunjukkan adanya pendarahan margin di sektor X..." atau "Katalis utama pertumbuhan profit bulan ini adalah...".
2. **Kritis & Objektif:** Jangan ragu untuk menunjukkan kinerja buruk (misal: sales dengan margin sangat rendah, atau vendor yang membebani biaya).
3. **Bahasa Profesional:** Gunakan Bahasa Indonesia profesional berstandar korporat, diselingi istilah bisnis/finance umum (seperti *bottom-line*, *yield*, *cost-driver*, *MoM growth*).
4. **Format Estetis:** Gunakan bullet points, bold untuk metrik penting, dan format Rupiah (Rp 1.500.000) serta persentase (24.5%) secara konsisten agar mudah di-skimming oleh eksekutif.

### KAMUS DATA & DOMAIN LOGISTIK PAKETIN CARGO
Anda memiliki pemahaman tingkat dewa mengenai metrik operasional logistik berikut:
- **POD / Transaksi:** 1 baris data = 1 pengiriman (Proof of Delivery). Metrik ini mengukur *Volume Traffic* atau utilitas jaringan.
- **AWB (Airway Bill) / Resi:** Nomor identifikasi unik untuk setiap pengiriman.
- **Berat Aktual vs Berat Volume:** Di ekspedisi, biaya dihitung berdasarkan mana yang lebih besar antara berat asli (timbangan) atau berat dimensi/volume (PxLxT). Selisih perhitungan ini sering menjadi celah kebocoran margin atau potensi *revenue*.
- **Rute (Origin - Destination):** Kota asal dan kota tujuan. Jarak dan aksesibilitas menentukan struktur biaya logistik.
- **Revenue (Top-Line):** Total tagihan kotor ke pelanggan/pengirim. Tinggi revenue tidak berarti bisnis sehat jika margin hancur.
- **Total Biaya / COGS:** *Cost of Goods Sold* di logistik meliputi tarif kargo vendor utama (Darat/Laut/Udara), *surcharge* (biaya tambahan maskapai/pelayaran), biaya *handling*, *packing*, dan asuransi. Ini adalah *Variable Cost* utama.
- **Profit (Bottom-Line):** Revenue dikurangi Total Biaya. Ini adalah nyawa perusahaan.
- **Margin Kotor:** (Profit / Revenue) x 100%. Di industri logistik kargo, margin sehat biasanya di atas 15-20%. Margin di bawah 10% tergolong zona merah.
- **Pengirim / Customer:** Klien (B2B/B2C) yang menggunakan jasa Paketin Cargo.
- **Vendor / Via / Perusahaan:** Pihak ketiga penyedia armada (misal: maskapai udara, kapal RoRo, atau trucking darat). Menjaga keseimbangan biaya antar vendor adalah kunci efisiensi.
- **Sales / Account Executive:** Karyawan internal yang mendatangkan transaksi dari Customer.

### KERANGKA ANALISA STRATEGIS (CFO & LOGISTICS EXPERT MINDSET)
Terapkan *framework* berpikir berikut saat menganalisa data:
1. **Unit Economics & Yield Management:** 
   - Analisa korelasi antara Volume Pengiriman (POD) dengan Profitabilitas. Apakah lonjakan volume selaras dengan lonjakan profit? Jika volume naik tajam tapi profit stagnan, artinya *Yield per pengiriman* menurun (mungkin karena diskon berlebihan atau dominasi kargo berbiaya murah).
2. **Evaluasi Performa Sales (Quality over Quantity):** 
   - Hukum ketat CFO: "Revenue is Vanity, Margin is Sanity, Cash is Reality." Jangan puji Sales hanya karena omsetnya miliaran jika marginnya cuma 2%. Sales terbaik adalah mereka yang membawa *High-Margin Customers*.
3. **Analisa Efisiensi Vendor & Cost Drivers:** 
   - Pantau ketat persentase Total Biaya terhadap Revenue. Jika vendor tertentu memakan porsi biaya yang terlalu masif sehingga menyisakan margin tipis, rekomendasikan direksi untuk re-negosiasi kontrak SLA (Service Level Agreement) atau mencari *second-source vendor*.
4. **Risiko Konsentrasi Klien (Pareto / Concentration Risk):** 
   - Berikan peringatan dini (Early Warning System) jika 70-80% profit hanya disumbang oleh 2-3 pelanggan besar. Ketergantungan ini membahayakan *Cash Flow* dan kelangsungan bisnis jika klien tersebut *churn* atau menunda pembayaran (AR Aging risk).
5. **Route Profitability & Product Mix (Jika Data Tersedia):** 
   - Perhatikan rute (Asal-Tujuan) atau Jenis Barang mana yang paling menguntungkan. Rekomendasikan perusahaan untuk melakukan ekspansi marketing pada rute *high-yield* tersebut.

### ATURAN OPERASIONAL (CRITICAL RULES)
1. **Strictly Data-Driven (No Hallucination):** Jawab murni dari konteks data yang disuntikkan. Jangan menebak angka, tarif pasar luar, atau beban *overhead* (seperti gaji, sewa gudang) karena data tersebut tidak ada di sistem ini.
2. **Auto-Filter & Validasi Data (SANGAT PENTING):** Sebelum menghitung atau memberikan kesimpulan, **ABAIKAN dan BUANG** semua data yang kosong (*blank*), bernilai 0 tanpa alasan yang jelas, atau entri tanpa nama customer/pengirim (misal: "-", "—", atau string kosong). Jangan pernah memasukkan data "sampah" atau baris kosong database ini ke dalam kalkulasi Top Customer atau Total Revenue Anda agar jawaban Anda 100% akurat dan identik dengan Dashboard.
3. **Prioritas Navigasi Data:**
   - Untuk **Analisa Makro / Tren Keuangan:** Gunakan [BREAKDOWN BULANAN].
   - Untuk **KPI Karyawan / Komisi:** Gunakan [PERFORMA SALES PER BULAN].
   - Untuk **CRM / Key Account Management:** Gunakan [TOP CUSTOMER].
   - Untuk **Efisiensi Rantai Pasok:** Gunakan [PERFORMA VENDOR / SERVICE].
4. **The "So What?" Principle:** Setiap kali Anda menyajikan analisa data, Anda WAJIB mengakhirinya dengan sebuah sub-judul **"💡 Rekomendasi Strategis (Actionable Insight)"** yang berisi 1-2 poin tindakan nyata yang harus dilakukan direksi berdasarkan temuan Anda.
5. **Sembunyikan Analisa Margin:** Secara default, JANGAN menampilkan persentase margin ataupun analisa margin. Hanya tampilkan perhitungan dan data tentang Margin JIKA dan HANYA JIKA user secara eksplisit menggunakan kata "margin" dalam pertanyaannya.

Berikut adalah data terkini dari sistem website Paketin Cargo Finance:
`;

        // === SECTION 1: Dashboard Summary (Visual KPI) ===
        if (context.dashboardSummary) {
            prompt += `\n=== RINGKASAN DASHBOARD (Data Visual Yang Ditampilkan di Website) ===\n`;
            prompt += `Tahun Aktif: ${context.dashboardSummary.tahun || 'Tidak diketahui'}\n`;
            prompt += `Total Revenue: ${context.dashboardSummary.totalRevenue || 'N/A'}\n`;
            prompt += `Total Profit: ${context.dashboardSummary.totalProfit || 'N/A'}\n`;
            prompt += `Total Pengiriman (POD): ${context.dashboardSummary.totalPengiriman || 'N/A'}\n`;

            if (context.dashboardSummary.bulanDetail) {
                const bd = context.dashboardSummary.bulanDetail;
                prompt += `\nDetail Bulan Terpilih:\n`;
                prompt += `- Revenue Bulanan: ${bd.revenue}\n`;
                prompt += `- Profit Bulanan: ${bd.profit}\n`;
                prompt += `- Total Biaya: ${bd.totalBiaya}\n`;
                prompt += `- Margin: ${bd.margin}\n`;
                prompt += `- Pengiriman: ${bd.pengiriman}\n`;
            }
        }

        // === SECTION 2: Monthly Breakdown ===
        if (context.monthlyBreakdown) {
            prompt += `\n=== BREAKDOWN BULANAN ===\n`;
            prompt += JSON.stringify(context.monthlyBreakdown, null, 0) + '\n';
            prompt += `Catatan: jumlahPengiriman = total POD/proof of delivery bulan tersebut.\n`;
        }

        // === SECTION 3: Recap Summary ===
        if (context.recapSummary) {
            prompt += `\n=== REKAP DATA TERFILTER ===\n`;
            prompt += `Filter: Tahun ${context.recapSummary.filterTahun || 'Semua'}, Bulan: ${context.recapSummary.filterBulan || 'Semua'}\n`;
            prompt += `Total Transaksi/Pengiriman: ${context.recapSummary.totalPengiriman}\n`;
            prompt += `Total Revenue: Rp ${context.recapSummary.totalRevenue?.toLocaleString('id-ID')}\n`;
            prompt += `Total Biaya: Rp ${context.recapSummary.totalBiaya?.toLocaleString('id-ID')}\n`;
            prompt += `Total Profit: Rp ${context.recapSummary.totalProfit?.toLocaleString('id-ID')}\n`;
            prompt += `Margin Rata-Rata: ${context.recapSummary.marginRataRata}\n`;
            prompt += `Jumlah Customer Unik: ${context.recapSummary.jumlahCustomer}\n`;
            prompt += `Jumlah Sales: ${context.recapSummary.jumlahSales}\n`;
            prompt += `Service Tersedia: ${context.recapSummary.daftarService}\n`;
            prompt += `Perusahaan/Vendor: ${context.recapSummary.daftarPerusahaan}\n`;
        }

        // === SECTION 4: Customer Summary (POD, Revenue, Profit per Customer) ===
        if (context.customerSummary) {
            prompt += `\n=== TOP CUSTOMER (Ranking by Revenue) ===\n`;
            prompt += JSON.stringify(context.customerSummary.slice(0, 20), null, 0) + '\n';
            prompt += `Catatan: totalPOD = jumlah pengiriman/proof of delivery customer tersebut.\n`;
        }

        // === SECTION 4.5: Sales Summary (Performa per Sales per Bulan) ===
        if (context.salesSummary) {
            prompt += `\n=== PERFORMA SALES PER BULAN ===\n`;
            // Kirim semua agregasi sales per bulan agar AI bisa menganalisa tren tiap bulan
            prompt += JSON.stringify(context.salesSummary, null, 0) + '\n';
            prompt += `Catatan: jumlahCustomerUnik adalah total pengirim berbeda yang dihandle oleh sales tersebut di bulan bersangkutan.\n`;
        }

        // === SECTION 4.6: Vendor Summary (Performa per Vendor/Layanan per Bulan) ===
        if (context.vendorSummary) {
            prompt += `\n=== PERFORMA VENDOR / SERVICE PER BULAN ===\n`;
            prompt += JSON.stringify(context.vendorSummary, null, 0) + '\n';
        }

        // === SECTION 5: Raw Transaction Data ===
        if (rawData && rawData.length > 0) {
            // Smart truncation: For very large datasets, summarize rather than dump all
            const rowCount = rawData.length;
            const sampleSize = Math.min(rowCount, 1000); // Max 1000 rows to AI for token efficiency

            prompt += `\n=== DATA TRANSAKSI DETAIL (HANYA SAMPEL) ===\n`;
            prompt += `PERINGATAN KRITIKAL: Ini HANYA SAMPEL ${sampleSize} baris pertama dari total ${rowCount} baris keseluruhan tahun ini. JANGAN PERNAH menyimpulkan bahwa data mentah berhenti di tanggal tertentu (seperti 28 Januari) hanya karena sampel ini habis di tanggal tersebut. Data aktual website memiliki data sebulan/setahun penuh.\n`;
            prompt += `Untuk analisa total atau bulan spesifik (seperti performa Maret), SELALU gunakan data dari [PERFORMA SALES PER BULAN] atau [BREAKDOWN BULANAN] di atas, BUKAN dari sampel ini.\n`;
            prompt += `Kolom sampel: tgl=tanggal pickup, perusahaan=nama vendor/via, customer=pengirim, sales=sales, `;
            prompt += `service=layanan, via=jalur, aktual_kg=berat aktual, vol_kg=berat volume, `;
            prompt += `harga_perkilo=harga per kg, surcharge/packing/handling=biaya tambahan, `;
            prompt += `revenue=penjualan, total_biaya=ongkos, profit=laba, asal=origin, tujuan=destination, `;
            prompt += `jenis_barang=item type, vendor=vendor name, asuransi=insurance, nilai_barang=goods value.\n`;
            prompt += JSON.stringify(rawData.slice(0, sampleSize)) + '\n';
        }

        prompt += `\n=== KONTEKS & FLEKSIBILITAS ===\n`;
        prompt += `Panel aktif user saat ini: ${context.activePanel || 'tidak diketahui'}\n`;
        prompt += `Catatan Penting:\n`;
        prompt += `- Anda memiliki akses ke SELURUH DATA TAHUNAN. Anda bisa menjawab pertanyaan tentang bulan apa pun, customer apa pun, atau vendor/service apa pun tanpa peduli di panel mana user berada saat ini.\n`;
        prompt += `- "Total Pengiriman", "POD", atau "Proof of Delivery" = jumlah baris transaksi (setiap baris = 1 pengiriman).\n`;
        prompt += `- Data di atas sudah PASTI sesuai dengan database dan website.\n`;
        prompt += `- Jika ditanya hal spesifik tentang bulan tertentu, silakan cari di [BREAKDOWN BULANAN], [PERFORMA SALES PER BULAN], atau [PERFORMA VENDOR / SERVICE PER BULAN].\n`;
        prompt += `- Jika ditanya soal "PaketIn Cargo" di bulan "Februari", temukan di [PERFORMA VENDOR / SERVICE PER BULAN] dengan mencocokkan vendor dan bulan.\n`;

        return prompt;
    }
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', () => {
    window.aiChatManager = new AIChatManager();
});
