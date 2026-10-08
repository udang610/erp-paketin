/**
 * FORMULA ENGINE v2.2 (Google Sheets Style)
 * Advanced parser for spreadsheet-like formulas with dependency tracking
 */
class FormulaEngine {
    constructor() {
        this.dependencyGraph = new Map(); // cellId -> Set of dependent cellIds
        this.formulas = new Map(); // cellId -> raw formula string
        this.cellErrors = new Map(); // cellId -> error string

        // Mapping columns to fields based on Paketin Finance V2 structure
        this.colToField = [
            null, // 0 index
            'tanggal_pickup', 'nama', 'awb', 'awb_sistem', 'pengirim', 'sales', 'penerima', 'service', 'via',
            'aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil', 'harga', 'surcharge', 'packing', 'handling',
            'penjualan', 'asal_pickup', 'jenis_barang', 'tujuan', 'nama_vendor', 'nama_vendor_ii', 'nama_vendor_iii',
            'nama_vendor_iv', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops', 'total_biaya', 'profit',
            'idx_profit', 'asuransi', 'nilai_barang', 'asuransi_jasindo'
        ];

        this.fieldToCol = {};
        this.colToField.forEach((f, i) => { if (f) this.fieldToCol[f] = i; });

        this.functions = {
            'SUM': (...args) => args.reduce((a, b) => a + (parseFloat(b) || 0), 0),
            'AVG': (...args) => args.length ? args.reduce((a, b) => a + (parseFloat(b) || 0), 0) / args.length : 0,
            'AVERAGE': (...args) => args.length ? args.reduce((a, b) => a + (parseFloat(b) || 0), 0) / args.length : 0,
            'MIN': (...args) => Math.min(...args.map(v => parseFloat(v) || 0)),
            'MAX': (...args) => Math.max(...args.map(v => parseFloat(v) || 0)),
            'COUNT': (...args) => args.length,
            'COUNTA': (...args) => args.filter(a => a !== null && a !== undefined && a !== '').length,
            'PRODUCT': (...args) => args.reduce((a, b) => a * (parseFloat(b) || 0), 1),
            'ABS': (v) => Math.abs(parseFloat(v) || 0),
            'ROUND': (v, p) => {
                const val = parseFloat(v) || 0;
                const precision = parseInt(p) || 0;
                return Number(Math.round(val + 'e' + precision) + 'e-' + precision);
            },
            'IFERROR': (v, fallback) => {
                if (v === '#ERROR' || v === '#VALUE!' || v === '#CIRCULAR' || isNaN(v)) return fallback;
                return v;
            },
            'SUBTOTAL': (fnNum, ...args) => {
                const n = parseInt(fnNum);
                switch (n) {
                    case 1: case 101: return this.functions.AVERAGE(...args);
                    case 2: case 102: return this.functions.COUNT(...args);
                    case 3: case 103: return this.functions.COUNTA(...args);
                    case 4: case 104: return this.functions.MAX(...args);
                    case 5: case 105: return this.functions.MIN(...args);
                    case 6: case 106: return this.functions.PRODUCT(...args);
                    case 9: case 109: return this.functions.SUM(...args);
                    default: return 0;
                }
            },
            'IF': (cond, t, f) => (cond ? t : f),
            'AND': (...args) => args.every(v => !!v),
            'OR': (...args) => args.some(v => !!v),
            'NOT': (v) => !v
        };

        this.functionMetadata = {
            'SUM': { desc: 'Menjumlahkan semua angka dalam rentang sel.', syntax: 'SUM(nilai1, [nilai2, ...])', example: 'SUM(A1:A10)' },
            'AVG': { desc: 'Menghitung rata-rata dari sekelompok angka.', syntax: 'AVG(nilai1, [nilai2, ...])', example: 'AVG(B1:B5)' },
            'AVERAGE': { desc: 'Menghitung rata-rata dari sekelompok angka.', syntax: 'AVERAGE(nilai1, [nilai2, ...])', example: 'AVERAGE(B1:B5)' },
            'MIN': { desc: 'Mencari nilai terkecil dalam sekelompok data.', syntax: 'MIN(nilai1, [nilai2, ...])', example: 'MIN(C1:C20)' },
            'MAX': { desc: 'Mencari nilai terbesar dalam sekelompok data.', syntax: 'MAX(nilai1, [nilai2, ...])', example: 'MAX(C1:C20)' },
            'COUNT': { desc: 'Menghitung jumlah sel yang berisi angka.', syntax: 'COUNT(nilai1, [nilai2, ...])', example: 'COUNT(A1:A50)' },
            'COUNTA': { desc: 'Menghitung jumlah sel yang tidak kosong.', syntax: 'COUNTA(nilai1, [nilai2, ...])', example: 'COUNTA(A1:A50)' },
            'PRODUCT': { desc: 'Mengalikan semua angka yang diberikan sebagai argumen.', syntax: 'PRODUCT(nilai1, [nilai2, ...])', example: 'PRODUCT(A1, A2, 5)' },
            'ABS': { desc: 'Menghasilkan nilai mutlak dari sebuah angka.', syntax: 'ABS(angka)', example: 'ABS(-10)' },
            'ROUND': { desc: 'Membulatkan angka ke jumlah digit tertentu.', syntax: 'ROUND(angka, [digit])', example: 'ROUND(3.14159, 2)' },
            'IF': { desc: 'Menjalankan tes logika dan menghasilkan satu nilai jika benar, dan nilai lain jika salah.', syntax: 'IF(tes_logika, nilai_jika_benar, nilai_jika_salah)', example: 'IF(A1>100, "Bonus", "No")' },
            'IFERROR': { desc: 'Menghasilkan nilai kustom jika rumus menghasilkan error, jika tidak menghasilkan nilai rumus itu sendiri.', syntax: 'IFERROR(nilai, nilai_jika_error)', example: 'IFERROR(A1/B1, 0)' },
            'SUBTOTAL': { desc: 'Menghasilkan subtotal dalam daftar atau database.', syntax: 'SUBTOTAL(angka_fungsi, rentang1, [rentang2, ...])', example: 'SUBTOTAL(9, A1:A10)' },
            'AND': { desc: 'Menghasilkan TRUE jika semua argumen bernilai benar.', syntax: 'AND(logika1, [logika2, ...])', example: 'AND(A1>10, B1<5)' },
            'OR': { desc: 'Menghasilkan TRUE jika salah satu argumen bernilai benar.', syntax: 'OR(logika1, [logika2, ...])', example: 'OR(A1>10, B1<5)' },
            'NOT': { desc: 'Membalikkan nilai logika argumennya.', syntax: 'NOT(logika)', example: 'NOT(A1=10)' }
        };
    }

    /**
     * Parse and compute a formula for a specific cell
     * @param {string} formulaStr - e.g. "=A1+B1"
     * @param {string} rowId - row uuid
     * @param {string} field - column key
     * @returns {any} computed value or error string
     */
    evaluate(formulaStr, rowId, field) {
        if (!formulaStr || !formulaStr.startsWith('=')) return formulaStr;

        const cellId = `${rowId}:${field}`;
        const expression = formulaStr.substring(1).toUpperCase();

        try {
            // Check for circular reference before computing
            const visited = new Set();
            if (this._hasCircularReference(cellId, expression, visited)) {
                this.cellErrors.set(cellId, '#CIRCULAR');
                return '#CIRCULAR';
            }

            // Extract dependencies and register them
            const deps = this.extractDependencies(expression);
            this._registerDependencies(cellId, deps);
            this.formulas.set(cellId, formulaStr);

            // Compute value
            const result = this._computeExpression(expression);
            this.cellErrors.delete(cellId);
            return result;
        } catch (e) {
            console.error('Formula Error:', e);
            this.cellErrors.set(cellId, '#ERROR');
            return '#ERROR';
        }
    }

    unregisterFormula(rowId, field) {
        const cellId = `${rowId}:${field}`;
        this.formulas.delete(cellId);
        this.cellErrors.delete(cellId);
        for (const [depA1, cellIds] of this.dependencyGraph.entries()) {
            if (cellIds.has(cellId)) {
                cellIds.delete(cellId);
                if (cellIds.size === 0) {
                    this.dependencyGraph.delete(depA1);
                }
            }
        }
    }

    compute(name, data, options = {}) {
        const template = options.template;
        const rowLogic = {
            'penjualan': (r) => {
                const harga = this._getCellValueByA1_Logic(r.harga);
                const aktual = this._getCellValueByA1_Logic(r.aktual);
                const vol = this._getCellValueByA1_Logic(r.vol);
                const surcharge = this._getCellValueByA1_Logic(r.surcharge);
                const packing = this._getCellValueByA1_Logic(r.packing);
                const handling = this._getCellValueByA1_Logic(r.handling);

                if (template === 'double_charge') {
                    return (harga * aktual) + (harga * vol) + surcharge + packing + handling;
                } else if (template === 'actual_only') {
                    return (harga * aktual) + surcharge + packing + handling;
                } else if (template === 'volume_only') {
                    return (harga * vol) + surcharge + packing + handling;
                } else {
                    // standard_cargo (default)
                    const beratChargeable = Math.max(aktual, vol);
                    return (harga * beratChargeable) + surcharge + packing + handling;
                }
            },
            'total_biaya': (r) => {
                return this._getCellValueByA1_Logic(r.vendor_i) +
                    this._getCellValueByA1_Logic(r.vendor_ii) +
                    this._getCellValueByA1_Logic(r.vendor_iii) +
                    this._getCellValueByA1_Logic(r.vendor_iv) +
                    this._getCellValueByA1_Logic(r.ops);
            },
            'total_vendor': (r) => rowLogic.total_biaya(r),
            'asuransi': (r) => {
                if (template === 'nilai_barang_none') return 0;
                return this._getCellValueByA1_Logic(r.nilai_barang) * 0.002;
            },
            'asuransi_jasindo': (r) => {
                if (template === 'nilai_barang_none') return 0;
                return this._getCellValueByA1_Logic(r.nilai_barang) * 0.001;
            },
            'profit': (r) => {
                // Fetch direct cell values to support manual overrides and respect manual settings
                const rev = this._getCellValueByA1_Logic(r.penjualan);
                const cost = this._getCellValueByA1_Logic(r.total_biaya);
                return rev - cost;
            },
            'margin_percent': (r) => {
                const rev = this._getCellValueByA1_Logic(r.penjualan);
                const prof = this._getCellValueByA1_Logic(r.profit);
                return rev === 0 ? 0 : (prof / rev);
            }
        };

        if (name === 'monthly_summary' || name === 'yearly_summary') {
            const { year, month } = options;

            let totalRevenue = 0, totalProfit = 0, totalCost = 0, count = 0;
            let floatingRevenue = 0, floatingProfit = 0, floatingCost = 0, floatingCount = 0;

            data.forEach(r => {
                const rev = this._getCellValueByA1_Logic(r.penjualan);
                const cost = this._getCellValueByA1_Logic(r.total_biaya);

                // Sum stored database profit directly to respect manual values and user expectation
                let prof = this._getCellValueByA1_Logic(r.profit);
                if (r.formulas && r.formulas.profit === ' ') {
                    if (r.profit === null || r.profit === undefined || r.profit === '' || r.profit === 0) {
                        prof = 0;
                    }
                }

                if (!r.tanggal_pickup) {
                    floatingRevenue += rev;
                    floatingCost += cost;
                    floatingProfit += prof;
                    floatingCount++;
                    return;
                }

                const d = this._parseDate(r.tanggal_pickup);
                if (!d) {
                    floatingRevenue += rev;
                    floatingCost += cost;
                    floatingProfit += prof;
                    floatingCount++;
                    return;
                }

                const matchYear = d.getFullYear() === year;
                const matchMonth = name === 'monthly_summary' ? (d.getMonth() + 1) === month : true;

                if (matchYear && matchMonth) {
                    totalRevenue += rev;
                    totalCost += cost;
                    totalProfit += prof;
                    count++;
                } else if (matchYear) {
                    // if it matches year but not month, we don't count it as floating either.
                }
            });

            return {
                totalRevenue, totalProfit, totalCost, count,
                avgMargin: totalRevenue === 0 ? 0 : (totalProfit / totalRevenue),
                floating: {
                    revenue: floatingRevenue,
                    profit: floatingProfit,
                    count: floatingCount
                }
            };
        }

        if (rowLogic[name]) return rowLogic[name](data);
        return 0;
    }

    _parseDate(v) {
        if (!v) return null;
        if (v instanceof Date) return v;

        // Handle DD/MM/YYYY explicitly first to avoid JS Date confusing it with MM/DD/YYYY
        if (typeof v === 'string') {
            const parts = v.trim().split(/[-/]/);
            if (parts.length === 3) {
                // If year is first: YYYY-MM-DD
                if (parts[0].length === 4) {
                    return new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
                }
                // If year is last: DD-MM-YYYY or DD/MM/YY
                let year = parseInt(parts[2]);
                if (parts[2].length === 2) {
                    year += 2000; // Assume 2000+ for 2-digit years
                }
                return new Date(year, parseInt(parts[1]) - 1, parseInt(parts[0]));
            }
        }

        const d = new Date(v);
        if (!isNaN(d.getTime())) return d;

        return null;
    }

    /**
     * Extract A1 notation references from expression
     */
    extractDependencies(expression) {
        if (!expression) return [];
        let allRefs = [];

        // Extract and expand ranges first (e.g., A1:B5)
        const rangeRegex = /([A-Z]+\d+):([A-Z]+\d+)/g;
        const processedExpr = expression.replace(rangeRegex, (match, start, end) => {
            const range = this._expandRange(start, end);
            allRefs.push(...range);
            return ''; // Remove to prevent double counting
        });

        // Extract remaining individual cell references
        const refRegex = /([A-Z]+)(\d+)/g;
        const refs = processedExpr.match(refRegex) || [];
        allRefs.push(...refs);

        return [...new Set(allRefs)];
    }

    // Alias for backward compatibility
    extractReferences(expression) {
        return this.extractDependencies(expression);
    }
    _registerDependencies(targetCellId, deps) {
        deps.forEach(depA1 => {
            if (!this.dependencyGraph.has(depA1)) {
                this.dependencyGraph.set(depA1, new Set());
            }
            this.dependencyGraph.get(depA1).add(targetCellId);
        });
    }

    /**
     * Internal recursive expression evaluator
     */
    _computeExpression(expr) {
        let processedExpr = expr.trim();

        // 1. Resolve parentheses groups and functions (inner to outer)
        let hasParen = true;
        let iterations = 0;

        while (hasParen && iterations < 20) {
            let found = false;

            // a. Resolve named functions: FUNC(args)
            const funcRegex = /([A-Z]+)\(([^()]*)\)/g;
            processedExpr = processedExpr.replace(funcRegex, (match, funcName, argsStr) => {
                found = true;
                const args = this._parseArgs(argsStr);
                if (this.functions[funcName]) {
                    return this.functions[funcName](...args);
                }
                return 0;
            });

            // b. Resolve plain parentheses: (expr)
            const parenRegex = /\(([^()]+)\)/g;
            processedExpr = processedExpr.replace(parenRegex, (match, inner) => {
                found = true;
                return inner; // Just strip parentheses for now, they will be handled by math later
            });

            if (!found) hasParen = false;
            iterations++;
        }

        // 2. Resolve cell references
        processedExpr = processedExpr.replace(/([A-Z]+)(\d+)/g, (match) => {
            const val = this._getCellValueByA1(match);
            return isNaN(val) ? 0 : val;
        });

        // 3. Simple math evaluation (Safe)
        try {
            let finalExpr = processedExpr.replace(/(\d+(\.\d+)?)%/g, '($1/100)');

            // Allow basic math characters only
            if (/[^0-9\+\-\*\/\.\(\) ]/.test(finalExpr)) {
                console.warn('[FormulaEngine] Invalid math expression:', finalExpr);
                return '#VALUE!';
            }

            const result = new Function(`return ${finalExpr}`)();
            if (typeof result === 'number' && !isFinite(result)) return '#DIV/0!';
            console.log(`[FormulaEngine] Evaluated "${expr}" -> "${finalExpr}" ->`, result);
            return result;
        } catch (e) {
            console.error('[FormulaEngine] Calculation error for expr:', expr, 'finalExpr:', processedExpr, e);
            return '#ERROR';
        }
    }

    _isSubtotalCell(ref) {
        if (!window.tableManager) return false;
        const cellId = this._mapA1ToCellId(ref);
        if (!cellId) return false;

        const [id, f] = cellId.split(':');
        const rowMap = this.rowMap || window.tableManager.rowMap;
        const row = rowMap ? rowMap.get(String(id)) : window.tableManager.currentData.find(r => r && r.id == id);
        if (!row) return false;

        let parsedFormulas = row.formulas;
        if (parsedFormulas) {
            if (typeof parsedFormulas === 'string') {
                try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
            }
            if (parsedFormulas && typeof parsedFormulas === 'object') {
                const formulaStr = String(parsedFormulas[f] || '').toUpperCase();
                return formulaStr.includes('SUBTOTAL');
            }
        }
        return false;
    }

    _parseArgs(argsStr) {
        const parts = argsStr.split(',');
        const args = [];
        parts.forEach(p => {
            p = p.trim();
            if (p.includes(':')) {
                const [start, end] = p.split(':');
                const range = this._expandRange(start, end);
                range.forEach(ref => {
                    if (this._isSubtotalCell(ref)) return; // Skip subtotal cells
                    const val = this._getCellValueByA1(ref);
                    args.push(parseFloat(val) || 0);
                });
            } else if (/^[A-Z]+\d+$/.test(p)) {
                if (this._isSubtotalCell(p)) return;
                const val = this._getCellValueByA1(p);
                args.push(parseFloat(val) || 0);
            } else {
                const val = parseFloat(p);
                args.push(isNaN(val) ? p : val);
            }
        });
        return args;
    }

    _expandRange(start, end) {
        const sMatch = start.match(/([A-Z]+)(\d+)/);
        const eMatch = end.match(/([A-Z]+)(\d+)/);
        if (!sMatch || !eMatch) return [];

        const sCol = this._colNameToIndex(sMatch[1]);
        const sRow = parseInt(sMatch[2]);
        const eCol = this._colNameToIndex(eMatch[1]);
        const eRow = parseInt(eMatch[2]);

        const cells = [];
        for (let r = Math.min(sRow, eRow); r <= Math.max(sRow, eRow); r++) {
            for (let c = Math.min(sCol, eCol); c <= Math.max(sCol, eCol); c++) {
                cells.push(this._indexToColName(c) + r);
            }
        }
        return cells;
    }

    /**
     * Map A1 to value from TableManager data
     */
    _getCellValueByA1(a1) {
        if (!window.tableManager) return 0;
        const cellId = this._mapA1ToCellId(a1);
        if (!cellId) return 0;

        const [id, f] = cellId.split(':');
        const rowMap = this.rowMap || window.tableManager.rowMap;
        const row = rowMap ? rowMap.get(String(id)) : window.tableManager.currentData.find(r => r && r.id == id);
        if (!row) return 0;

        // Handle manual-clear overrides
        if (row.formulas && row.formulas[f] === ' ') {
            if (row[f] === null || row[f] === undefined || row[f] === '' || row[f] === 0) {
                return 0;
            }
        }

        const val = this._getCellValueByA1_Logic(row[f]);
        console.log(`[FormulaEngine] cell ${a1} -> field ${f} -> raw: ${row[f]} -> parsed: ${val}`);
        return val;
    }

    _getCellValueByA1_Logic(val) {
        return window.Formatter ? window.Formatter.parseLocaleFloat(val) : 0;
    }

    _colNameToIndex(name) {
        let index = 0;
        for (let i = 0; i < name.length; i++) {
            index = index * 26 + (name.charCodeAt(i) - 64);
        }
        return index;
    }

    _indexToColName(index) {
        let name = '';
        while (index > 0) {
            let mod = (index - 1) % 26;
            name = String.fromCharCode(65 + mod) + name;
            index = Math.floor((index - mod) / 26);
        }
        return name;
    }

    _hasCircularReference(currentCellId, expression, visited = new Set()) {
        if (visited.has(currentCellId)) return true;
        visited.add(currentCellId);

        const deps = this.extractDependencies(expression);
        for (const depA1 of deps) {
            const depCellId = this._mapA1ToCellId(depA1);
            if (!depCellId) continue;

            // If the dependency itself is what we're currently visiting, it's circular
            if (visited.has(depCellId)) return true;

            const depFormula = this.formulas.get(depCellId);
            if (depFormula && depFormula.startsWith('=')) {
                if (this._hasCircularReference(depCellId, depFormula.substring(1), visited)) return true;
            }
        }

        visited.delete(currentCellId); // Backtrack
        return false;
    }

    _mapA1ToCellId(a1) {
        if (!window.tableManager) return null;
        const match = a1.match(/([A-Z]+)(\d+)/);
        if (!match) return null;

        const colIdx = this._colNameToIndex(match[1]);
        const rowIdx = parseInt(match[2]) - 1;
        const field = this.colToField[colIdx];
        const row = window.tableManager.currentData[rowIdx];

        return row ? `${row.id}:${field}` : null;
    }

    /**
     * Recalculate all cells that depend on a specific A1 reference
     */
    recalculateDependents(changedA1) {
        const dependents = this.dependencyGraph.get(changedA1);
        if (!dependents) return;

        dependents.forEach(cellId => {
            const [rowId, field] = cellId.split(':');
            const formula = this.formulas.get(cellId);
            if (formula) {
                const newValue = this.evaluate(formula, rowId, field);
                if (window.tableManager) {
                    window.tableManager.updateCellValue(rowId, field, newValue);
                    const td = document.querySelector(`td[data-id="${rowId}"][data-field="${field}"]`);
                    if (td) window.tableManager.renderCellDisplay(td, field, rowId);

                    // Queue save the calculated formula value to the database
                    window.tableManager.queueSave(rowId, field, newValue);

                    // Recursive call for chained dependencies
                    const cellA1 = this._mapCellIdToA1(cellId);
                    if (cellA1) this.recalculateDependents(cellA1);

                    // Sync auto-calc fields that might depend on this newly calculated value
                    if (typeof window.tableManager.updateRelatedCells === 'function') {
                        window.tableManager.updateRelatedCells(rowId);
                    }
                }
            }
        });
    }

    _mapCellIdToA1(cellId) {
        if (!window.tableManager) return null;
        const [rowId, field] = cellId.split(':');
        const row = window.tableManager.rowMap.get(String(rowId));
        const colIndex = this.fieldToCol[field];
        if (!row || !colIndex) return null;

        return this._indexToColName(colIndex) + (row._idx + 1);
    }

    evaluateCustomFormula(formulaStr, row) {
        if (!formulaStr) return 0;
        let expr = String(formulaStr).trim();
        if (expr.startsWith('=')) {
            expr = expr.substring(1);
        }

        const fields = [
            'harga', 'aktual', 'vol', 'surcharge', 'packing', 'handling',
            'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops',
            'nilai_barang', 'penjualan', 'total_biaya', 'asuransi',
            'asuransi_jasindo', 'profit', 'idx_profit', 'kubik', 'unit', 'koil'
        ];

        expr = expr.replace(/max\(/gi, 'Math.max(');
        expr = expr.replace(/min\(/gi, 'Math.min(');
        expr = expr.replace(/(\d+(\.\d+)?)%/g, '($1/100)');

        const sortedFields = [...fields].sort((a, b) => b.length - a.length);
        sortedFields.forEach(f => {
            const val = this._getCellValueByA1_Logic(row[f]);
            const regex = new RegExp('\\b' + f + '\\b', 'gi');
            expr = expr.replace(regex, val);
        });

        try {
            // Validate: only allow numbers, math operators, Math.max/min, parentheses, dots, commas, whitespace
            const isValid = /^[\d\s+\-*/().,%]*$/.test(expr.replace(/Math\.(max|min)/g, ''));
            if (!isValid) {
                console.warn('[FormulaEngine] Custom formula contains invalid characters:', expr);
                return 0;
            }
            const fn = new Function('return (' + expr + ');');
            const res = fn();
            return isNaN(res) || !isFinite(res) ? 0 : res;
        } catch (e) {
            console.error('[FormulaEngine] Error evaluating custom formula:', formulaStr, 'resolved to:', expr, e);
            return 0;
        }
    }

    isRowExcludedForField(row, field) {
        if (!row) return false;

        let parsedFormulas = row.formulas;
        if (parsedFormulas) {
            if (typeof parsedFormulas === 'string') {
                try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
            }
            if (parsedFormulas && parsedFormulas[field] === ' ') {
                return true;
            }
        }

        const config = (window.tableManager && window.tableManager.sheetConfig) || {};
        const fieldCfg = config[field];
        if (fieldCfg && fieldCfg.excludeRows && fieldCfg.excludeRows.trim()) {
            let rowIdx = row._idx;
            if (rowIdx === undefined && window.tableManager) {
                rowIdx = window.tableManager.currentData.findIndex(r => r && r.id == row.id);
            }
            if (rowIdx === undefined || rowIdx === -1) return false;

            const visualRowNum = rowIdx + 1;
            const excludedSet = new Set();
            const parts = fieldCfg.excludeRows.split(',');

            parts.forEach(part => {
                const range = part.trim().split('-');
                if (range.length === 1) {
                    const val = parseInt(range[0].trim());
                    if (!isNaN(val)) excludedSet.add(val);
                } else if (range.length === 2) {
                    const start = parseInt(range[0].trim());
                    const end = parseInt(range[1].trim());
                    if (!isNaN(start) && !isNaN(end)) {
                        const s = Math.min(start, end);
                        const e = Math.max(start, end);
                        for (let idx = s; idx <= e; idx++) {
                            excludedSet.add(idx);
                        }
                    }
                }
            });

            if (excludedSet.has(visualRowNum)) {
                return true;
            }
        }

        return false;
    }
}

// Export
window.FormulaEngine = FormulaEngine;
window.formulaEngine = new FormulaEngine();
