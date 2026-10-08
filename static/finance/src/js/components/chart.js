/**
 * CHART MANAGER v3.0: Dashboard Bar Chart
 * Menampilkan diagram balok Revenue & Profit per bulan
 * dengan konfigurasi tahun & bulan yang sinkron dengan file tahunan KPI.
 */
class ChartsManager {
    constructor() {
        this.revenueChart = null;
        this.serviceChart = null;
        this.topCustomerChart = null;
        this.selectedYear = new Date().getFullYear();
        this.selectedMonth = null; // null = semua bulan (recap tahunan)
        this.cachedYearlyData = null;
        this.cachedFileId = null;
    }

    async renderDashboardStats(data) {
        if (!data) return;

        // Filter baris kosong dari data keseluruhan tahun & pastikan bukan row konfigurasi sheet
        const realData = data.filter(r => r.id && r.nama !== '__SHEET_CONFIG__' && (r.nama || r.tanggal_pickup || r.awb));
        
        // Simpan ke cache agar bisa diakses oleh AI (HANYA YANG VALID)
        this.cachedYearlyData = realData;
        if (window.yearlyFileManager) {
            this.cachedFileId = window.yearlyFileManager.activeFileId;
        }


        // Sync selectedYear
        if (window.yearlyFileManager) {
            const activeFile = window.yearlyFileManager.files.find(f => f.id == window.yearlyFileManager.activeFileId);
            if (activeFile) {
                const m = activeFile.name.match(/(\d{4})/);
                if (m) {
                    this.selectedYear = parseInt(m[1]);
                    const displayYear = document.getElementById('displayYear');
                    if (displayYear) displayYear.textContent = this.selectedYear;
                }
            }
        }

        // Build selectors
        this._buildYearSelector();

        // 1. Calculate Totals based on selection (Yearly vs Monthly)
        let summary;
        const statLabelSuffix = this.selectedMonth ? `(${['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'][this.selectedMonth - 1]} ${this.selectedYear})` : `(Tahunan ${this.selectedYear})`;

        if (this.selectedMonth) {
            summary = window.formulaEngine.compute('monthly_summary', realData, { year: this.selectedYear, month: this.selectedMonth });
        } else {
            summary = window.formulaEngine.compute('yearly_summary', realData, { year: this.selectedYear });
        }

        // Update labels on the cards
        const revLabel = document.querySelector('#totalRevenue').previousElementSibling;
        const profLabel = document.querySelector('#totalProfit').previousElementSibling;
        if (revLabel) revLabel.textContent = `Total Revenue ${statLabelSuffix}`;
        if (profLabel) profLabel.textContent = `Total Profit ${statLabelSuffix}`;

        this._updateStatCards(summary, realData);

        // Filter for charts/tables
        let filteredData = this.selectedMonth ? realData.filter(r => {
            if (!r.tanggal_pickup) return false;
            const d = window.formulaEngine._parseDate(r.tanggal_pickup);
            return d && d.getFullYear() === this.selectedYear && (d.getMonth() + 1) === this.selectedMonth;
        }) : realData;

        this._renderBarChart(realData);
        this._renderServiceChart(filteredData);
        this._renderTopCustomerChart(filteredData);
        this.renderRecentTable(filteredData);
        this._populateMonthlyPanel(realData);
    }


    _updateStatCards(summary, allData) {
        const revEl = document.getElementById('totalRevenue');
        const profEl = document.getElementById('totalProfit');
        const shipEl = document.getElementById('totalShipments');

        if (!revEl || !profEl || !shipEl) return;

        let finalRev = summary.totalRevenue || summary.revenue || 0;
        let finalProf = summary.totalProfit || summary.profit || 0;
        let finalCount = summary.count || 0;

        // Update labels (Just keep it simple: Total Revenue / Total Profit)
        const revLabel = revEl.previousElementSibling;
        const profLabel = profEl.previousElementSibling;
        if (revLabel) revLabel.textContent = `Total Revenue`;
        if (profLabel) profLabel.textContent = `Total Profit`;

        revEl.textContent = window.Formatter.currency(Math.round(finalRev));
        profEl.textContent = window.Formatter.currency(Math.round(finalProf));
        shipEl.textContent = finalCount;
        this._updateFloatingWarning(summary);
    }

    _updateFloatingWarning(summary) {
        const floatingEl = document.getElementById('dashboardDiscrepancyWarning');
        if (floatingEl) floatingEl.remove();
    }

    _buildYearSelector() {
        // Get years from KPI files
        const files = window.yearlyFileManager ? window.yearlyFileManager.files || [] : [];
        const years = new Set();

        files.forEach(f => {
            const match = f.name.match(/(\d{4})/);
            if (match) years.add(parseInt(match[1]));
        });

        // Fallback: add current year
        if (years.size === 0) years.add(new Date().getFullYear());

        const sortedYears = [...years].sort((a, b) => b - a);

        this.availableYears = sortedYears;
        this._buildMonthSelector();
    }

    _buildMonthSelector() {
        const container = document.getElementById('dashboardMonthFilter');
        if (!container) return;

        const months = ['Semua Bulan', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        let html = `<select class="month-pill-select" onchange="chartsManager.selectMonth(parseInt(this.value))">`;
        html += months.map((m, i) => {
            const isSelected = i === (this.selectedMonth || 0);
            return `<option value="${i}" ${isSelected ? 'selected' : ''}>${m}</option>`;
        }).join('');
        html += '</select>';

        // Keep the year selector if it exists
        if (this.availableYears && this.availableYears.length > 0) {
            html += `<select class="year-pill-select" onchange="chartsManager.selectYear(parseInt(this.value))">`;
            this.availableYears.forEach(y => {
                const isSelected = y === this.selectedYear;
                html += `<option value="${y}" ${isSelected ? 'selected' : ''}>${y}</option>`;
            });
            html += `</select>`;
        }

        container.innerHTML = html;
    }

    selectYear(year) {
        this.selectedYear = parseInt(year);
        this.selectedMonth = null;

        // Auto-switch file if there's a matching file
        if (window.yearlyFileManager) {
            const matchingFile = window.yearlyFileManager.files.find(f => f.name.includes(year));
            if (matchingFile && matchingFile.id !== window.yearlyFileManager.activeFileId) {
                window.yearlyFileManager.switchFile(matchingFile.id, true); // true = suppressToggle
                return; // switchFile will trigger data reload
            }
        }

        this._buildMonthSelector();
        this._reloadDashboardData();
    }

    selectMonth(month) {
        console.log('[ChartsManager] Selecting month:', month);
        this.selectedMonth = month === 0 ? null : month;
        this._buildMonthSelector();

        // Force refresh data from database to ensure no missing recap
        this.cachedYearlyData = null;
        this._reloadDashboardData();
    }

    showMonthlyDetail() {
        const panel = document.getElementById('monthlyDetailPanel');
        if (panel) {
            panel.classList.add('active');
            this._updateMonthlyDetailTitle();
        }
    }

    hideMonthlyDetail() {
        const panel = document.getElementById('monthlyDetailPanel');
        if (panel) panel.classList.remove('active');
    }

    _updateMonthlyDetailTitle() {
        if (!this.selectedMonth) return;
        const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        const title = document.getElementById('monthlyDetailTitle');
        if (title) {
            title.innerHTML = `<i class="fas fa-calendar-check"></i> Detail ${months[this.selectedMonth - 1]} ${this.selectedYear}`;
        }
    }



    _populateMonthlyPanel(data) {
        if (!this.selectedMonth) return;

        const summary = window.formulaEngine.compute('monthly_summary', data, {
            year: this.selectedYear, month: this.selectedMonth
        });

        const el = (id) => document.getElementById(id);
        if (el('monthlyRevenue')) el('monthlyRevenue').textContent = window.Formatter.currency(summary.totalRevenue);
        if (el('monthlyProfit')) {
            el('monthlyProfit').textContent = window.Formatter.currency(summary.totalProfit);
            el('monthlyProfit').style.color = summary.totalProfit >= 0 ? '#16a34a' : '#dc2626';
        }
        if (el('monthlyCost')) el('monthlyCost').textContent = window.Formatter.currency(summary.totalCost);
        if (el('monthlyMargin')) el('monthlyMargin').textContent = window.Formatter.percent(summary.avgMargin);
        if (el('monthlyShipments')) el('monthlyShipments').textContent = summary.count || 0;
    }

    async _reloadDashboardData() {
        const fileId = window.yearlyFileManager ? window.yearlyFileManager.activeFileId : null;
        if (!fileId) return;

        // Use cache if same file and data already exists
        if (this.cachedFileId === fileId && this.cachedYearlyData) {
            await this.renderDashboardStats(this.cachedYearlyData);
            return;
        }

        const data = await databaseManager.fetchYearlyData(fileId, 'id, nama, tanggal_pickup, awb, awb_sistem, pengirim, service, penjualan, profit, total_biaya, sheet_id, formulas');
        if (data && data.length) {
            this.cachedFileId = fileId;
            this.cachedYearlyData = data;
            await this.renderDashboardStats(data);
        }
    }

    // Call this when data in spreadsheet changes to invalidate cache
    invalidateCache() {
        this.cachedYearlyData = null;
        this.cachedFileId = null;
    }

    _renderBarChart(data) {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        if (this.revenueChart) this.revenueChart.destroy();

        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
        const revenues = [];
        const profits = [];
        const costs = [];

        for (let i = 1; i <= 12; i++) {
            const mSummary = window.formulaEngine.compute('monthly_summary', data, {
                year: this.selectedYear, month: i
            });
            revenues.push(mSummary.totalRevenue);
            profits.push(mSummary.totalProfit);
            costs.push(mSummary.totalCost);
        }

        const textColor = '#374151';
        const gridColor = 'rgba(0,0,0,0.05)';

        this.revenueChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revenues,
                        backgroundColor: this.selectedMonth
                            ? months.map((_, i) => i + 1 === this.selectedMonth
                                ? 'rgba(204, 0, 0, 0.9)' : 'rgba(204, 0, 0, 0.1)')
                            : 'rgba(204, 0, 0, 0.8)',
                        borderColor: '#9B0000',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        borderSkipped: false
                    },
                    {
                        label: 'Profit',
                        data: profits,
                        backgroundColor: this.selectedMonth
                            ? months.map((_, i) => i + 1 === this.selectedMonth
                                ? 'rgba(34, 197, 94, 0.9)' : 'rgba(34, 197, 94, 0.1)')
                            : 'rgba(34, 197, 94, 0.8)',
                        borderColor: '#15803d',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        borderSkipped: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                onClick: (e, activeElements) => {
                    if (activeElements.length > 0) {
                        const monthIndex = activeElements[0].index + 1;
                        this.selectMonth(monthIndex);
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            font: { size: 11, weight: '600' },
                            usePointStyle: true,
                            pointStyle: 'rectRounded',
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleFont: { size: 12, weight: '700' },
                        bodyFont: { size: 11 },
                        padding: 12,
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${window.Formatter.currency(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: textColor,
                            font: { size: 10 },
                            callback: (v) => v >= 1000000 ? (v / 1000000).toFixed(1) + 'M' : v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v
                        },
                        grid: { color: gridColor, drawBorder: false }
                    },
                    x: {
                        ticks: { color: textColor, font: { size: 11, weight: '500' } },
                        grid: { display: false }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const monthIndex = elements[0].index + 1;
                        this.selectMonth(monthIndex);
                    }
                }
            }
        });
    }

    _renderServiceChart(data) {
        const ctx = document.getElementById('serviceChart');
        if (!ctx) return;
        if (this.serviceChart) this.serviceChart.destroy();

        const vendorMap = {};
        data.forEach(r => {
            if (r.id === '__SHEET_CONFIG__') return;
            let v = (r.nama || 'Lainnya').trim().toUpperCase();
            if (v === '__SHEET_CONFIG__') return;

            // Alias grouping
            if (v === 'PAKETIN CARGO' || v === 'PAKETIN' || v === 'AMANAH') {
                v = 'PAKETIN CARGO';
            } else if (v === 'PAKETIN EXPRESS' || v === 'EXPRESS' || v === 'SINERGI' || v === 'PAKETIN XPRESS') {
                v = 'PAKETIN EXPRESS';
            } else if (v === 'SARANA EXPRESS' || v === 'SARANA' || v === 'SARANA XPRESS') {
                v = 'SARANA EXPRESS';
            }

            if (!vendorMap[v]) vendorMap[v] = 0;
            vendorMap[v]++;
        });

        const sorted = Object.entries(vendorMap).sort((a,b) => b[1] - a[1]);
        const labels = sorted.map(i => i[0]);
        const values = sorted.map(i => i[1]);

        this.serviceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: ['#ef4444', '#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#64748b', '#94a3b8', '#ec4899', '#14b8a6'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 10, font: {size: 10} } }
                },
                cutout: '65%'
            }
        });
    }

    _renderTopCustomerChart(data) {
        const ctx = document.getElementById('topCustomerChart');
        if (!ctx) return;
        if (this.topCustomerChart) this.topCustomerChart.destroy();

        const customerMap = {};
        data.forEach(r => {
            if (r.id === '__SHEET_CONFIG__') return;
            const cust = (r.pengirim || 'Tanpa Nama').trim();
            if (cust === '__SHEET_CONFIG__') return;
            const profit = window.formulaEngine ? window.formulaEngine._getCellValueByA1_Logic(r.profit) : (parseFloat(r.profit) || 0);
            if (!customerMap[cust]) customerMap[cust] = 0;
            customerMap[cust] += profit;
        });

        const sorted = Object.entries(customerMap).sort((a,b) => b[1] - a[1]).slice(0, 5);
        const labels = sorted.map(i => i[0].length > 15 ? i[0].substring(0,15)+'...' : i[0]);
        const values = sorted.map(i => i[1]);

        this.topCustomerChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Profit',
                    data: values,
                    backgroundColor: '#16a34a',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (c) => window.Formatter.currency(c.raw)
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: (v) => v >= 1000000 ? (v/1000000).toFixed(1)+'M' : v >= 1000 ? (v/1000).toFixed(0)+'K' : v,
                            font: {size: 10}
                        }
                    },
                    y: {
                        ticks: { font: {size: 10, weight: '600'} }
                    }
                }
            }
        });
    }

    renderRecentTable(data) {
        // Initialize year filter dropdown if needed
        const yearSel = document.getElementById('recentFilterYear');
        if (yearSel && !yearSel.options.length) {
            const startYear = 2024;
            const endYear = new Date().getFullYear() + 1;
            let yHtml = '';
            for (let y = endYear; y >= startYear; y--) {
                yHtml += `<option value="${y}" ${y === this.selectedYear ? 'selected' : ''}>${y}</option>`;
            }
            yearSel.innerHTML = yHtml;
        }

        setTimeout(() => {
            const tbody = document.getElementById('recentTableBody');
            if (!tbody) return;

            // Determine data source: use provided data or filter from cached yearly data
            let sourceData = data;
            if (!sourceData && this.cachedYearlyData) {
                const yEl = document.getElementById('recentFilterYear');
                const mEl = document.getElementById('recentFilterMonth');
                const filterYear = yEl ? parseInt(yEl.value) : this.selectedYear;
                const filterMonth = mEl ? parseInt(mEl.value) : 0;

                sourceData = this.cachedYearlyData.filter(r => {
                    if (!r.nama && !r.tanggal_pickup) return false;
                    if (filterMonth === 0) {
                        // Filter only by year if provided
                        if (!r.tanggal_pickup) return true;
                        const d = window.formulaEngine._parseDate(r.tanggal_pickup);
                        return !d || d.getFullYear() === filterYear;
                    }
                    if (!r.tanggal_pickup) return false;
                    const d = window.formulaEngine._parseDate(r.tanggal_pickup);
                    if (!d) return false;
                    return d.getFullYear() === filterYear && d.getMonth() + 1 === filterMonth;
                });
            }

            const realData = (sourceData || []).filter(r => r.nama !== '__SHEET_CONFIG__' && (r.nama || r.tanggal_pickup));
            if (realData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:20px; color:var(--text-muted);">Belum ada data</td></tr>';
                return;
            }

            // Group by combination of customer name and company (via)
            const customerMap = {};
            realData.forEach((row, idx) => {
                const namaCustomer = (row.pengirim || '').trim() || '—';
                const viaData = (row.nama || '').trim() || '—';

                let mappedVia = viaData;
                const upperVia = viaData.toUpperCase();

                if (upperVia.includes('PAKETIN CARGO')) {
                    mappedVia = 'AMANAH';
                } else if (upperVia.includes('PAKETIN XPRESS')) {
                    mappedVia = 'SINERGI';
                } else if (upperVia.includes('SARANA')) {
                    mappedVia = 'SARANA';
                } else {
                    // Fallback just in case they type something else
                    mappedVia = viaData;
                }

                // Gunakan nilai penjualan & profit persis dari database/worksheet agar sinkron 100%
                const penjualan = window.formulaEngine ? window.formulaEngine._getCellValueByA1_Logic(row.penjualan) : (parseFloat(row.penjualan) || 0);
                const profit = window.formulaEngine ? window.formulaEngine._getCellValueByA1_Logic(row.profit) : (parseFloat(row.profit) || 0);
                
                const key = `${namaCustomer}::${mappedVia}`;
                if (!customerMap[key]) {
                    customerMap[key] = { nama: namaCustomer, via: mappedVia, pod: 0, revenue: 0, profit: 0 };
                }

                customerMap[key].revenue += penjualan;
                customerMap[key].profit += profit;
                customerMap[key].pod += 1;
            });

            // Sort by revenue descending and take only the top 10
            const sorted = Object.values(customerMap)
                .sort((a, b) => b.revenue - a.revenue)
                .slice(0, 10);

            tbody.innerHTML = sorted.map((info, idx) => {
                const no = idx + 1;
                const revFmt = window.Formatter ? window.Formatter.currency(info.revenue) : new Intl.NumberFormat('en-US').format(info.revenue);
                const profFmt = window.Formatter ? window.Formatter.currency(info.profit) : new Intl.NumberFormat('en-US').format(info.profit);
                const profitColor = info.profit >= 0 ? '#16a34a' : '#dc2626';

                return `
                    <tr>
                        <td class="col-no" style="text-align:center;">${no}</td>
                        <td style="text-align:center; color:#000; font-weight:600;">${info.via}</td>
                        <td class="customer-name" style="text-align:left; color:#000; font-weight:600;">${info.nama}</td>
                        <td class="col-pod" style="text-align:center; color:var(--text-secondary); font-weight:600;">${info.pod}</td>
                        <td class="col-revenue" style="text-align:right; font-weight:700; color:#000;">${revFmt}</td>
                        <td class="col-profit" style="text-align:right; font-weight:700; color:${profitColor};">${profFmt}</td>
                    </tr>
                `;
            }).join('');
        }, 50);
    }

    destroyCharts() {
        if (this.revenueChart) { this.revenueChart.destroy(); this.revenueChart = null; }
        if (this.serviceChart) { this.serviceChart.destroy(); this.serviceChart = null; }
        if (this.topCustomerChart) { this.topCustomerChart.destroy(); this.topCustomerChart = null; }
    }
}

const chartsManager = new ChartsManager();
window.chartsManager = chartsManager;