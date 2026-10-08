/**
 * RECAP MANAGER v5.1 (Worksheet Data Synchronization, Year Resolving & Inline Table Summaries)
 * Menyediakan dashboard analisis worksheet dengan navigasi menu sidebar:
 * - Revenue: Detail penjualan dan total omset bulanan/tahunan.
 * - Profit: Pengawasan margin, biaya operasional, dan profitabilitas.
 * - List Customer: Analisis pengiriman, revenue, dan profit per customer teraktif.
 * - Asuransi: Placeholder dinamis untuk analisis premi (Coming Soon).
 */

class RecapPageManager {
    constructor() {
        this.rawData = [];
        this.cleanData = [];
        this.filteredData = [];
        this.activeTab = 'revenue'; // default tab
        this.initialized = false;
        this.advFilters = {
            perusahaan: 'all',
            sales: 'all',
            service: 'all',
            minRevenue: '',
            maxRevenue: '',
            startDate: '',
            endDate: ''
        };
    }

    _parseLocaleFloat(val) {
        return window.Formatter ? window.Formatter.parseLocaleFloat(val) : 0;
    }

    async init() {
        this._populateMonthSelect();
        this._populateYearSelect();
        
        // Bind year select change to handle switching database files
        const yearSelect = document.getElementById('recapFilterYear');
        if (yearSelect && !this.initialized) {
            yearSelect.addEventListener('change', async (e) => {
                await this.handleYearChange(e.target.value);
            });
        }
        
        this.initialized = true;
        await this.refreshData();
    }

    switchTab(tabId) {
        this.activeTab = tabId;
        
        // Update active class in sidebar menu
        document.querySelectorAll('.recap-menu-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.getElementById(`recapMenuBtn-${tabId}`);
        if (activeBtn) activeBtn.classList.add('active');

        // Show/hide search and filter bar based on tab (located inside recap-main now)
        const filterBar = document.getElementById('recapFilterBar');
        if (filterBar) {
            filterBar.style.display = 'flex';
        }

        // Show/hide main table wrapper depending on tab
        const tableCard = document.getElementById('recapTableCard');
        if (tableCard) {
            tableCard.style.display = 'flex';
        }

        // Remove old insurance coming soon card if exists
        const oldPlaceholder = document.getElementById('recapInsurancePlaceholder');
        if (oldPlaceholder) oldPlaceholder.remove();

        this.filterData();
    }

    _populateMonthSelect() {
        const select = document.getElementById('recapFilterMonth');
        if (!select || select.options.length > 0) return;
        
        const months = [
            { value: 'all', label: 'Semua Bulan' },
            { value: 1, label: 'Januari' },
            { value: 2, label: 'Februari' },
            { value: 3, label: 'Maret' },
            { value: 4, label: 'April' },
            { value: 5, label: 'Mei' },
            { value: 6, label: 'Juni' },
            { value: 7, label: 'Juli' },
            { value: 8, label: 'Agustus' },
            { value: 9, label: 'September' },
            { value: 10, label: 'Oktober' },
            { value: 11, label: 'November' },
            { value: 12, label: 'Desember' }
        ];
        
        select.innerHTML = months.map(m => `<option value="${m.value}">${m.label}</option>`).join('');
    }

    _populateYearSelect() {
        const select = document.getElementById('recapFilterYear');
        if (!select) return;
        
        const files = window.yearlyFileManager ? window.yearlyFileManager.files || [] : [];
        if (files.length === 0) {
            if (select.options.length === 0) {
                select.innerHTML = '<option value="all" selected>Semua Tahun</option>';
            }
            return;
        }
        
        const currentSelected = select.value || 'all';
        
        const years = new Set();
        files.forEach(f => {
            const match = f.name.match(/(\d{4})/);
            if (match) years.add(parseInt(match[1]));
        });
        if (years.size === 0) years.add(new Date().getFullYear());
        
        const sortedYears = [...years].sort((a, b) => b - a);
        let html = '<option value="all">Semua Tahun</option>';
        
        sortedYears.forEach(y => {
            html += `<option value="${y}">Tahun ${y}</option>`;
        });
        select.innerHTML = html;
        select.value = currentSelected;
    }

    _getActiveFileYear() {
        if (window.yearlyFileManager && window.yearlyFileManager.files) {
            const activeFile = window.yearlyFileManager.files.find(f => f.id == window.yearlyFileManager.activeFileId);
            if (activeFile) {
                const match = activeFile.name.match(/(\d{4})/);
                if (match) return parseInt(match[1]);
            }
        }
        return new Date().getFullYear();
    }

    _getRowYear(row) {
        if (row.tanggal_pickup) {
            const d = window.formulaEngine ? window.formulaEngine._parseDate(row.tanggal_pickup) : null;
            if (d) return d.getFullYear();
        }
        return this._getActiveFileYear();
    }

    async handleYearChange(year) {
        if (window.yearlyFileManager) {
            const matchingFile = window.yearlyFileManager.files.find(f => f.name.includes(year));
            if (matchingFile && matchingFile.id !== window.yearlyFileManager.activeFileId) {
                await window.yearlyFileManager.switchFile(matchingFile.id, true);
            }
        }
        await this.refreshData();
    }

    async refreshData() {
        // Automatically sync the year dropdown selection with the active yearly file on reload
        this._populateYearSelect();
        
        const yearSelect = document.getElementById('recapFilterYear');
        const selectedYearVal = yearSelect ? yearSelect.value : 'all';
        
        const loader = document.getElementById('recapTableBody');
        if (loader) {
            loader.innerHTML = `<tr><td colspan="100" style="padding: 80px; text-align: center; color: var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size: 2.2rem; color: var(--red); display: inline-block; margin-bottom: 15px;"></i><div style="font-weight: 600; font-size: 0.9rem;">Mengunduh data rekapitulasi...</div></td></tr>`;
        }

        try {
            // 1. Fetch from backend database for the selected file(s)
            let dbData = [];
            if (selectedYearVal === 'all') {
                const files = window.yearlyFileManager ? window.yearlyFileManager.files || [] : [];
                const promises = files.map(f => window.databaseManager.fetchYearlyData(f.id));
                const results = await Promise.all(promises);
                results.forEach(res => {
                    if (res) dbData.push(...res);
                });
            } else {
                let fileId = null;
                if (window.yearlyFileManager && window.yearlyFileManager.files) {
                    const matchingFile = window.yearlyFileManager.files.find(f => f.name.includes(selectedYearVal));
                    if (matchingFile) {
                        fileId = matchingFile.id;
                    }
                }
                if (fileId) {
                    dbData = await window.databaseManager.fetchYearlyData(fileId);
                }
            }

            // 2. Fetch from active live worksheet in-memory to ensure draft/unsaved data is responsive
            let liveData = [];
            if (window.tableManager && window.tableManager.currentData) {
                liveData = window.tableManager.currentData;
            }

            // 3. Merge both datasets uniquely by ID
            const mergedMap = new Map();
            dbData.forEach(r => { if (r && r.id) mergedMap.set(String(r.id), r); });
            liveData.forEach(r => { if (r && r.id) mergedMap.set(String(r.id), r); });

            this.rawData = Array.from(mergedMap.values());

            // Fetch all sheets across loaded years to build a robust sheet ID -> Sheet mapping
            const sheetsMap = new Map();
            const files = window.yearlyFileManager ? window.yearlyFileManager.files || [] : [];
            if (files.length > 0) {
                try {
                    const sheetsPromises = files.map(f => window.databaseManager.fetchSheets(f.id));
                    const sheetsResults = await Promise.all(sheetsPromises);
                    sheetsResults.forEach(sheets => {
                        if (sheets) {
                            sheets.forEach(s => sheetsMap.set(s.id, s));
                        }
                    });
                } catch (e) {
                    console.error('[Recap] Failed to fetch sheets for mapping:', e);
                }
            }
            this.recapSheetsMap = sheetsMap;

            const isNumberVal = (v) => {
                if (v === null || v === undefined || v === '') return false;
                const n = parseFloat(v);
                return !isNaN(n) && n !== 0;
            };

            // 4. Filter completely empty spreadsheet rows (keeping rows with any visible values)
            this.cleanData = this.rawData.filter(r => r && r.id && (
                (r.nama && String(r.nama).trim() !== '') || 
                (r.tanggal_pickup && String(r.tanggal_pickup).trim() !== '') || 
                (r.pengirim && String(r.pengirim).trim() !== '') || 
                (r.awb && String(r.awb).trim() !== '') ||
                isNumberVal(r.penjualan) ||
                isNumberVal(r.total_biaya) ||
                isNumberVal(r.profit)
            ));

            this._lastDbCount = dbData.length;
            this._lastLiveCount = liveData.length;
            this._lastRawCount = this.rawData.length;
            this._lastCleanCount = this.cleanData.length;

            console.log('[Recap Diagnostic] DB:', dbData.length, 'Live:', liveData.length, 'Raw:', this.rawData.length, 'Clean:', this.cleanData.length);

            // Populate advanced filter choices dynamically
            this.populateAdvFilterOptions();

            // Remove old debug panel if exists to completely clean the view
            const debugPanel = document.getElementById('recapDebugDiagnostics');
            if (debugPanel) debugPanel.remove();

            this.filterData();
        } catch (error) {
            console.error('[RecapPageManager] Gagal refresh data:', error);
            if (loader) {
                loader.innerHTML = `<tr><td colspan="100" style="padding: 60px; text-align: center; color: var(--red); font-weight: 700;"><i class="fas fa-exclamation-triangle" style="font-size: 2rem; display: block; margin-bottom: 12px;"></i>Gagal memuat data dari server. Silakan klik tombol Refresh.</td></tr>`;
            }
        }
    }

    _getRowMonth(row) {
        if (row.tanggal_pickup) {
            const d = window.formulaEngine ? window.formulaEngine._parseDate(row.tanggal_pickup) : null;
            if (d) return d.getMonth() + 1;
        }
        
        // Lookup sheet_id map in SheetsManager to find sheet month name
        const sheetId = row.sheet_id || window.activeSheetId;
        if (sheetId) {
            let sheet = null;
            if (this.recapSheetsMap) {
                sheet = this.recapSheetsMap.get(Number(sheetId)) || this.recapSheetsMap.get(String(sheetId));
            }
            if (!sheet && window.sheetsManager && window.sheetsManager.sheets) {
                sheet = window.sheetsManager.sheets.find(s => s.id == sheetId);
            }
            if (sheet) {
                const name = sheet.name.toLowerCase();
                const sheetType = String(sheet.sheet_type || '').toLowerCase();
                if (name.includes('config') || sheetType === 'config') {
                    return null;
                }

                const matchMonth = name.match(/bulan\s+(\d+)/);
                if (matchMonth) return parseInt(matchMonth[1]);
                
                if (name.includes('jan')) return 1;
                if (name.includes('feb')) return 2;
                if (name.includes('mar')) return 3;
                if (name.includes('apr')) return 4;
                if (name.includes('mei')) return 5;
                if (name.includes('jun')) return 6;
                if (name.includes('jul')) return 7;
                if (name.includes('agu') || name.includes('aug')) return 8;
                if (name.includes('sep')) return 9;
                if (name.includes('okt') || name.includes('oct')) return 10;
                if (name.includes('nov')) return 11;
                if (name.includes('des') || name.includes('dec')) return 12;
            }
        }
        
        return null;
    }

    _formatDateDMY(dateStr) {
        if (!dateStr) return '—';
        // Handle yyyy-mm-dd or yyyy/mm/dd format
        const match = dateStr.match(/^(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
        if (match) {
            const [_, y, m, d] = match;
            return `${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`;
        }
        
        // If it's already in dd/mm/yyyy or dd-mm-yyyy, return as is
        const matchDMY = dateStr.match(/^(\d{1,2})[-\/](\d{1,2})[-\/](\d{4})/);
        if (matchDMY) {
            const [_, d, m, y] = matchDMY;
            return `${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`;
        }
        
        // Fallback: try parsing with Date
        try {
            const d = new Date(dateStr);
            if (!isNaN(d.getTime())) {
                const day = String(d.getDate()).padStart(2, '0');
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const year = d.getFullYear();
                return `${day}/${month}/${year}`;
            }
        } catch (e) {}
        
        return dateStr;
    }

    filterData() {

        const yearSelect = document.getElementById('recapFilterYear');
        const monthSelect = document.getElementById('recapFilterMonth');
        const searchInput = document.getElementById('recapSearch');
        
        const selectedYearVal = yearSelect ? yearSelect.value : 'all';
        const selectedMonth = monthSelect ? monthSelect.value : 'all';
        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        
        const initialCount = (this.cleanData || []).length;
        let filtered = this.cleanData || [];
        
        // 1. Filter out subtotal/formula rows to present a pristine transaction reporting view
        // ONLY filter if the formula contains SUBTOTAL or if the name indicates a total row
        filtered = filtered.filter(row => {
            // Exclude __SHEET_CONFIG__ rows and any rows belonging to a config sheet
            if (row.nama === '__SHEET_CONFIG__') return false;

            const sheetId = row.sheet_id;
            if (sheetId && this.recapSheetsMap) {
                const sheetObj = this.recapSheetsMap.get(Number(sheetId)) || this.recapSheetsMap.get(String(sheetId));
                if (sheetObj) {
                    const sheetName = String(sheetObj.name || '').toLowerCase();
                    const sheetType = String(sheetObj.sheet_type || '').toLowerCase();
                    if (sheetName.includes('config') || sheetType === 'config') {
                        return false;
                    }
                }
            }

            let parsedFormulas = row.formulas;
            if (typeof parsedFormulas === 'string') {
                try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
            }
            
            const hasSubtotalFormula = parsedFormulas && typeof parsedFormulas === 'object' && Object.values(parsedFormulas).some(v => typeof v === 'string' && v.includes('SUBTOTAL'));
            
            const namaLower = String(row.nama || '').toLowerCase().trim();
            const pengirimLower = String(row.pengirim || '').toLowerCase().trim();
            const awbLower = String(row.awb || row.awb_sistem || '').toLowerCase().trim();
            const tglLower = String(row.tanggal_pickup || '').toLowerCase().trim();
            
            // Only exclude actual subtotal rows (exactly 'total', 'subtotal', 'grand total', or starting with them)
            // This prevents false positives on legitimate company names like 'Total Logistics' or 'Total Cargo'
            const isSubtotalText = 
                namaLower === 'total' || namaLower === 'subtotal' || namaLower === 'grand total' || namaLower === 'grandtotal' ||
                namaLower.startsWith('total ') || namaLower.startsWith('subtotal ') || namaLower.startsWith('grand total ') ||
                pengirimLower === 'total' || pengirimLower === 'subtotal' || pengirimLower === 'grand total' ||
                pengirimLower.startsWith('total ') || pengirimLower.startsWith('subtotal ');

            // Check if this row is completely empty of identifying transaction details, which indicates it's a summary/subtotal row or empty row
            const isEmptyIdentity = 
                (!row.nama || namaLower === '' || namaLower === '—' || namaLower === '-') &&
                (!row.tanggal_pickup || tglLower === '' || tglLower === '—' || tglLower === '-') &&
                (!row.pengirim || pengirimLower === '' || pengirimLower === '—' || pengirimLower === '-') &&
                (!row.awb && !row.awb_sistem || awbLower === '' || awbLower === '—' || awbLower === '-');
            
            return !(hasSubtotalFormula || isSubtotalText || isEmptyIdentity);
        });
        const afterSubtotalCount = filtered.length;

        // 2. Filter by year resolved dynamically
        let afterYearCount = afterSubtotalCount;
        if (selectedYearVal !== 'all') {
            const y = parseInt(selectedYearVal);
            filtered = filtered.filter(row => {
                const yearNum = this._getRowYear(row);
                return yearNum === y;
            });
            afterYearCount = filtered.length;
        }
        
        // 3. Filter by month resolved dynamically
        let afterMonthCount = afterYearCount;
        if (selectedMonth !== 'all') {
            const m = parseInt(selectedMonth);
            filtered = filtered.filter(row => {
                const monthNum = this._getRowMonth(row);
                return monthNum === m;
            });
            afterMonthCount = filtered.length;
        }
        
        // 3. Filter by search query
        let afterSearchCount = afterMonthCount;
        if (query) {
            filtered = filtered.filter(row => {
                return Object.entries(row).some(([key, val]) => {
                    if (key === 'id' || key === 'formulas') return false;
                    return String(val).toLowerCase().includes(query);
                });
            });
            afterSearchCount = filtered.length;
        }

        // 4. Filter by standard advanced options (perusahaan, sales, service, revenue range, date range)
        if (this.advFilters) {
            // Filter by Perusahaan
            if (this.advFilters.perusahaan && this.advFilters.perusahaan !== 'all') {
                const p = this.advFilters.perusahaan.trim().toLowerCase();
                filtered = filtered.filter(row => String(row.nama || '').trim().toLowerCase() === p);
            }
            // Filter by Customer (Pengirim)
            if (this.advFilters.customer && this.advFilters.customer !== 'all') {
                const c = this.advFilters.customer.trim().toLowerCase();
                filtered = filtered.filter(row => String(row.pengirim || '').trim().toLowerCase() === c);
            }
            // Filter by Sales
            if (this.advFilters.sales && this.advFilters.sales !== 'all') {
                const s = this.advFilters.sales.trim().toLowerCase();
                filtered = filtered.filter(row => String(row.sales || '').trim().toLowerCase() === s);
            }
            // Filter by Service
            if (this.advFilters.service && this.advFilters.service !== 'all') {
                const svc = this.advFilters.service.trim().toLowerCase();
                filtered = filtered.filter(row => String(row.service || '').trim().toLowerCase() === svc);
            }
            // Filter by Min Revenue
            if (this.advFilters.minRevenue !== '' && this.advFilters.minRevenue !== null) {
                const minRev = parseFloat(this.advFilters.minRevenue);
                if (!isNaN(minRev)) {
                    filtered = filtered.filter(row => this._parseLocaleFloat(row.penjualan) >= minRev);
                }
            }
            // Filter by Max Revenue
            if (this.advFilters.maxRevenue !== '' && this.advFilters.maxRevenue !== null) {
                const maxRev = parseFloat(this.advFilters.maxRevenue);
                if (!isNaN(maxRev)) {
                    filtered = filtered.filter(row => this._parseLocaleFloat(row.penjualan) <= maxRev);
                }
            }
            // Filter by Start Date (Pickup)
            if (this.advFilters.startDate) {
                const start = window.formulaEngine ? window.formulaEngine._parseDate(this.advFilters.startDate) : new Date(this.advFilters.startDate);
                if (start && !isNaN(start.getTime())) {
                    start.setHours(0, 0, 0, 0);
                    filtered = filtered.filter(row => {
                        const rowDate = window.formulaEngine ? window.formulaEngine._parseDate(row.tanggal_pickup) : null;
                        if (!rowDate) return false;
                        rowDate.setHours(0, 0, 0, 0);
                        return rowDate >= start;
                    });
                }
            }
            // Filter by End Date (Pickup)
            if (this.advFilters.endDate) {
                const end = window.formulaEngine ? window.formulaEngine._parseDate(this.advFilters.endDate) : new Date(this.advFilters.endDate);
                if (end && !isNaN(end.getTime())) {
                    end.setHours(23, 59, 59, 999);
                    filtered = filtered.filter(row => {
                        const rowDate = window.formulaEngine ? window.formulaEngine._parseDate(row.tanggal_pickup) : null;
                        if (!rowDate) return false;
                        rowDate.setHours(0, 0, 0, 0);
                        return rowDate <= end;
                    });
                }
            }
        }
        
        // 5. Apply sorting (Ascending / Descending)
        const sortFieldSelect = document.getElementById('recapSortField');
        const sortOrderSelect = document.getElementById('recapSortOrder');
        const sortField = sortFieldSelect ? sortFieldSelect.value : 'tanggal_pickup';
        const sortOrder = sortOrderSelect ? sortOrderSelect.value : 'desc';

        filtered.sort((a, b) => {
            let valA, valB;

            if (sortField === 'tanggal_pickup') {
                const dateA = window.formulaEngine ? window.formulaEngine._parseDate(a.tanggal_pickup) : new Date(a.tanggal_pickup);
                const dateB = window.formulaEngine ? window.formulaEngine._parseDate(b.tanggal_pickup) : new Date(b.tanggal_pickup);
                valA = dateA && !isNaN(dateA.getTime()) ? dateA.getTime() : 0;
                valB = dateB && !isNaN(dateB.getTime()) ? dateB.getTime() : 0;
            } else if (sortField === 'penjualan' || sortField === 'profit') {
                valA = this._parseLocaleFloat(a[sortField]);
                valB = this._parseLocaleFloat(b[sortField]);
            } else {
                valA = String(a[sortField] || '').toLowerCase();
                valB = String(b[sortField] || '').toLowerCase();
            }

            if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
            if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
            
            // Fallback stable sort matching worksheet (by ID/insertion order)
            const idA = parseInt(a.id) || 0;
            const idB = parseInt(b.id) || 0;
            return sortOrder === 'asc' ? (idA - idB) : (idB - idA);
        });

        this.filteredData = filtered;
        
        // Debug mode disabled

        const countDisplay = document.getElementById('recapRowsCount');
        if (countDisplay) countDisplay.textContent = filtered.length;
        
        this.renderTable();
    }

    renderTable() {
        const thead = document.getElementById('recapTableHead');
        const tbody = document.getElementById('recapTableBody');
        if (!thead || !tbody) return;

        const fmt = (v) => window.Formatter ? window.Formatter.currency(v) : new Intl.NumberFormat('en-US').format(v);

        // Hide legacy top KPI bar if it is present
        const kpisBar = document.getElementById('recapKpisBar');
        if (kpisBar) kpisBar.innerHTML = '';

        if (this.activeTab === 'revenue') {
            // Force strict pixel alignments using !important to resolve the misalignment bug
            thead.innerHTML = `
                <tr>
                    <th style="width: 60px; text-align: center !important; background: var(--red); color: white;">NO</th>
                    <th style="text-align: center !important; background: var(--red); color: white;">TANGGAL PICKUP</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">PERUSAHAAN</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">NO AWB</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">NAMA CUSTOMER</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">SALES</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">SERVICE</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">REVENUE</th>
                </tr>
            `;

            if (this.filteredData.length === 0) {
                const dbCount = this._lastDbCount || 0;
                const liveCount = this._lastLiveCount || 0;
                const rawCount = this._lastRawCount || 0;
                const cleanCount = this._lastCleanCount || 0;
                tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 60px; color: var(--text-muted); font-weight: 600; text-align: center;">
                    <i class="fas fa-search" style="font-size: 2rem; display: block; margin-bottom: 10px; text-align: center; width: 100%;"></i> 
                    Belum ada data penjualan ditemukan.<br>
                    <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 400; margin-top: 8px; display: inline-block; background: rgba(0,0,0,0.03); padding: 4px 10px; border-radius: 6px; border: 1px dashed var(--border-light);">
                        Diagnostics: DB Data: ${dbCount} | Live Data: ${liveCount} | Raw: ${rawCount} | Clean: ${cleanCount}
                    </span>
                </td></tr>`;
                return;
            }

            let html = '';
            let totalRevenue = 0;

            this.filteredData.forEach((row, idx) => {
                const dateVal = this._formatDateDMY(row.tanggal_pickup);
                const namaVal = row.nama ? row.nama : '—';
                const awbVal = row.awb || row.awb_sistem || '—';
                const pengirimVal = row.pengirim ? row.pengirim : '—';
                const salesVal = row.sales ? row.sales : '—';
                const serviceVal = row.service ? row.service : '—';
                
                const rev = this._parseLocaleFloat(row.penjualan);
                
                totalRevenue += rev;

                html += `
                    <tr>
                        <td style="text-align: center; font-weight: 700; color: var(--red);">${idx + 1}</td>
                        <td style="text-align: center; color: var(--text-secondary);">${dateVal}</td>
                        <td style="font-weight: 700; color: #000; text-align: left;">${namaVal}</td>
                        <td style="font-weight: 600; color: var(--text-secondary); text-align: left;">${awbVal}</td>
                        <td style="font-weight: 600; color: var(--text-primary); text-align: left;">${pengirimVal}</td>
                        <td style="color: var(--text-secondary); text-align: left;">${salesVal}</td>
                        <td style="color: var(--text-secondary); text-align: left;">${serviceVal}</td>
                        <td style="text-align: right; font-weight: 700; color: #000;">${fmt(rev)}</td>
                    </tr>
                `;
            });

            // Aggregate Summary bottom row (replacing cards)
            html += `
                <tr style="background: rgba(204, 0, 0, 0.05); border-top: 2px solid var(--red);">
                    <td colspan="7" style="text-align: right; font-weight: 800; color: var(--text-primary); font-size: 0.85rem; padding: 14px 12px;">TOTAL REVENUE:</td>
                    <td style="text-align: right; font-weight: 900; color: #16a34a; font-size: 0.9rem; padding: 14px 12px;">${fmt(totalRevenue)}</td>
                </tr>
            `;

            tbody.innerHTML = html;

        } else if (this.activeTab === 'profit') {
            thead.innerHTML = `
                <tr>
                    <th style="width: 60px; text-align: center !important; background: var(--red); color: white;">NO</th>
                    <th style="text-align: center !important; background: var(--red); color: white;">TANGGAL PICKUP</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">PERUSAHAAN</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">NAMA CUSTOMER</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">REVENUE</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">TOTAL BIAYA</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">PROFIT</th>
                </tr>
            `;

            if (this.filteredData.length === 0) {
                const dbCount = this._lastDbCount || 0;
                const liveCount = this._lastLiveCount || 0;
                const rawCount = this._lastRawCount || 0;
                const cleanCount = this._lastCleanCount || 0;
                tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 60px; color: var(--text-muted); font-weight: 600; text-align: center;">
                    <i class="fas fa-search" style="font-size: 2rem; display: block; margin-bottom: 10px; text-align: center; width: 100%;"></i> 
                    Belum ada data profitabilitas ditemukan.<br>
                    <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 400; margin-top: 8px; display: inline-block; background: rgba(0,0,0,0.03); padding: 4px 10px; border-radius: 6px; border: 1px dashed var(--border-light);">
                        Diagnostics: DB Data: ${dbCount} | Live Data: ${liveCount} | Raw: ${rawCount} | Clean: ${cleanCount}
                    </span>
                </td></tr>`;
                return;
            }

            let html = '';
            let totalRevenue = 0;
            let totalCost = 0;
            let totalProfit = 0;

            this.filteredData.forEach((row, idx) => {
                const dateVal = this._formatDateDMY(row.tanggal_pickup);
                const namaVal = row.nama ? row.nama : '—';
                const pengirimVal = row.pengirim ? row.pengirim : '—';
                
                const rev = this._parseLocaleFloat(row.penjualan);
                const cost = this._parseLocaleFloat(row.total_biaya);
                const profit = this._parseLocaleFloat(row.profit);

                totalRevenue += rev;
                totalCost += cost;
                totalProfit += profit;

                const profitStyle = `color: ${profit >= 0 ? '#16a34a' : '#dc2626'}; font-weight: 700;`;

                html += `
                    <tr>
                        <td style="text-align: center; font-weight: 700; color: var(--red);">${idx + 1}</td>
                        <td style="text-align: center; color: var(--text-secondary);">${dateVal}</td>
                        <td style="font-weight: 700; color: #000; text-align: left;">${namaVal}</td>
                        <td style="font-weight: 600; color: var(--text-primary); text-align: left;">${pengirimVal}</td>
                        <td style="text-align: right; font-weight: 600; color: var(--text-primary);">${fmt(rev)}</td>
                        <td style="text-align: right; font-weight: 600; color: #ea580c;">${fmt(cost)}</td>
                        <td style="text-align: right; ${profitStyle}">${fmt(profit)}</td>
                    </tr>
                `;
            });

            const profitColor = totalProfit >= 0 ? '#16a34a' : '#dc2626';

            // Aggregate Summary bottom row (replacing cards)
            html += `
                <tr style="background: rgba(204, 0, 0, 0.05); border-top: 2px solid var(--red);">
                    <td colspan="4" style="text-align: right; font-weight: 800; color: var(--text-primary); font-size: 0.85rem; padding: 14px 12px;">GRAND TOTAL:</td>
                    <td style="text-align: right; font-weight: 800; color: var(--text-primary); font-size: 0.85rem; padding: 14px 12px;">${fmt(totalRevenue)}</td>
                    <td style="text-align: right; font-weight: 800; color: #ea580c; font-size: 0.85rem; padding: 14px 12px;">${fmt(totalCost)}</td>
                    <td style="text-align: right; font-weight: 900; color: ${profitColor}; font-size: 0.9rem; padding: 14px 12px;">${fmt(totalProfit)}</td>
                </tr>
            `;

            tbody.innerHTML = html;

        } else if (this.activeTab === 'customer') {
            thead.innerHTML = `
                <tr>
                    <th style="width: 60px; text-align: center !important; background: var(--red); color: white;">NO</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">NAMA CUSTOMER</th>
                    <th style="text-align: center !important; background: var(--red); color: white;">JUMLAH POD</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">TOTAL REVENUE</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">TOTAL PROFIT</th>
                </tr>
            `;

            // Aggregate data by Customer Name
            const agg = {};
            this.filteredData.forEach(row => {
                const customer = (row.pengirim || '—').trim();
                
                if (!agg[customer]) {
                    agg[customer] = {
                        name: customer,
                        pods: 0,
                        revenue: 0,
                        profit: 0
                    };
                }
                agg[customer].pods++;
                
                const rev = this._parseLocaleFloat(row.penjualan);
                const profit = this._parseLocaleFloat(row.profit);
                
                agg[customer].revenue += rev;
                agg[customer].profit += profit;
            });

            // Sort customer aggregation descending by total revenue
            const sortedCusts = Object.values(agg).sort((a, b) => b.revenue - a.revenue);

            if (sortedCusts.length === 0) {
                const dbCount = this._lastDbCount || 0;
                const liveCount = this._lastLiveCount || 0;
                const rawCount = this._lastRawCount || 0;
                const cleanCount = this._lastCleanCount || 0;
                tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 60px; color: var(--text-muted); font-weight: 600; text-align: center;">
                    <i class="fas fa-search" style="font-size: 2rem; display: block; margin-bottom: 10px; text-align: center; width: 100%;"></i> 
                    Belum ada data customer terakumulasi.<br>
                    <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 400; margin-top: 8px; display: inline-block; background: rgba(0,0,0,0.03); padding: 4px 10px; border-radius: 6px; border: 1px dashed var(--border-light);">
                        Diagnostics: DB Data: ${dbCount} | Live Data: ${liveCount} | Raw: ${rawCount} | Clean: ${cleanCount}
                    </span>
                </td></tr>`;
                return;
            }

            let html = '';
            let totalPods = 0;
            let grandRevenue = 0;
            let grandProfit = 0;

            sortedCusts.forEach((c, idx) => {
                totalPods += c.pods;
                grandRevenue += c.revenue;
                grandProfit += c.profit;

                const profitStyle = `color: ${c.profit >= 0 ? '#16a34a' : '#dc2626'}; font-weight: 700;`;

                html += `
                    <tr>
                        <td style="text-align: center; font-weight: 700; color: var(--red);">${idx + 1}</td>
                        <td style="font-weight: 700; color: var(--text-primary); text-align: left;">${c.name}</td>
                        <td style="text-align: center; font-weight: 700; color: var(--text-secondary);">${c.pods}</td>
                        <td style="text-align: right; font-weight: 700; color: #000;">${fmt(c.revenue)}</td>
                        <td style="text-align: right; ${profitStyle}">${fmt(c.profit)}</td>
                    </tr>
                `;
            });

            const profitColor = grandProfit >= 0 ? '#16a34a' : '#dc2626';

            // Aggregate Summary bottom row (replacing cards)
            html += `
                <tr style="background: rgba(204, 0, 0, 0.05); border-top: 2px solid var(--red);">
                    <td colspan="2" style="text-align: right; font-weight: 800; color: var(--text-primary); font-size: 0.85rem; padding: 14px 12px;">GRAND TOTAL:</td>
                    <td style="text-align: center; font-weight: 800; color: var(--text-secondary); font-size: 0.85rem; padding: 14px 12px;">${totalPods} POD</td>
                    <td style="text-align: right; font-weight: 800; color: #000; font-size: 0.85rem; padding: 14px 12px;">${fmt(grandRevenue)}</td>
                    <td style="text-align: right; font-weight: 900; color: ${profitColor}; font-size: 0.9rem; padding: 14px 12px;">${fmt(grandProfit)}</td>
                </tr>
            `;

            tbody.innerHTML = html;
        } else if (this.activeTab === 'insurance') {
            thead.innerHTML = `
                <tr>
                    <th style="width: 60px; text-align: center !important; background: var(--red); color: white;">NO</th>
                    <th style="text-align: center !important; background: var(--red); color: white;">TANGGAL PICKUP</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">PERUSAHAAN</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">NAMA CUSTOMER</th>
                    <th style="text-align: left !important; background: var(--red); color: white;">NO AWB</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">NILAI BARANG</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">PENJUALAN ASURANSI</th>
                    <th style="text-align: right !important; background: var(--red); color: white;">MODAL ASURANSI</th>
                </tr>
            `;

            if (this.filteredData.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 60px; color: var(--text-muted); font-weight: 600; text-align: center;">
                    <i class="fas fa-search" style="font-size: 2rem; display: block; margin-bottom: 10px; text-align: center; width: 100%;"></i> 
                    Belum ada data asuransi ditemukan.
                </td></tr>`;
                return;
            }

            let html = '';
            let totalNilaiBarang = 0;
            let totalAsuransi = 0;
            let totalJasindo = 0;

            this.filteredData.forEach((row, idx) => {
                const dateVal = this._formatDateDMY(row.tanggal_pickup);
                const namaVal = row.nama ? row.nama : '—';
                const pengirimVal = row.pengirim ? row.pengirim : '—';
                const awbVal = row.awb || row.awb_sistem || '—';
                
                const nb = this._parseLocaleFloat(row.nilai_barang);
                const asuransi = this._parseLocaleFloat(row.asuransi);
                const jasindo = this._parseLocaleFloat(row.asuransi_jasindo);

                totalNilaiBarang += nb;
                totalAsuransi += asuransi;
                totalJasindo += jasindo;

                html += `
                    <tr>
                        <td style="text-align: center; font-weight: 700; color: var(--red);">${idx + 1}</td>
                        <td style="text-align: center; color: var(--text-secondary);">${dateVal}</td>
                        <td style="font-weight: 700; color: #000; text-align: left;">${namaVal}</td>
                        <td style="font-weight: 600; color: var(--text-primary); text-align: left;">${pengirimVal}</td>
                        <td style="color: var(--text-secondary); text-align: left;">${awbVal}</td>
                        <td style="text-align: right; font-weight: 600; color: var(--text-primary);">${fmt(nb)}</td>
                        <td style="text-align: right; font-weight: 600; color: #ea580c;">${fmt(asuransi)}</td>
                        <td style="text-align: right; font-weight: 600; color: #16a34a;">${fmt(jasindo)}</td>
                    </tr>
                `;
            });

            html += `
                <tr style="background: rgba(204, 0, 0, 0.05); border-top: 2px solid var(--red);">
                    <td colspan="5" style="text-align: right; font-weight: 800; color: var(--text-primary); font-size: 0.85rem; padding: 14px 12px;">GRAND TOTAL:</td>
                    <td style="text-align: right; font-weight: 800; color: var(--text-primary); font-size: 0.85rem; padding: 14px 12px;">${fmt(totalNilaiBarang)}</td>
                    <td style="text-align: right; font-weight: 800; color: #ea580c; font-size: 0.85rem; padding: 14px 12px;">${fmt(totalAsuransi)}</td>
                    <td style="text-align: right; font-weight: 900; color: #16a34a; font-size: 0.9rem; padding: 14px 12px;">${fmt(totalJasindo)}</td>
                </tr>
            `;

            tbody.innerHTML = html;
        }
    }

    populateAdvFilterOptions() {
        const selectPerusahaan = document.getElementById('recapAdvFilterPerusahaan');
        const selectSales = document.getElementById('recapAdvFilterSales');
        const selectService = document.getElementById('recapAdvFilterService');
        
        const selectCustomer = document.getElementById('recapAdvFilterCustomer');
        
        if (!this.cleanData) return;
        
        // 1a. Perusahaan options
        if (selectPerusahaan) {
            const currentSelected = selectPerusahaan.value || 'all';
            const uniquePerusahaan = new Set();
            this.cleanData.forEach(row => {
                if (row.nama) {
                    const name = String(row.nama).trim();
                    if (name && name !== '—' && name !== '-') uniquePerusahaan.add(name);
                }
            });
            const sorted = Array.from(uniquePerusahaan).sort();
            let html = '<option value="all">Semua Perusahaan</option>';
            sorted.forEach(p => {
                html += `<option value="${p}">${p}</option>`;
            });
            selectPerusahaan.innerHTML = html;
            selectPerusahaan.value = uniquePerusahaan.has(currentSelected) ? currentSelected : 'all';
        }

        // 1b. Customer options
        if (selectCustomer) {
            const currentSelected = selectCustomer.value || 'all';
            const uniqueCustomer = new Set();
            this.cleanData.forEach(row => {
                if (row.pengirim) {
                    const pengirim = String(row.pengirim).trim();
                    if (pengirim && pengirim !== '—' && pengirim !== '-') uniqueCustomer.add(pengirim);
                }
            });
            const sorted = Array.from(uniqueCustomer).sort();
            let html = '<option value="all">Semua Customer</option>';
            sorted.forEach(p => {
                html += `<option value="${p}">${p}</option>`;
            });
            selectCustomer.innerHTML = html;
            selectCustomer.value = uniqueCustomer.has(currentSelected) ? currentSelected : 'all';
        }
        
        // 2. Sales options
        if (selectSales) {
            const currentSelected = selectSales.value || 'all';
            const uniqueSales = new Set();
            this.cleanData.forEach(row => {
                if (row.sales) {
                    const s = String(row.sales).trim();
                    if (s && s !== '—' && s !== '-') uniqueSales.add(s);
                }
            });
            const sorted = Array.from(uniqueSales).sort();
            let html = '<option value="all">Semua Sales</option>';
            sorted.forEach(s => {
                html += `<option value="${s}">${s}</option>`;
            });
            selectSales.innerHTML = html;
            selectSales.value = uniqueSales.has(currentSelected) ? currentSelected : 'all';
        }
        
        // 3. Service options
        if (selectService) {
            const currentSelected = selectService.value || 'all';
            const uniqueService = new Set();
            this.cleanData.forEach(row => {
                if (row.service) {
                    const svc = String(row.service).trim();
                    if (svc && svc !== '—' && svc !== '-') uniqueService.add(svc);
                }
            });
            const sorted = Array.from(uniqueService).sort();
            let html = '<option value="all">Semua Service</option>';
            sorted.forEach(svc => {
                html += `<option value="${svc}">${svc}</option>`;
            });
            selectService.innerHTML = html;
            selectService.value = uniqueService.has(currentSelected) ? currentSelected : 'all';
        }
    }

    toggleAdvFilter(forceClose = false) {
        const popover = document.getElementById('recapFilterPopover');
        if (!popover) return;
        
        if (forceClose) {
            popover.style.display = 'none';
            return;
        }
        
        const isHidden = popover.style.display === 'none';
        popover.style.display = isHidden ? 'flex' : 'none';
        
        if (isHidden) {
            const closeHandler = (e) => {
                const container = document.getElementById('recapFilterContainer');
                if (container && !container.contains(e.target)) {
                    popover.style.display = 'none';
                    document.removeEventListener('click', closeHandler);
                }
            };
            setTimeout(() => {
                document.addEventListener('click', closeHandler);
            }, 50);
        }
    }

    applyAdvFilters() {
        const selectPerusahaan = document.getElementById('recapAdvFilterPerusahaan');
        const selectCustomer = document.getElementById('recapAdvFilterCustomer');
        const selectSales = document.getElementById('recapAdvFilterSales');
        const selectService = document.getElementById('recapAdvFilterService');
        const inputMinRev = document.getElementById('recapAdvFilterMinRev');
        const inputMaxRev = document.getElementById('recapAdvFilterMaxRev');
        const inputStartDate = document.getElementById('recapAdvFilterStartDate');
        const inputEndDate = document.getElementById('recapAdvFilterEndDate');
        
        this.advFilters = {
            perusahaan: selectPerusahaan ? selectPerusahaan.value : 'all',
            customer: selectCustomer ? selectCustomer.value : 'all',
            sales: selectSales ? selectSales.value : 'all',
            service: selectService ? selectService.value : 'all',
            minRevenue: inputMinRev ? inputMinRev.value.trim() : '',
            maxRevenue: inputMaxRev ? inputMaxRev.value.trim() : '',
            startDate: inputStartDate ? inputStartDate.value.trim() : '',
            endDate: inputEndDate ? inputEndDate.value.trim() : ''
        };
        
        const advBtn = document.getElementById('recapFilterAdvBtn');
        const hasActiveFilter = 
            this.advFilters.perusahaan !== 'all' || 
            this.advFilters.customer !== 'all' || 
            this.advFilters.sales !== 'all' || 
            this.advFilters.service !== 'all' || 
            this.advFilters.minRevenue !== '' || 
            this.advFilters.maxRevenue !== '' ||
            this.advFilters.startDate !== '' ||
            this.advFilters.endDate !== '';
            
        if (advBtn) {
            if (hasActiveFilter) {
                advBtn.classList.add('active');
                advBtn.innerHTML = '<i class="fas fa-filter"></i> Filter (Aktif)';
                advBtn.style.borderColor = 'var(--red)';
                advBtn.style.color = 'var(--red)';
                advBtn.style.background = 'rgba(204, 0, 0, 0.08)';
            } else {
                advBtn.classList.remove('active');
                advBtn.innerHTML = '<i class="fas fa-filter"></i> Filter';
                advBtn.style.borderColor = 'var(--border-color)';
                advBtn.style.color = 'var(--text-primary)';
                advBtn.style.background = 'white';
            }
        }
        
        this.filterData();
        this.toggleAdvFilter(true);
    }

    clearAdvFilters() {
        const selectPerusahaan = document.getElementById('recapAdvFilterPerusahaan');
        const selectCustomer = document.getElementById('recapAdvFilterCustomer');
        const selectSales = document.getElementById('recapAdvFilterSales');
        const selectService = document.getElementById('recapAdvFilterService');
        const inputMinRev = document.getElementById('recapAdvFilterMinRev');
        const inputMaxRev = document.getElementById('recapAdvFilterMaxRev');
        const inputStartDate = document.getElementById('recapAdvFilterStartDate');
        const inputEndDate = document.getElementById('recapAdvFilterEndDate');
        
        if (selectPerusahaan) selectPerusahaan.value = 'all';
        if (selectCustomer) selectCustomer.value = 'all';
        if (selectSales) selectSales.value = 'all';
        if (selectService) selectService.value = 'all';
        if (inputMinRev) inputMinRev.value = '';
        if (inputMaxRev) inputMaxRev.value = '';
        if (inputStartDate) inputStartDate.value = '';
        if (inputEndDate) inputEndDate.value = '';
        
        this.advFilters = {
            perusahaan: 'all',
            customer: 'all',
            sales: 'all',
            service: 'all',
            minRevenue: '',
            maxRevenue: '',
            startDate: '',
            endDate: ''
        };
        
        const advBtn = document.getElementById('recapFilterAdvBtn');
        if (advBtn) {
            advBtn.classList.remove('active');
            advBtn.innerHTML = '<i class="fas fa-filter"></i> Filter';
            advBtn.style.borderColor = 'var(--border-color)';
            advBtn.style.color = 'var(--text-primary)';
            advBtn.style.background = 'white';
        }
        
        this.filterData();
        this.toggleAdvFilter(true);
    }
}

const recapPageManager = new RecapPageManager();
window.recapPageManager = recapPageManager;
