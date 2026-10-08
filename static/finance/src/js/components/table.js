/**
 * TABLE MANAGER: Pengelola Tabel KPI Interaktif (Spreadsheet Mode)
 * 1000 baris selalu tersedia dan SEMUA siap diedit tanpa auto-create
 */
class TableManager {
    constructor() {
        this.selectedRange = { sr: -1, er: -1, sc: -1, ec: -1 };
        this.activeCellPos = { r: -1, c: -1 };
        this.currentData = [];
        this.originalData = [];
        this.editingCell = null;
        this.selectedCells = [];
        this.activeCell = null;
        this.spreadsheetState = {
            activeCell: { row: null, col: null },
            selection: { startRow: null, startCol: null, endRow: null, endCol: null }
        };
        this.isDragging = false;
        this.dragStartCell = null;
        this.history = new HistoryManager(this);
        this.colWidths = {};
        this.saveQueue = new Map();

        this.saveTimer = null;
        this.displayRows = 100;
        this.clipboard = null;
        this.selectedColumns = [];
        this.columnSortState = { field: null, direction: null };
        this.findState = { query: '', matches: [], currentIdx: -1, showReplace: false };
        this.preloadedRows = [];
        this.isPreloading = false;
        this.initContextMenus();
        this.selection = new SelectionManager(this);
        this.selectCell = (td) => this.selection.selectCell(td);
        this.selectRangeByPos = (s, e) => this.selection.selectRangeByPos(s, e);
        this.selectRange = (sTd, eTd) => this.selection.selectRange(sTd, eTd);
        this.handleAutoScroll = (e) => this.selection.handleAutoScroll(e);
        this.stopAutoScroll = () => this.selection.stopAutoScroll();
        this._updateSelectionUI = () => this.selection._updateSelectionUI();

        this.keyboard = new KeyboardManager(this);
        this.keyboard.init();
        this.initFloatingToolbar();
        this.initTableEvents();
        this.initFormulaBar();
        this._initFormulaAutocomplete();

        this._initRowMap();
        this.initPresence(); // Fitur Presence (Remote Cursor)

        this.activeSyncCount = 0;
        window.addEventListener('beforeunload', (e) => {
            if (Object.keys(this.saveQueue).length > 0 || this.activeSyncCount > 0) {
                this.flushSaveQueue();
                e.preventDefault();
                e.returnValue = 'Ada perubahan yang belum tersimpan atau sedang disimpan ke server. Yakin ingin keluar?';
                return e.returnValue;
            }
        });
        
        // Mulai polling real-time untuk data CRM
        this.startRealtimeSync();
        
        console.log('✅ TableManager v2.4 Loaded (Audit Log, Presence & Save Safety Ready)');
    }

    _initRowMap() {
        this.rowMap = new Map();
        if (this.currentData) {
            this.currentData.forEach(r => { if (r) this.rowMap.set(String(r.id), r); });
        }
    }

    initTableEvents() {
        const t = document.getElementById('kpiTableBody');
        if (!t) return;
        t.addEventListener('contextmenu', (e) => {
            const td = e.target.closest('td');
            if (td && !td.classList.contains('col-actions') && !td.classList.contains('col-index')) {
                e.preventDefault();
                if (!td.classList.contains('cell-selected') && !td.classList.contains('cell-active')) this.selectCell(td);
                this.showContextMenu(e.pageX, e.pageY);
            }
        });

        const thead = document.querySelector('#kpiTable thead');
        if (thead) {
            thead.addEventListener('contextmenu', (e) => {
                const th = e.target.closest('th');
                if (!th || th.classList.contains('col-index') || th.classList.contains('col-actions')) return;
                e.preventDefault();
                e.stopPropagation();
                const ci = th.cellIndex;
                if (!this.selectedColumns.includes(ci) || this.selectedRange.sr !== 0) this.selectColumn(ci);
                this.showColumnContextMenu(e.pageX, e.pageY);
            });
            thead.addEventListener('click', (e) => {
                const th = e.target.closest('th');
                if (!th || th.classList.contains('col-index') || th.classList.contains('col-actions')) return;
                const ci = th.cellIndex;
                if (e.shiftKey && this.selectedColumns.length > 0) {
                    this.selectColumnRange(this.selectedColumns[this.selectedColumns.length - 1], ci);
                } else {
                    this.selectColumn(ci);
                }
            });
        }

        t.addEventListener('mousedown', (e) => {
            if (e.button === 2) return;
            const td = e.target.closest('td');
            if (!td || td.classList.contains('col-actions')) return;

            // Check if clicked close to bottom-right corner of the active cell (autofill handle)
            const isActiveCell = td.classList.contains('cell-active');
            let isHandleClick = false;
            if (isActiveCell) {
                const rect = td.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const clickY = e.clientY - rect.top;
                isHandleClick = (rect.width - clickX <= 12) && (rect.height - clickY <= 12);
            }

            if (isHandleClick) {
                e.preventDefault();
                e.stopPropagation();
                this.isFillDragging = true;
                const tr = td.closest('tr');
                this.fillStartPos = { r: parseInt(tr.dataset.idx), c: td.cellIndex };
                document.body.style.userSelect = 'none';
                return;
            }

            // ==================== FORMULA PICKING LOGIC ====================
            const editor = document.getElementById('cellFloatingEditor');
            const editorInp = editor?.querySelector('input');

            if (this.editingCell && editor?.style.display === 'block' && editorInp && editorInp.value.startsWith('=')) {
                if (!td.classList.contains('col-index') && td !== this.editingCell.td) {
                    e.preventDefault();
                    e.stopPropagation();

                    const a1 = window.formulaEngine._mapCellIdToA1(`${td.dataset.id}:${td.dataset.field}`);
                    if (a1) {
                        this.isPickingRange = true;
                        this.pickStartA1 = a1;
                        this._insertReferenceIntoEditor(editorInp, a1);
                        return;
                    }
                }
            }

            // Standard selection logic
            if (td.classList.contains('col-index')) {
                const tr = td.closest('tr');
                if (tr) this.selectRow(tr.dataset.idx);
                return;
            }

            this.isDragging = true;
            this.dragStartCell = td;

            const tr = td.closest('tr');
            this.dragStartPos = { r: parseInt(tr.dataset.idx), c: td.cellIndex };

            if (e.shiftKey && this.activeCell) {
                this.selectRange(this.activeCell, td);
            } else {
                this.selectCell(td);
            }

            document.body.style.userSelect = 'none';
        });

        window.addEventListener('mousemove', (e) => {
            if (this.isFillDragging && this.fillStartPos) {
                const td = document.elementFromPoint(e.clientX, e.clientY)?.closest('td');
                if (td && !td.classList.contains('col-index') && !td.classList.contains('col-actions')) {
                    const tr = td.closest('tr');
                    if (tr && tr.dataset.idx !== undefined) {
                        const r = parseInt(tr.dataset.idx);
                        const c = td.cellIndex;

                        const rowDelta = Math.abs(r - this.fillStartPos.r);
                        const colDelta = Math.abs(c - this.fillStartPos.c);

                        if (rowDelta >= colDelta) {
                            this.selectRangeByPos(this.fillStartPos, { r, c: this.fillStartPos.c });
                        } else {
                            this.selectRangeByPos(this.fillStartPos, { r: this.fillStartPos.r, c });
                        }
                    }
                }
                this.handleAutoScroll(e);
                return;
            }

            if (this.isDragging && this.dragStartPos) {
                const targetEl = document.elementFromPoint(e.clientX, e.clientY);
                const td = targetEl?.closest('td');
                const th = targetEl?.closest('th');

                if (td && !td.classList.contains('col-index') && !td.classList.contains('col-actions')) {
                    const tr = td.closest('tr');
                    if (tr && tr.dataset.idx !== undefined) {
                        const r = parseInt(tr.dataset.idx);
                        const c = td.cellIndex;
                        this.selectRangeByPos(this.dragStartPos, { r, c });
                    }
                } else if (th && !th.classList.contains('col-index') && !th.classList.contains('col-actions')) {
                    const c = th.cellIndex;
                    if (c !== undefined && c >= 0) {
                        this.selectRangeByPos(this.dragStartPos, { r: 0, c });
                    }
                }
                this.handleAutoScroll(e);
            }

            if (this.isPickingRange && this.pickStartA1) {
                const td = e.target.closest('td');
                if (td && !td.classList.contains('col-index') && !td.classList.contains('col-actions')) {
                    const currentA1 = window.formulaEngine._mapCellIdToA1(`${td.dataset.id}:${td.dataset.field}`);
                    if (currentA1 && currentA1 !== this.lastPickedA1) {
                        const editor = document.getElementById('cellFloatingEditor');
                        const inp = editor?.querySelector('input');
                        if (inp) {
                            const range = this.pickStartA1 === currentA1 ? this.pickStartA1 : `${this.pickStartA1}:${currentA1}`;
                            this._insertReferenceIntoEditor(inp, range, true);
                            this.lastPickedA1 = currentA1;
                        }
                    }
                }
            }
        });

        window.addEventListener('mouseup', () => {
            if (this.isFillDragging) {
                this.isFillDragging = false;
                document.body.style.userSelect = '';
                this.stopAutoScroll();

                const { sr, er, sc, ec } = this.selectedRange;
                this.autofillRange(sr, er, sc, ec);
            }
            if (this.isDragging) {
                this.isDragging = false;
                document.body.style.userSelect = '';
                this.stopAutoScroll();
            }
            this.isPickingRange = false;
            this.pickStartA1 = null;
            this.lastPickedA1 = null;
        });

        t.addEventListener('click', (e) => {
            const td = e.target.closest('td');
            if (!td || td.classList.contains('col-index') || td.classList.contains('col-actions')) return;

            if (td.classList.contains('cell-readonly')) {
                const colLabel = EDITABLE_COLUMNS.find(c => c.field === td.dataset.field)?.label || td.dataset.field;
                this.updateStatusBar('⚠ Kolom "' + colLabel + '" tidak boleh diedit oleh Anda');
                return;
            }

            // Committing current edit if clicking elsewhere
            if (this.editingCell && this.editingCell.td !== td) {
                this.saveCellEdit();
            }

            this.selectCell(td);
        });

        t.addEventListener('dblclick', (e) => {
            const td = e.target.closest('td');
            if (!td) return;

            // Allow editing if not a helper column
            if (td.classList.contains('col-index') || td.classList.contains('col-actions')) return;
            if (td.classList.contains('cell-readonly')) return;

            console.log('[Table] Triggering edit for cell:', td.dataset.field, td.dataset.id);
            this.startEditCell(td);
        });
    }

    initFloatingToolbar() {
        const ft = document.createElement('div');
        ft.id = 'floatingToolbar';
        ft.className = 'floating-toolbar';
        ft.style.display = 'none';
        ft.innerHTML = `
            <button class="btn-float" data-action="copy" title="Copy (Ctrl+C)"><i class="fas fa-copy"></i></button>
            <button class="btn-float" data-action="cut" title="Cut (Ctrl+X)"><i class="fas fa-cut"></i></button>
            <button class="btn-float" data-action="paste" title="Paste (Ctrl+V)"><i class="fas fa-paste"></i></button>
            <div class="float-divider"></div>
            <button class="btn-float" data-action="custom-formula" title="Custom Formula"><i class="fas fa-function"></i> ƒ</button>
            <div class="float-divider"></div>
            <button class="btn-float" data-action="delete" title="Hapus (Del)"><i class="fas fa-eraser"></i></button>
            <button class="btn-float danger" data-action="delete-row" title="Hapus Baris"><i class="fas fa-trash"></i></button>
        `;
        document.body.appendChild(ft);
        this.floatingToolbar = ft;

        ft.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (btn) { this.handleCellAction(btn.dataset.action); this.hideFloatingToolbar(); }
        });

        document.addEventListener('mousedown', (e) => {
            if (this.floatingToolbar && !this.floatingToolbar.contains(e.target)) this.hideFloatingToolbar();
        });
    }

    showFloatingToolbar(x, y) {
        if (!this.floatingToolbar) return;
        this.floatingToolbar.style.left = x + 'px';
        this.floatingToolbar.style.top = (y - 50) + 'px';
        this.floatingToolbar.style.display = 'flex';
    }

    hideFloatingToolbar() {
        if (this.floatingToolbar) this.floatingToolbar.style.display = 'none';
    }

    initFormulaBar() {
        const bar = document.getElementById('formulaBar');
        if (!bar) return;

        bar.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (this.activeCell) {
                    this._applyFormulaFromBar(bar.value);
                    bar.blur();
                }
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                this._updateFormulaBar(this.activeCell);
                bar.blur();
            }
        });

        bar.addEventListener('input', () => {
            this.showAutocomplete(bar);
            this.highlightReferencedCells(bar.value);
        });

        bar.addEventListener('focus', () => {
            if (!this.activeCell) bar.blur();
            else this.highlightReferencedCells(bar.value);
        });
    }

    _updateFormulaBar(td) {
        this.clearReferencedHighlights();
        const bar = document.getElementById('formulaBar');
        if (!bar || !td) return;
        const id = td.dataset.id, f = td.dataset.field;
        if (!id || !f) { bar.value = ''; return; }

        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
        if (!row) { bar.value = ''; return; }

        const formula = row.formulas ? row.formulas[f] : null;
        const isRealFormula = typeof formula === 'string' && formula.trim().startsWith('=');
        if (isRealFormula) {
            bar.value = formula;
        } else {
            const cfg = (this.sheetConfig && this.sheetConfig[f]) || { autoCalc: false };
            let isExcluded = false;
            if (window.formulaEngine && window.formulaEngine.isRowExcludedForField(row, f)) {
                isExcluded = true;
            }
            if (cfg.autoCalc && !isExcluded) {
                if (cfg.formula) {
                    const cleanFormula = cfg.formula.trim().startsWith('=') ? cfg.formula.trim().substring(1) : cfg.formula;
                    bar.value = `[AUTO] =${cleanFormula}`;
                } else {
                    let tpl = cfg.template || '';
                    let lbl = '';
                    if (f === 'penjualan') {
                        if (tpl === 'double_charge') lbl = '(HARGA * AKTUAL) + (HARGA * VOL) + SURCHARGE + PACKING + HANDLING';
                        else if (tpl === 'actual_only') lbl = '(HARGA * AKTUAL) + SURCHARGE + PACKING + HANDLING';
                        else if (tpl === 'volume_only') lbl = '(HARGA * VOL) + SURCHARGE + PACKING + HANDLING';
                        else lbl = '(HARGA * MAX(AKTUAL, VOL)) + SURCHARGE + PACKING + HANDLING';
                    } else if (f === 'total_biaya') lbl = 'VENDOR_I + VENDOR_II + VENDOR_III + VENDOR_IV + OPS';
                    else if (f === 'profit') lbl = 'PENJUALAN - TOTAL_BIAYA - ASURANSI_JASINDO';
                    else if (f === 'asuransi') lbl = 'NILAI_BARANG * 0.2%';
                    else if (f === 'asuransi_jasindo') lbl = 'NILAI_BARANG * 0.1%';
                    else if (f === 'idx_profit') lbl = 'PROFIT / PENJUALAN';
                    bar.value = lbl ? `[AUTO] =${lbl}` : `[AUTO] (Sistem)`;
                }
            } else {
                const rawVal = this.getRawValue(id, f);
                if (f === 'tanggal_pickup' && rawVal) {
                    bar.value = this.fmtDate(rawVal);
                } else {
                    bar.value = rawVal || '';
                }
            }
        }
    }

    _applyFormulaFromBar(value) {
        if (!this.activeCell) return;
        if (typeof value === 'string' && value.startsWith('[AUTO]')) return;
        const td = this.activeCell, id = td.dataset.id, f = td.dataset.field;
        if (!id || !f || !this.isColEditable(f)) return;

        const ov = this.getRawValue(id, f);
        this._processAndSaveValue(id, f, value, ov, td);
    }

    _initializeFormulas() {
        if (!this.currentData) return;

        // Clear formula engine state before re-initializing to avoid stale cross-load/cross-sheet dependencies
        if (window.formulaEngine) {
            window.formulaEngine.formulas.clear();
            window.formulaEngine.dependencyGraph.clear();
        }

        // 1. Normalize formulas to object if it's a string from the database
        this.currentData.forEach(row => {
            if (!row) return;
            if (row.formulas && typeof row.formulas === 'string') {
                try {
                    row.formulas = JSON.parse(row.formulas);
                } catch (e) {
                    console.error('Failed to parse row.formulas:', e);
                    row.formulas = null;
                }
            }
        });

        // 2. Pass 1: Iterative Relaxation Loop to evaluate manual formulas in normal (non-subtotal) rows
        // This ensures multi-level chained formula dependencies are resolved correctly.
        let changed = true;
        let iterations = 0;
        const maxIterations = 5;

        while (changed && iterations < maxIterations) {
            changed = false;
            this.currentData.forEach(row => {
                if (!row) return;
                // Skip subtotal rows in this pass
                const isSubtotal = row.formulas && Object.values(row.formulas).some(v => typeof v === 'string' && v.includes('SUBTOTAL'));
                if (isSubtotal) return;

                if (row.formulas && typeof row.formulas === 'object') {
                    Object.entries(row.formulas).forEach(([field, formula]) => {
                        if (typeof formula === 'string' && formula.startsWith('=')) {
                            const oldVal = row[field];
                            const newVal = window.formulaEngine.evaluate(formula, row.id, field);
                            // Stringify comparisons to prevent false negatives from type mismatches
                            if (String(oldVal) !== String(newVal)) {
                                row[field] = newVal;
                                changed = true;
                            }
                        }
                    });
                }
            });
            iterations++;
        }

        // 3. Pass 2: Dynamically calculate automatic computed fields in memory for non-subtotal rows
        const _pass2Config = this.sheetConfig || {};
        console.log('[AutoCalc] _initializeFormulas Pass2 with sheetConfig keys:', Object.keys(_pass2Config), 'penjualan.autoCalc:', _pass2Config.penjualan?.autoCalc, 'penjualan.formula:', _pass2Config.penjualan?.formula);
        this.currentData.forEach(row => {
            if (!row) return;

            // Skip subtotal rows from standard formula calculations
            const isSubtotal = row.formulas && Object.values(row.formulas).some(v => typeof v === 'string' && v.includes('SUBTOTAL'));
            if (isSubtotal) return;

            const hasFormula = (field) => {
                if (window.formulaEngine && window.formulaEngine.isRowExcludedForField(row, field)) return true;
                return row.formulas && row.formulas[field];
            };

            const config = this.sheetConfig || {};

            // Kolom Penjualan
            const penjualanCfg = config.penjualan || { autoCalc: true, template: 'standard_cargo' };
            if (penjualanCfg.autoCalc && !hasFormula('penjualan')) {
                if (penjualanCfg.formula) {
                    row.penjualan = window.formulaEngine.evaluateCustomFormula(penjualanCfg.formula, row);
                } else {
                    row.penjualan = window.formulaEngine.compute('penjualan', row, { template: penjualanCfg.template });
                }
            }

            // Kolom Total Biaya
            const totalBiayaCfg = config.total_biaya || { autoCalc: true, template: 'vendor_ops' };
            if (totalBiayaCfg.autoCalc && !hasFormula('total_biaya')) {
                if (totalBiayaCfg.formula) {
                    row.total_biaya = window.formulaEngine.evaluateCustomFormula(totalBiayaCfg.formula, row);
                } else {
                    row.total_biaya = window.formulaEngine.compute('total_biaya', row, { template: totalBiayaCfg.template });
                }
            }

            // Kolom Asuransi
            const asuransiCfg = config.asuransi || { autoCalc: true, template: 'nilai_barang_02' };
            if (asuransiCfg.autoCalc && !hasFormula('asuransi')) {
                if (asuransiCfg.formula) {
                    row.asuransi = window.formulaEngine.evaluateCustomFormula(asuransiCfg.formula, row);
                } else {
                    row.asuransi = window.formulaEngine.compute('asuransi', row, { template: asuransiCfg.template });
                }
            }

            // Kolom Asuransi Jasindo
            const jasindoCfg = config.asuransi_jasindo || { autoCalc: true, template: 'nilai_barang_01' };
            if (jasindoCfg.autoCalc && !hasFormula('asuransi_jasindo')) {
                if (jasindoCfg.formula) {
                    row.asuransi_jasindo = window.formulaEngine.evaluateCustomFormula(jasindoCfg.formula, row);
                } else {
                    row.asuransi_jasindo = window.formulaEngine.compute('asuransi_jasindo', row, { template: jasindoCfg.template });
                }
            }

            // Kolom Profit
            const profitCfg = config.profit || { autoCalc: true, template: 'penjualan_minus_cost' };
            if (profitCfg.autoCalc && !hasFormula('profit')) {
                if (profitCfg.formula) {
                    row.profit = window.formulaEngine.evaluateCustomFormula(profitCfg.formula, row);
                } else {
                    row.profit = window.formulaEngine.compute('profit', row, { template: profitCfg.template });
                }
            }

            // Kolom Margin Percent (IDX Profit)
            const idxProfitCfg = config.idx_profit || { autoCalc: true };
            if (idxProfitCfg.autoCalc && !hasFormula('idx_profit')) {
                row.idx_profit = row.penjualan === 0 ? 0 : (row.profit / row.penjualan);
            }
        });

        // 4. Pass 3: Finally, evaluate manual formulas in subtotal rows (so they sum the correctly computed profit/penjualan)
        this.currentData.forEach(row => {
            if (!row) return;
            const isSubtotal = row.formulas && Object.values(row.formulas).some(v => typeof v === 'string' && v.includes('SUBTOTAL'));
            if (!isSubtotal) return;

            if (row.formulas && typeof row.formulas === 'object') {
                Object.entries(row.formulas).forEach(([field, formula]) => {
                    if (typeof formula === 'string' && formula.startsWith('=')) {
                        console.log(`[FormulaEngine] Subtotal Row ${row.id} has formula: ${formula} on field ${field}`);
                        const val = window.formulaEngine.evaluate(formula, row.id, field);
                        console.log(`[FormulaEngine] Subtotal Result for Row ${row.id} field ${field}:`, val);
                        row[field] = val; // Store computed value locally
                    }
                });
            }
        });
    }

    initContextMenus() {
        const cm = document.getElementById('contextMenu');
        if (cm) {
            cm.innerHTML = '<div class="context-menu-item" data-action="copy"><i class="fas fa-copy"></i> Copy <span class="context-menu-shortcut">Ctrl+C</span></div><div class="context-menu-item" data-action="cut"><i class="fas fa-cut"></i> Cut <span class="context-menu-shortcut">Ctrl+X</span></div><div class="context-menu-item" data-action="paste"><i class="fas fa-paste"></i> Paste <span class="context-menu-shortcut">Ctrl+V</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="autofill-down"><i class="fas fa-arrow-down"></i> Auto-Fill Down <span class="context-menu-shortcut">Ctrl+D</span></div><div class="context-menu-item" data-action="autofill-right"><i class="fas fa-arrow-right"></i> Auto-Fill Right</div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="custom-formula"><i class="fas fa-calculator"></i> Custom Formula <span class="context-menu-shortcut">ƒ</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="delete"><i class="fas fa-eraser"></i> Hapus Isi <span class="context-menu-shortcut">Del</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="undo"><i class="fas fa-undo"></i> Undo <span class="context-menu-shortcut">Ctrl+Z</span></div><div class="context-menu-item" data-action="redo"><i class="fas fa-redo"></i> Redo <span class="context-menu-shortcut">Ctrl+Y</span></div><div class="context-menu-divider"></div><div class="context-menu-item danger" data-action="delete-row"><i class="fas fa-trash"></i> Hapus Baris</div>';
            this.cellContextMenu = cm;
            document.addEventListener('click', () => cm.classList.remove('show'));
            cm.addEventListener('click', (e) => { const i = e.target.closest('.context-menu-item'); if (i) { this.handleCellAction(i.dataset.action); cm.classList.remove('show'); } });
        }
        const col = document.getElementById('columnContextMenu');
        if (col) {
            this.columnContextMenu = col;
            document.addEventListener('click', () => col.classList.remove('show'));
            col.addEventListener('click', (e) => { const i = e.target.closest('.context-menu-item'); if (i) { this.handleColAction(i.dataset.action); col.classList.remove('show'); } });
        }
    }

    handleCellAction(a) {
        const m = {
            copy: () => this.copySelection(),
            cut: () => this.cutSelection(),
            paste: () => this.pasteFromClipboard(),
            'autofill-down': () => { const { sr, er, sc, ec } = this.selectedRange; this.autofillRange(sr, er, sc, ec); },
            'autofill-right': () => { const { sr, er, sc, ec } = this.selectedRange; this.autofillRange(sr, er, sc, ec); },
            delete: () => this.deleteSelection(),
            'delete-all': () => this.deleteAllCells(),
            undo: () => this.history.undo(),
            redo: () => this.history.redo(),
            'delete-row': () => this.deleteActiveRow(),
            'custom-formula': () => this.showCustomFormulaDialog(),
            'reset-to-auto': () => this.resetCellToAuto(),
            'set-to-manual': () => this.setCellToManual(),
            'toggle-lock': () => this.toggleLockCells(),
            'edit-comment': () => this.showCommentDialog(),
            'delete-comment': () => this.deleteComment(),
            'cell-date-swap': () => this.swapDateMonthFormats()
        };
        if (m[a]) m[a]();
    }

    handleColAction(a) {
        if (!this.selectedColumns.length) return;
        const f = this.getColumnField(this.selectedColumns[0]);
        switch (a) {
            case 'sort-asc': if (f) this.sortByColumn(f, 'asc'); break;
            case 'sort-desc': if (f) this.sortByColumn(f, 'desc'); break;
            case 'sort-none': this.sortByColumn(null, null); break;
            case 'col-copy': this.copySelection(); break;
            case 'col-clear': this.clearColumns(); break;
            case 'col-select-all': this.selectAllColumns(); break;
            case 'col-date-bulk': if(f === 'tanggal_pickup') this.showBulkDateEditDialog(); break;
            case 'col-date-clean': if(f === 'tanggal_pickup') this.cleanDateFormats(); break;
            case 'col-date-swap': if(f === 'tanggal_pickup') this.swapDateMonthFormats(); break;
        }
    }

    getColumnField(ci) {
        const th = document.querySelector('#kpiTable thead tr:last-child th:nth-child(' + (ci + 1) + ')');
        return th?.dataset?.field || null;
    }

    showContextMenu(x, y) {
        if (!this.cellContextMenu) return;

        let autoCalcItems = '';
        if (this.activeCell) {
            const field = this.activeCell.dataset.field;
            const id = this.activeCell.dataset.id;
            const computedColumns = ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'];

            if (computedColumns.includes(field)) {
                const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
                if (row) {
                    const formulasObj = row.formulas || {};
                    const hasManualFormula = formulasObj[field] !== undefined;

                    const config = this.sheetConfig || {};
                    let activeFormulaDesc = '';
                    if (field === 'penjualan') {
                        const temp = (config.penjualan && config.penjualan.template) || 'standard_cargo';
                        activeFormulaDesc = temp === 'double_charge' ? '(Harga * Aktual) + (Harga * Vol) + Surcharge + Packing + Handling' :
                            temp === 'actual_only' ? '(Harga * Aktual) + Surcharge + Packing + Handling' :
                                temp === 'volume_only' ? '(Harga * Vol) + Surcharge + Packing + Handling' :
                                    '(Harga * MAX(Aktual, Vol)) + Surcharge + Packing + Handling';
                    } else if (field === 'total_biaya') {
                        activeFormulaDesc = 'Vendor I + II + III + IV + Ops';
                    } else if (field === 'profit') {
                        activeFormulaDesc = 'Penjualan - Total Biaya - Asuransi Jasindo';
                    } else if (field === 'asuransi') {
                        const temp = (config.asuransi && config.asuransi.template) || 'nilai_barang_02';
                        activeFormulaDesc = temp === 'nilai_barang_none' ? '0 (Nonaktif)' : 'Nilai Barang * 0.2%';
                    } else if (field === 'asuransi_jasindo') {
                        const temp = (config.asuransi_jasindo && config.asuransi_jasindo.template) || 'nilai_barang_01';
                        activeFormulaDesc = temp === 'nilai_barang_none' ? '0 (Nonaktif)' : 'Nilai Barang * 0.1%';
                    } else if (field === 'idx_profit') {
                        activeFormulaDesc = 'Profit / Penjualan (Margin)';
                    }

                    const statusText = hasManualFormula
                        ? `<span style="color: #EF4444; font-weight: bold;">Manual Override</span>`
                        : `<span style="color: #10B981; font-weight: bold;">Otomatis (Template Sheet)</span>`;

                    autoCalcItems += `<div class="context-menu-divider"></div>`;
                    autoCalcItems += `<div class="context-menu-item disabled" style="opacity: 0.85; font-size: 0.8rem; pointer-events: none; padding: 4px 12px; background: rgba(255,255,255,0.05); color: #f3f4f6;">Rumus: ${activeFormulaDesc}</div>`;
                    autoCalcItems += `<div class="context-menu-item disabled" style="opacity: 0.85; font-size: 0.8rem; pointer-events: none; padding: 4px 12px; background: rgba(255,255,255,0.05); color: #f3f4f6;">Status: ${statusText}</div>`;

                    if (hasManualFormula) {
                        autoCalcItems += `<div class="context-menu-item" data-action="reset-to-auto" style="color: #10B981; font-weight: 500;"><i class="fas fa-magic"></i> Kembalikan ke Perhitungan Otomatis</div>`;
                    } else {
                        autoCalcItems += `<div class="context-menu-item" data-action="set-to-manual" style="color: #EF4444; font-weight: 500;"><i class="fas fa-unlock"></i> Buka Kunci & Edit (Override Manual)</div>`;
                    }
                }
            }
        }
        const baseHTMLPart1 = '<div class="context-menu-item" data-action="copy"><i class="fas fa-copy"></i> Copy <span class="context-menu-shortcut">Ctrl+C</span></div><div class="context-menu-item" data-action="cut"><i class="fas fa-cut"></i> Cut <span class="context-menu-shortcut">Ctrl+X</span></div><div class="context-menu-item" data-action="paste"><i class="fas fa-paste"></i> Paste <span class="context-menu-shortcut">Ctrl+V</span></div><div class="context-menu-divider"></div>';

        const baseHTMLPart2 = '<div class="context-menu-item" data-action="autofill-down"><i class="fas fa-arrow-down"></i> Auto-Fill Down <span class="context-menu-shortcut">Ctrl+D</span></div><div class="context-menu-item" data-action="autofill-right"><i class="fas fa-arrow-right"></i> Auto-Fill Right</div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="custom-formula"><i class="fas fa-calculator"></i> Custom Formula <span class="context-menu-shortcut">ƒx</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="delete"><i class="fas fa-eraser"></i> Hapus Isi <span class="context-menu-shortcut">Del</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="undo"><i class="fas fa-undo"></i> Undo <span class="context-menu-shortcut">Ctrl+Z</span></div><div class="context-menu-item" data-action="redo"><i class="fas fa-redo"></i> Redo <span class="context-menu-shortcut">Ctrl+Y</span></div>';

        const deleteRowHTML = '<div class="context-menu-divider"></div><div class="context-menu-item danger" data-action="delete-all"><i class="fas fa-dumpster"></i> Hapus Semua Cell</div><div class="context-menu-divider"></div><div class="context-menu-item danger" data-action="delete-row"><i class="fas fa-trash"></i> Hapus Baris</div>';

        const lockHTML = '<div class="context-menu-divider"></div><div class="context-menu-item" data-action="toggle-lock"><i class="fas fa-lock"></i> Kunci / Buka Sel</div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="edit-comment"><i class="fas fa-comment-dots"></i> Add / Edit Comment</div><div class="context-menu-item" data-action="delete-comment"><i class="fas fa-comment-slash"></i> Hapus Comment</div>';

        let dateHTML = '';
        if (this.activeCell && this.activeCell.dataset.field === 'tanggal_pickup') {
            dateHTML = '<div class="context-menu-divider"></div><div class="context-menu-item text-blue-600 font-medium" data-action="cell-date-swap"><i class="fas fa-exchange-alt text-blue-500"></i> Tukar Posisi Tanggal & Bulan</div>';
        }

        this.cellContextMenu.innerHTML = baseHTMLPart1 + (autoCalcItems ? autoCalcItems + '<div class="context-menu-divider"></div>' : '') + baseHTMLPart2 + lockHTML + dateHTML + deleteRowHTML;

        this.cellContextMenu.style.left = x + 'px';
        this.cellContextMenu.style.top = y + 'px';
        this.cellContextMenu.classList.add('show');
        
        // Prevent menu from going out of screen bounds
        const rect = this.cellContextMenu.getBoundingClientRect();
        if (y + rect.height > window.innerHeight) {
            this.cellContextMenu.style.top = Math.max(0, window.innerHeight - rect.height - 10) + 'px';
        }
        if (x + rect.width > window.innerWidth) {
            this.cellContextMenu.style.left = Math.max(0, window.innerWidth - rect.width - 10) + 'px';
        }
    }

    toggleLockCells() {
        if (this.selectedRange.sr === -1 && !this.activeCell) return;
        
        const { sr, er, sc, ec } = this.selectedRange.sr !== -1 
            ? this.selectedRange 
            : { 
                sr: this.currentData.findIndex(r => r.id == this.activeCell.dataset.id),
                er: this.currentData.findIndex(r => r.id == this.activeCell.dataset.id),
                sc: window.formulaEngine.colToField.indexOf(this.activeCell.dataset.field),
                ec: window.formulaEngine.colToField.indexOf(this.activeCell.dataset.field)
              };

        if (sr === -1 || sc === -1) return;

        const firstRow = this.currentData[sr];
        const firstField = window.formulaEngine.colToField[sc];
        
        let isLocked = false;
        if (firstRow) {
            while (firstRow.formulas && typeof firstRow.formulas === 'string') {
                try { 
                    let parsed = JSON.parse(firstRow.formulas); 
                    if (typeof parsed === 'string' && parsed === firstRow.formulas) break; 
                    firstRow.formulas = parsed; 
                } catch (e) { firstRow.formulas = {}; break; }
            }
            if (firstRow.formulas && firstRow.formulas.__formats && firstRow.formulas.__formats[firstField]) {
                isLocked = firstRow.formulas.__formats[firstField].locked;
            }
        }
        const targetLock = !isLocked;
        let lockedCount = 0;

        for (let r = sr; r <= er; r++) {
            const row = this.currentData[r];
            if (!row || String(row.id).startsWith('preload_')) continue;
            
            for (let c = sc; c <= ec; c++) {
                const field = window.formulaEngine.colToField[c];
                if (!field) continue;
                
                while (row.formulas && typeof row.formulas === 'string') { 
                    try { 
                        let parsed = JSON.parse(row.formulas); 
                        if (typeof parsed === 'string' && parsed === row.formulas) break; 
                        row.formulas = parsed; 
                    } catch (e) { row.formulas = {}; break; } 
                }
                
                if (!row.formulas) row.formulas = {};
                if (!row.formulas.__formats) row.formulas.__formats = {};
                if (!row.formulas.__formats[field]) row.formulas.__formats[field] = {};
                row.formulas.__formats[field].locked = targetLock;
                
                const td = document.querySelector(`td[data-id="${row.id}"][data-field="${field}"]`);
                if (td) this.renderCellDisplay(td, field, row.id);
                
                this.queueSave(row.id, 'formulas', row.formulas);
                lockedCount++;
            }
        }
        this.updateStatusBar(`Lock diubah untuk ${lockedCount} cell`);
    }

    deleteComment() {
        if (this.selectedRange.sr === -1 && !this.activeCell) return;
        
        const { sr, er, sc, ec } = this.selectedRange.sr !== -1 
            ? this.selectedRange 
            : { 
                sr: this.currentData.findIndex(r => r.id == this.activeCell.dataset.id),
                er: this.currentData.findIndex(r => r.id == this.activeCell.dataset.id),
                sc: window.formulaEngine.colToField.indexOf(this.activeCell.dataset.field),
                ec: window.formulaEngine.colToField.indexOf(this.activeCell.dataset.field)
              };

        if (sr === -1 || sc === -1) return;

        let deletedCount = 0;
        
        for (let r = sr; r <= er; r++) {
            const row = this.currentData[r];
            if (!row || String(row.id).startsWith('preload_')) continue;
            
            for (let c = sc; c <= ec; c++) {
                const field = window.formulaEngine.colToField[c];
                if (!field) continue;
                
                while (row.formulas && typeof row.formulas === 'string') { 
                    try { 
                        let parsed = JSON.parse(row.formulas); 
                        if (typeof parsed === 'string' && parsed === row.formulas) break; 
                        row.formulas = parsed; 
                    } catch (e) { row.formulas = {}; break; } 
                }
                
                if (row.formulas && row.formulas.__comments && row.formulas.__comments[field]) {
                    delete row.formulas.__comments[field];
                    
                    const td = document.querySelector(`td[data-id="${row.id}"][data-field="${field}"]`);
                    if (td) this.renderCellDisplay(td, field, row.id);
                    
                    this.queueSave(row.id, 'formulas', row.formulas);
                    deletedCount++;
                }
            }
        }
        
        if (deletedCount > 0) {
            this.updateStatusBar(`Berhasil menghapus komentar dari ${deletedCount} cell.`);
        }
    }

    showCommentDialog() {
        if (!this.activeCell) return;
        const td = this.activeCell;
        const id = td.dataset.id;
        const f = td.dataset.field;
        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
        if (!row) return;

        let existingComment = '';
        if (row.formulas && row.formulas.__comments && row.formulas.__comments[f]) {
            existingComment = row.formulas.__comments[f];
        }

        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0'; overlay.style.left = '0'; overlay.style.right = '0'; overlay.style.bottom = '0';
        overlay.style.background = 'rgba(0,0,0,0.4)';
        overlay.style.zIndex = '9999';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';

        const dialog = document.createElement('div');
        dialog.style.background = 'var(--bg-primary, #ffffff)';
        dialog.style.padding = '20px';
        dialog.style.borderRadius = '12px';
        dialog.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
        dialog.style.width = '350px';
        dialog.style.display = 'flex';
        dialog.style.flexDirection = 'column';
        dialog.style.gap = '15px';

        const title = document.createElement('h3');
        title.textContent = 'Tambahkan Komentar';
        title.style.margin = '0';
        title.style.fontSize = '1.1rem';
        title.style.color = 'var(--text-primary, #333)';

        const textarea = document.createElement('textarea');
        textarea.value = existingComment;
        textarea.placeholder = 'Ketik komentar di sini...';
        textarea.style.width = '100%';
        textarea.style.height = '100px';
        textarea.style.padding = '12px';
        textarea.style.border = '1px solid var(--border-color, #ccc)';
        textarea.style.borderRadius = '8px';
        textarea.style.resize = 'none';
        textarea.style.outline = 'none';
        textarea.style.background = 'var(--bg-secondary, #f8f9fa)';
        textarea.style.color = 'var(--text-primary, #333)';
        textarea.style.fontFamily = 'inherit';
        textarea.style.fontSize = '0.9rem';

        const btnContainer = document.createElement('div');
        btnContainer.style.display = 'flex';
        btnContainer.style.justifyContent = 'flex-end';
        btnContainer.style.gap = '10px';

        const btnCancel = document.createElement('button');
        btnCancel.textContent = 'Batal';
        btnCancel.style.padding = '8px 16px';
        btnCancel.style.border = '1px solid var(--border-color, #ccc)';
        btnCancel.style.background = 'transparent';
        btnCancel.style.color = 'var(--text-primary, #333)';
        btnCancel.style.borderRadius = '6px';
        btnCancel.style.cursor = 'pointer';
        btnCancel.style.fontWeight = '500';

        const btnSave = document.createElement('button');
        btnSave.textContent = 'Simpan';
        btnSave.style.padding = '8px 16px';
        btnSave.style.border = 'none';
        btnSave.style.background = 'var(--red, #CC0000)';
        btnSave.style.color = '#fff';
        btnSave.style.borderRadius = '6px';
        btnSave.style.cursor = 'pointer';
        btnSave.style.fontWeight = '500';

        const cleanup = () => {
            if (document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
        };

        btnCancel.onclick = cleanup;
        
        btnSave.onclick = () => {
            const newComment = textarea.value;
            while (row.formulas && typeof row.formulas === 'string') { try { let parsed = JSON.parse(row.formulas); if (typeof parsed === 'string' && parsed === row.formulas) break; row.formulas = parsed; } catch (e) { row.formulas = {}; break; } }
            if (!row.formulas) row.formulas = {};
            if (!row.formulas.__comments) row.formulas.__comments = {};
            if (newComment.trim() === '') {
                delete row.formulas.__comments[f];
            } else {
                row.formulas.__comments[f] = newComment.trim();
            }
            this.renderCellDisplay(td, f, id);
            this.queueSave(id, 'formulas', row.formulas);
            this.updateStatusBar('Komentar berhasil disimpan');
            cleanup();
        };

        btnContainer.appendChild(btnCancel);
        btnContainer.appendChild(btnSave);
        dialog.appendChild(title);
        dialog.appendChild(textarea);
        dialog.appendChild(btnContainer);
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        textarea.focus();
    }

    resetCellToAuto() {
        if (!this.activeCell) return;
        
        const targetCells = [];
        if (this.selectedRange.sr !== -1) {
            const { sr, er, sc, ec } = this.selectedRange;
            for (let r = sr; r <= er; r++) {
                const row = this.currentData[r];
                if (!row || String(row.id).startsWith('preload_')) continue;
                for (let c = sc; c <= ec; c++) {
                    const field = window.formulaEngine.colToField[c];
                    if (field && ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'].includes(field)) {
                        targetCells.push({ id: row.id, field });
                    }
                }
            }
        } else {
            targetCells.push({ id: this.activeCell.dataset.id, field: this.activeCell.dataset.field });
        }

        if (targetCells.length === 0) return;

        let lastField = '';
        targetCells.forEach(({ id, field }) => {
            const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
            if (!row) return;

            if (row.formulas) {
                if (typeof row.formulas === 'string') {
                    try { row.formulas = JSON.parse(row.formulas); } catch (e) { row.formulas = {}; }
                }
                delete row.formulas[field];
            }

            const updatedRow = window.calculationsManager.calculateRow(row);
            row[field] = updatedRow[field];

            if (field === 'penjualan' || field === 'total_biaya' || field === 'asuransi_jasindo') {
                const profitCfg = (this.sheetConfig && this.sheetConfig.profit) || { autoCalc: true };
                const idxProfitCfg = (this.sheetConfig && this.sheetConfig.idx_profit) || { autoCalc: true };

                if (profitCfg.autoCalc && (!row.formulas || !row.formulas.profit)) {
                    row.profit = window.formulaEngine.compute('profit', row, { template: profitCfg.template });
                }
                if (idxProfitCfg.autoCalc && (!row.formulas || !row.formulas.idx_profit)) {
                    row.idx_profit = row.penjualan === 0 ? 0 : (row.profit / row.penjualan);
                }
            }

            this.queueSave(id, field, row[field]);
            this.queueSave(id, 'formulas', row.formulas);

            const cellA1 = window.formulaEngine._mapCellIdToA1(`${id}:${field}`);
            if (cellA1) {
                window.formulaEngine.recalculateDependents(cellA1);
            }

            const dependents = ['profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'];
            dependents.forEach(depField => {
                const depTd = document.querySelector(`td[data-id="${id}"][data-field="${depField}"]`);
                if (depTd) {
                    this.queueSave(id, depField, row[depField]);
                }
            });
            lastField = field;
        });

        const td = this.activeCell;
        this.updateStatusBar(`✓ ${targetCells.length > 1 ? targetCells.length + ' Cell' : 'Kolom "' + lastField + '"'} telah dikembalikan ke otomatis.`);

        this._updateFormulaBar(td);
        this.renderTable(this.currentData);
    }

    setCellToManual() {
        if (!this.activeCell) return;
        
        const targetCells = [];
        if (this.selectedRange.sr !== -1) {
            const { sr, er, sc, ec } = this.selectedRange;
            for (let r = sr; r <= er; r++) {
                const row = this.currentData[r];
                if (!row || String(row.id).startsWith('preload_')) continue;
                for (let c = sc; c <= ec; c++) {
                    const field = window.formulaEngine.colToField[c];
                    if (field && ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'].includes(field)) {
                        targetCells.push({ id: row.id, field });
                    }
                }
            }
        } else {
            targetCells.push({ id: this.activeCell.dataset.id, field: this.activeCell.dataset.field });
        }

        if (targetCells.length === 0) return;

        let lastField = '';
        targetCells.forEach(({ id, field }) => {
            const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
            if (!row) return;

            while (row.formulas && typeof row.formulas === 'string') { try { let parsed = JSON.parse(row.formulas); if (typeof parsed === 'string' && parsed === row.formulas) break; row.formulas = parsed; } catch (e) { row.formulas = {}; break; } }
            if (!row.formulas) row.formulas = {};
            row.formulas[field] = ' ';

            this.queueSave(id, 'formulas', row.formulas);
            lastField = field;
        });

        const td = this.activeCell;
        this.updateStatusBar(`✓ ${targetCells.length > 1 ? targetCells.length + ' Cell' : 'Kolom "' + lastField + '"'} diubah ke manual.`);

        this._updateFormulaBar(td);

        // Langsung buka editor agar user bisa memasukkan rumus manual
        setTimeout(() => {
            this.startEditCell(td, false); // false = retain current calculated value
        }, 50);
        this.renderTable(this.currentData);
    }

    showColumnContextMenu(x, y) {
        if (!this.columnContextMenu) return;
        
        const f = this.selectedColumns.length ? this.getColumnField(this.selectedColumns[0]) : null;
        
        let html = '<div class="context-menu-item" data-action="sort-asc"><i class="fas fa-sort-amount-up"></i> Sortir A-Z</div>' +
                   '<div class="context-menu-item" data-action="sort-desc"><i class="fas fa-sort-amount-down"></i> Sortir Z-A</div>' +
                   '<div class="context-menu-item" data-action="sort-none"><i class="fas fa-sort"></i> Tanpa Sortir</div>' +
                   '<div class="context-menu-divider"></div>' +
                   '<div class="context-menu-item" data-action="col-copy"><i class="fas fa-copy"></i> Copy Kolom</div>' +
                   '<div class="context-menu-item" data-action="col-clear"><i class="fas fa-eraser"></i> Kosongkan Kolom</div>' +
                   '<div class="context-menu-divider"></div>' +
                   '<div class="context-menu-item" data-action="col-select-all"><i class="fas fa-columns"></i> Pilih Semua Kolom</div>';
                   
        if (f === 'tanggal_pickup') {
            html += '<div class="context-menu-divider"></div>' +
                    '<div class="context-menu-item text-blue-600 font-medium" data-action="col-date-swap"><i class="fas fa-exchange-alt text-blue-500"></i> Tukar Posisi Tanggal & Bulan</div>' +
                    '<div class="context-menu-item text-blue-600 font-medium" data-action="col-date-bulk"><i class="fas fa-calendar-alt text-blue-500"></i> Ubah Bulan/Tahun Serentak</div>' +
                    '<div class="context-menu-item text-blue-600 font-medium" data-action="col-date-clean"><i class="fas fa-magic text-blue-500"></i> Rapikan Format Tanggal</div>';
        }
        
        this.columnContextMenu.innerHTML = html;
        this.columnContextMenu.style.left = Math.min(x, innerWidth - 220) + 'px';
        this.columnContextMenu.style.top = Math.min(y, innerHeight - 280) + 'px';
        this.columnContextMenu.classList.add('show');
    }

    swapDateMonthFormats() {
        const { sr, er, sc, ec } = this.selectedRange;
        if (sr === -1 || sc === -1) return;
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Mode read-only.'); return; }
        
        const f = 'tanggal_pickup';
        const batch = [];
        let swappedCount = 0;
        
        for (let r = sr; r <= er; r++) {
            const row = this.currentData[r];
            if (!row || String(row.id).startsWith('preload_')) continue;
            
            const raw = row[f];
            if (raw && typeof raw === 'string') {
                const separator = raw.includes('-') ? '-' : raw.includes('/') ? '/' : null;
                if (separator) {
                    const parts = raw.split(separator).map(p => p.trim());
                    if (parts.length === 3) {
                        // Kalau formatnya YYYY-MM-DD, tukar MM dan DD menjadi YYYY-DD-MM
                        // Kalau DD-MM-YYYY, tukar menjadi MM-DD-YYYY
                        let newDateStr;
                        if (parts[0].length === 4) {
                            newDateStr = `${parts[0]}${separator}${parts[2]}${separator}${parts[1]}`;
                        } else {
                            newDateStr = `${parts[1]}${separator}${parts[0]}${separator}${parts[2]}`;
                        }

                        if (raw !== newDateStr) {
                            batch.push({ id: row.id, field: f, oldValue: raw, newValue: newDateStr });
                            row[f] = newDateStr;
                            this.queueSave(row.id, f, newDateStr);
                            swappedCount++;
                        }
                    }
                }
            }
        }
        
        if (batch.length) {
            this.history.push({ type: 'batch', actions: batch });
            this.renderTable(this.currentData);
            this.flushSaveQueue();
            window.showToast(`Berhasil menukar posisi tanggal & bulan pada ${swappedCount} baris.`, 'success');
        } else {
            window.showToast('Tidak ada format tanggal yang valid untuk ditukar pada seleksi ini.', 'error');
        }
    }

    cleanDateFormats() {
        const { sr, er, sc, ec } = this.selectedRange;
        if (sr === -1 || sc === -1) return;
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Mode read-only.'); return; }
        
        const f = 'tanggal_pickup';
        const batch = [];
        let cleanedCount = 0;
        
        for (let r = sr; r <= er; r++) {
            const row = this.currentData[r];
            if (!row || String(row.id).startsWith('preload_')) continue;
            
            const raw = row[f];
            if (raw) {
                const parsed = window.formulaEngine ? window.formulaEngine._parseDate(raw) : new Date(raw);
                if (parsed && !isNaN(parsed.getTime())) {
                    const y = parsed.getFullYear();
                    const m = String(parsed.getMonth() + 1).padStart(2, '0');
                    const d = String(parsed.getDate()).padStart(2, '0');
                    const stdDate = `${y}-${m}-${d}`;
                    
                    if (raw !== stdDate) {
                        batch.push({ id: row.id, field: f, oldValue: raw, newValue: stdDate });
                        row[f] = stdDate;
                        this.queueSave(row.id, f, stdDate);
                        cleanedCount++;
                    }
                }
            }
        }
        
        if (batch.length) {
            this.history.push({ type: 'batch', actions: batch });
            this.renderTable(this.currentData);
            this.flushSaveQueue();
            window.showToast(`Berhasil merapikan format pada ${cleanedCount} baris.`, 'success');
        } else {
            window.showToast('Semua tanggal sudah dalam format baku.', 'info');
        }
    }

    showBulkDateEditDialog() {
        const { sr, er, sc, ec } = this.selectedRange;
        if (sr === -1 || sc === -1) return;
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Mode read-only.'); return; }
        
        const currentMonth = new Date().getMonth() + 1;
        const currentYear = new Date().getFullYear();
        
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center p-4 backdrop-blur-sm';
        dialog.innerHTML = `
            <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden flex flex-col">
                <div class="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <h3 class="text-lg font-semibold text-gray-800"><i class="fas fa-calendar-alt text-blue-500 mr-2"></i>Ubah Bulan & Tahun</h3>
                    <button class="text-gray-400 hover:text-red-500 transition-colors" onclick="this.closest('.fixed').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-5 space-y-4">
                    <p class="text-sm text-gray-600 mb-2">Pilih bulan dan tahun baru untuk diterapkan pada <strong class="text-gray-800">${er - sr + 1} baris</strong> terpilih (Tanggal/Hari akan tetap dipertahankan):</p>
                    
                    <div>
                        <label class="block text-xs font-semibold text-gray-500 mb-1">Bulan Baru</label>
                        <select id="bulkDateMonth" class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none text-sm">
                            <option value="">-- Jangan Ubah --</option>
                            ${[...Array(12)].map((_, i) => '<option value="' + (i + 1) + '" ' + (i + 1 === currentMonth ? 'selected' : '') + '>' + new Date(2000, i, 1).toLocaleString('id-ID', {month: 'long'}) + '</option>').join('')}
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-semibold text-gray-500 mb-1">Tahun Baru</label>
                        <select id="bulkDateYear" class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none text-sm">
                            <option value="">-- Jangan Ubah --</option>
                            ${[...Array(10)].map((_, i) => '<option value="' + (currentYear - 2 + i) + '" ' + (currentYear - 2 + i === currentYear ? 'selected' : '') + '>' + (currentYear - 2 + i) + '</option>').join('')}
                        </select>
                    </div>
                </div>
                <div class="px-5 py-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-2">
                    <button class="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" onclick="this.closest('.fixed').remove()">Batal</button>
                    <button id="btnApplyBulkDate" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors">
                        Terapkan Perubahan
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(dialog);
        
        document.getElementById('btnApplyBulkDate').addEventListener('click', () => {
            const mRaw = document.getElementById('bulkDateMonth').value;
            const yRaw = document.getElementById('bulkDateYear').value;
            dialog.remove();
            
            if (!mRaw && !yRaw) return;
            
            const targetM = mRaw ? parseInt(mRaw) : null;
            const targetY = yRaw ? parseInt(yRaw) : null;
            
            const f = 'tanggal_pickup';
            const batch = [];
            let changedCount = 0;
            
            for (let r = sr; r <= er; r++) {
                const row = this.currentData[r];
                if (!row || String(row.id).startsWith('preload_')) continue;
                
                const raw = row[f];
                if (raw) {
                    const parsed = window.formulaEngine ? window.formulaEngine._parseDate(raw) : new Date(raw);
                    if (parsed && !isNaN(parsed.getTime())) {
                        let y = parsed.getFullYear();
                        let m = parsed.getMonth() + 1;
                        let d = parsed.getDate();
                        
                        if (targetY !== null) y = targetY;
                        if (targetM !== null) m = targetM;
                        
                        const newDateObj = new Date(y, m - 1, d);
                        const finalY = newDateObj.getFullYear();
                        const finalM = String(newDateObj.getMonth() + 1).padStart(2, '0');
                        const finalD = String(newDateObj.getDate()).padStart(2, '0');
                        
                        const stdDate = `${finalY}-${finalM}-${finalD}`;
                        
                        if (raw !== stdDate) {
                            batch.push({ id: row.id, field: f, oldValue: raw, newValue: stdDate });
                            row[f] = stdDate;
                            this.queueSave(row.id, f, stdDate);
                            changedCount++;
                        }
                    }
                }
            }
            
            if (batch.length) {
                this.history.push({ type: 'batch', actions: batch });
                this.renderTable(this.currentData);
                this.flushSaveQueue();
                window.showToast(`Berhasil mengubah bulan/tahun untuk ${changedCount} baris.`, 'success');
            } else {
                window.showToast('Tidak ada perubahan yang dilakukan.', 'info');
            }
        });
    }

    selectColumn(ci) {
        this.clearSelection();
        this.clearColumnSelection();
        this.selectedColumns = [ci];

        const ths = document.querySelectorAll('#kpiTable thead th');
        if (ths[ci]) ths[ci].classList.add('col-selected');

        // Update range for bulk operations
        this.selectedRange = {
            sr: 0,
            er: this.currentData.length - 1,
            sc: ci,
            ec: ci
        };
        this.activeCellPos = { r: 0, c: ci };
        this._updateSelectionUI();
    }

    selectColumnRange(s, e) {
        this.clearSelection();
        this.clearColumnSelection();
        const mn = Math.min(s, e), mx = Math.max(s, e);
        this.selectedColumns = [];

        const ths = document.querySelectorAll('#kpiTable thead th');
        for (let i = mn; i <= mx; i++) {
            this.selectedColumns.push(i);
            if (ths[i]) ths[i].classList.add('col-selected');
        }

        // Update range for bulk operations
        this.selectedRange = {
            sr: 0,
            er: this.currentData.length - 1,
            sc: mn,
            ec: mx
        };
        this.activeCellPos = { r: 0, c: mn };
        this._updateSelectionUI();
    }

    selectAllColumns() {
        this.clearSelection();
        this.clearColumnSelection();

        const ths = document.querySelectorAll('#kpiTable thead th');
        const numDataCols = window.formulaEngine.colToField.length - 1;

        this.selectedColumns = [];
        for (let i = 1; i <= numDataCols; i++) {
            this.selectedColumns.push(i);
            if (ths[i]) ths[i].classList.add('col-selected');
        }

        this.selectedRange = {
            sr: 0,
            er: this.currentData.length - 1,
            sc: 1,
            ec: numDataCols
        };
        this.activeCellPos = { r: 0, c: 1 };
        this._updateSelectionUI();

        this.updateStatusBar('Seluruh lembar kerja dipilih');
    }

    clearColumnSelection() {
        document.querySelectorAll('#kpiTable thead th.col-selected').forEach(th => th.classList.remove('col-selected'));
        this.selectedColumns = [];
    }

    clearColumns() {
        const { sr, er, sc, ec } = this.selectedRange;
        if (sr === -1 || sc === -1) return;
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Mode read-only.'); return; }

        const batch = [], ai = new Set();
        const totalRows = er - sr + 1;
        const totalCols = ec - sc + 1;
        
        if ((totalRows * totalCols) > 50) showToast(`Mengosongkan kolom...`, 'info');

        for (let r = sr; r <= er; r++) {
            const row = this.currentData[r];
            if (!row || String(row.id).startsWith('preload_')) continue;

            for (let c = sc; c <= ec; c++) {
                const f = window.formulaEngine.colToField[c];
                if (!f || !this.isColEditable(f)) continue;

                const ov = this.getRawValue(row.id, f);
                const nv = this.getFieldType(f) === 'number' ? 0 : (f === 'tanggal_pickup' ? null : '');
                
                batch.push({ id: row.id, field: f, oldValue: ov, newValue: nv });
                this.updateCellValue(row.id, f, nv);
                
                // Update DOM if rendered
                const tr = document.querySelector(`#kpiTableBody tr[data-idx="${r}"]`);
                if (tr) {
                    const td = tr.cells[c];
                    if (td) this.renderCellDisplay(td, f, row.id);
                }
                
                this.queueSave(row.id, f, nv);
                ai.add(row.id);
            }
        }

        if (batch.length) { this.history.push({ type: 'batch', actions: batch }); }
        ai.forEach(id => this.updateRelatedCells(id));
        this.flushSaveQueue();
        this.updateStatusBar(this.selectedColumns.length + ' kolom dikosongkan');
    }

    sortByColumn(field, direction) {
        if (!field || !direction) {
            this.columnSortState = { field: null, direction: null };
            this.currentData = [...this.originalData];
            this.renderTable(this.currentData);
            this.updateSortIndicators();
            this.updateStatusBar('Sortir direset');
            return;
        }
        if (this.columnSortState.field === field) {
            if (this.columnSortState.direction === 'asc') direction = 'desc';
            else {
                this.columnSortState = { field: null, direction: null };
                this.currentData = [...this.originalData];
                this.renderTable(this.currentData);
                this.updateSortIndicators();
                this.updateStatusBar('Sortir direset');
                return;
            }
        }
        this.columnSortState = { field, direction };
        this.currentData.sort((a, b) => {
            let va = a[field], vb = b[field];
            if (va == null) va = '';
            if (vb == null) vb = '';
            if (this.getFieldType(field) === 'number') {
                va = parseFloat(va) || 0;
                vb = parseFloat(vb) || 0;
                return direction === 'asc' ? va - vb : vb - va;
            }
            va = String(va).toLowerCase();
            vb = String(vb).toLowerCase();
            if (va < vb) return direction === 'asc' ? -1 : 1;
            if (va > vb) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        this.renderTable(this.currentData);
        this.updateSortIndicators();
        this.updateStatusBar('Sortir ' + field + ' ' + (direction === 'asc' ? 'A-Z' : 'Z-A'));
    }

    updateSortIndicators() {
        document.querySelectorAll('#kpiTable thead th .sort-indicator').forEach(el => el.remove());
        document.querySelectorAll('#kpiTable thead th[data-field]').forEach(th => {
            const s = document.createElement('span');
            s.className = 'sort-indicator';
            if (th.dataset.field === this.columnSortState.field) {
                s.classList.add('active');
                s.innerHTML = this.columnSortState.direction === 'asc' ? '<i class="fas fa-caret-up"></i>' : '<i class="fas fa-caret-down"></i>';
            } else {
                s.innerHTML = '<i class="fas fa-sort" style="opacity:0.3;"></i>';
            }
            th.appendChild(s);
        });

        this.updateHeaderIndicators();
    }

    updateHeaderIndicators() {
        document.querySelectorAll('#kpiTable thead th .autocalc-indicator').forEach(el => el.remove());

        const config = this.sheetConfig || {};

        // concept per sheet: dynamic highlight of toolbar calculator button based on active configs
        const btn = document.querySelector('[data-action="auto-calc-config"]');
        const hasActiveConfig = this.sheetConfigRow && Object.keys(config).length > 0 &&
            Object.values(config).some(val => val && val.autoCalc === true);

        if (btn) {
            if (hasActiveConfig) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }

        const shieldBtn = document.getElementById('btnFormulaProtect');
        if (shieldBtn) {
            const isProtected = config.formulaProtectionEnabled === true;
            if (isProtected) {
                shieldBtn.classList.add('active');
                shieldBtn.innerHTML = '<i class="fas fa-shield-alt" style="color: #16a34a;"></i>';
                shieldBtn.title = 'Perlindungan Rumus: ON (Cegah hapus/timpa tak sengaja)';
            } else {
                shieldBtn.classList.remove('active');
                shieldBtn.innerHTML = '<i class="fas fa-shield-alt"></i>';
                shieldBtn.title = 'Perlindungan Rumus: OFF (Hati-hati saat hapus massal)';
            }
        }
    }

    // ==================== FIND & REPLACE ====================

    openFind() {
        const b = document.getElementById('findBar');
        if (!b) return;
        b.style.display = 'block';
        const i = document.getElementById('findInput');
        if (i) { i.focus(); i.select(); }
    }

    closeFind() {
        const b = document.getElementById('findBar');
        if (b) b.style.display = 'none';
        this.clearFindHighlights();
        this.findState = { query: '', matches: [], currentIdx: -1, showReplace: false };
        const rg = document.getElementById('replaceGroup');
        if (rg) rg.style.display = 'none';
    }

    toggleReplace() {
        this.findState.showReplace = !this.findState.showReplace;
        const rg = document.getElementById('replaceGroup'), btn = document.getElementById('toggleReplaceBtn');
        if (rg) rg.style.display = this.findState.showReplace ? 'flex' : 'none';
        if (btn) btn.style.color = this.findState.showReplace ? 'var(--red)' : '';
    }

    executeFind() {
        const input = document.getElementById('findInput');
        if (!input) return;
        const q = input.value.trim().toLowerCase();
        this.findState.query = q;
        this.clearFindHighlights();
        if (!q) { this.updateFindCount(0, 0); return; }
        this.findState.matches = [];
        const tbody = document.getElementById('kpiTableBody');
        if (!tbody) return;
        Array.from(tbody.rows).forEach(tr => {
            Array.from(tr.children).forEach(td => {
                if (td.classList.contains('col-index') || td.classList.contains('col-actions')) return;
                const d = td.querySelector('.cell-display');
                if (d && d.textContent.toLowerCase().includes(q)) this.findState.matches.push(td);
            });
        });
        this.findState.matches.forEach(td => td.classList.add('cell-find-match'));
        if (this.findState.matches.length > 0) { this.findState.currentIdx = 0; this.navigateToMatch(); }
        else { this.findState.currentIdx = -1; }
        this.updateFindCount(this.findState.currentIdx + 1, this.findState.matches.length);
    }

    findNext() {
        if (!this.findState.matches.length) { this.executeFind(); return; }
        this.findState.currentIdx = (this.findState.currentIdx + 1) % this.findState.matches.length;
        this.navigateToMatch();
        this.updateFindCount(this.findState.currentIdx + 1, this.findState.matches.length);
    }

    findPrev() {
        if (!this.findState.matches.length) { this.executeFind(); return; }
        this.findState.currentIdx = (this.findState.currentIdx - 1 + this.findState.matches.length) % this.findState.matches.length;
        this.navigateToMatch();
        this.updateFindCount(this.findState.currentIdx + 1, this.findState.matches.length);
    }

    navigateToMatch() {
        document.querySelectorAll('.cell-find-current').forEach(el => el.classList.remove('cell-find-current'));
        const td = this.findState.matches[this.findState.currentIdx];
        if (td) {
            td.classList.add('cell-find-current');
            td.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
            if (td.dataset.id && !td.dataset.id.startsWith('preload_')) this.showLastEditInfo(td.dataset.id);
        }
    }

    clearFindHighlights() {
        document.querySelectorAll('.cell-find-match,.cell-find-current').forEach(el => {
            el.classList.remove('cell-find-match', 'cell-find-current');
        });
    }

    updateFindCount(c, t) {
        const el = document.getElementById('findCount');
        if (el) el.textContent = t > 0 ? c + '/' + t : '0/0';
    }

    replaceOne() {
        if (!this.findState.matches.length || this.findState.currentIdx < 0) return;
        const rv = document.getElementById('replaceInput')?.value || '';
        const td = this.findState.matches[this.findState.currentIdx];
        if (!td) return;
        const id = td.dataset.id, f = td.dataset.field;
        if (id && f) {
            if (!this.isColEditable(f)) return;
            if (id.startsWith('preload_')) return;
            const ov = this.getRawValue(id, f);
            let nv = String(ov || '');
            const idx = nv.toLowerCase().indexOf(this.findState.query);
            if (idx >= 0) {
                nv = nv.substring(0, idx) + rv + nv.substring(idx + this.findState.query.length);
                if (this.getFieldType(f) === 'number') nv = parseFloat(nv) || 0;
                else if (f === 'tanggal_pickup') nv = rv;
                this.history.push({ type: 'batch', actions: [{ id, field: f, oldValue: ov, newValue: nv }] });

                this.updateCellValue(id, f, nv);
                this.renderCellDisplay(td, f, id);
                this.updateRelatedCells(id);
                this.directSave(id, f, nv);
                this.executeFind();
            }
        }
    }

    replaceAll() {
        if (!this.findState.matches.length) return;
        const rv = document.getElementById('replaceInput')?.value || '';
        const batch = [];
        this.findState.matches.forEach(td => {
            const id = td.dataset.id, f = td.dataset.field;
            if (id && f) {
                if (!this.isColEditable(f)) return;
                if (id.startsWith('preload_')) return;
                const ov = this.getRawValue(id, f);
                let nv = String(ov || '');
                const idx = nv.toLowerCase().indexOf(this.findState.query);
                if (idx >= 0) {
                    nv = nv.substring(0, idx) + rv + nv.substring(idx + this.findState.query.length);
                    if (this.getFieldType(f) === 'number') nv = parseFloat(nv) || 0;
                    else if (f === 'tanggal_pickup') nv = rv;
                    batch.push({ id, field: f, oldValue: ov, newValue: nv });
                    this.updateCellValue(id, f, nv);
                    this.renderCellDisplay(td, f, id);
                    this.queueSave(id, f, nv);
                }
            }
        });
        if (batch.length) { this.history.push({ type: 'batch', actions: batch }); }
        [...new Set(batch.map(a => a.id))].forEach(id => this.updateRelatedCells(id));
        this.flushSaveQueue();
        this.executeFind();
        this.updateStatusBar(batch.length + ' cell diganti');
    }



    // ==================== PRELOAD 100 ROWS ====================

    /**
     * @param {number} count - Jumlah baris
     * @param {'fill'|'add'} mode - 'fill' = isi sampai total count, 'add' = tambah count baris baru
     */
    async preloadEmptyRows(count = 1000, mode = 'fill') {
        if (this.isPreloading) {
            console.log('⚠ Already preloading, skip');
            return;
        }
        if (this.isReadOnlyUser()) {
            console.log('⚠ Read-only user, skip preload');
            return;
        }

        const existingCount = this.currentData.length;
        const needRows = mode === 'add' ? count : Math.max(0, count - existingCount);

        console.log('📊 Existing:', existingCount, '| Mode:', mode, '| Need:', needRows);

        if (needRows <= 0) {
            console.log('✅ Already have enough rows');
            return;
        }

        this.isPreloading = true;
        this._updateLoadMoreButton(); // Immediately show loading state on button
        const label = mode === 'add'
            ? '⏳ Menambahkan ' + count + ' baris baru...'
            : '⏳ Menyiapkan ' + needRows + ' baris...';
        this.updateStatusBar(label);

        try {

            this.setSyncStatus('syncing');

            const rowsToInsert = [];
            for (let i = 0; i < needRows; i++) {
                rowsToInsert.push({
                    nama: '', tanggal_pickup: null, service: '', via: '', asal_pickup: '', tujuan: '',
                    jenis_barang: '', nilai_barang: null, awb: '', awb_sistem: '', pengirim: '', sales: '',
                    penerima: '', penjualan: null, nama_vendor: '', nama_vendor_ii: '', nama_vendor_iii: '', nama_vendor_iv: '',
                    vendor_i: null, vendor_ii: null,
                    vendor_iii: null, vendor_iv: null, ops: null, asuransi: null, asuransi_jasindo: null,
                    aktual: null, vol: null, unit: null, kubik: null, p: null, l: null, t: null, koil: null,
                    harga: null, surcharge: null, packing: null, handling: null,
                    total_biaya: null, profit: null, idx_profit: null,
                    sheet_id: window.activeSheetId
                });
            }

            let allNewRows = [];
            try {
                allNewRows = await window.databaseManager.insertRowsBulk(rowsToInsert);
                console.log('✅ Bulk insert success:', allNewRows.length, 'rows created.');
            } catch (e) {
                console.error('❌ Gagal bulk insert:', e.message);
                throw e; // Rethrow to let the main catch handle status bar updates
            }

            console.log('📊 Total new rows:', allNewRows.length);

            this.currentData.push(...allNewRows);
            this.originalData.push(...allNewRows);

            this.renderTable(this.currentData);

            this.setSyncStatus('synced');
            const msg = mode === 'add'
                ? '✓ ' + allNewRows.length + ' baris baru ditambahkan (total: ' + this.currentData.length + ')'
                : '✓ ' + this.currentData.length + ' baris siap diedit';
            this.updateStatusBar(msg);
            console.log('✅ Preload complete! Total rows:', this.currentData.length);

        } catch (e) {
            console.error('❌ Preload error:', e);
            this.setSyncStatus('error');
            this.updateStatusBar('⚠ Gagal menyiapkan baris: ' + e.message);
            window.showToast('Gagal menyiapkan baris: ' + e.message, 'error');
        } finally {
            this.isPreloading = false;
            this._updateLoadMoreButton(); // Always reset button state when done
        }
    }

    loadMoreRows() {
        this.preloadEmptyRows(100, 'add');
    }

    /** Update load-more button state without full table re-render */
    _updateLoadMoreButton() {
        const btn = document.getElementById('btnLoadMore');
        if (!btn) return;
        btn.style.display = this.isReadOnlyUser() ? 'none' : 'inline-flex';
        btn.disabled = this.isPreloading;
        btn.innerHTML = this.isPreloading
            ? '<i class="fas fa-spinner fa-spin"></i> Menambahkan...'
            : '<i class="fas fa-plus"></i> Tambah 1000 Baris Lagi';
    }

    // ==================== RENDER TABLE ====================

    /**
     * Mempersiapkan data untuk Virtual Scroller dan membangun Hash Map O(1)
     * @param {Array} data - Array object data kpi_finance
     */
    renderTable(data) {
        // Check if this is a fresh load from the database before modifying this.currentData
        const isFreshLoad = (data && data !== this.currentData);

        if (!this.originalData.length || this.columnSortState.field === null) this.originalData = [...(data || [])];
        this.currentData = data || [];

        this.currentData = this.currentData.filter(Boolean);
        this.originalData = this.originalData.filter(Boolean);
        
        // PENTING: Urutkan agar baris kosong selalu berada di bawah baris yang memiliki data.
        // Ini memastikan data CRM yang masuk belakangan tidak tersembunyi di bawah 1000 baris kosong!
        const sortEmptyToBottom = (a, b) => {
            const aEmpty = !a.nama && !a.tanggal_pickup;
            const bEmpty = !b.nama && !b.tanggal_pickup;
            if (aEmpty && !bEmpty) return 1;
            if (!aEmpty && bEmpty) return -1;
            return a.id - b.id; // Pertahankan urutan ID asli jika sama-sama kosong/berisi
        };
        
        this.currentData.sort(sortEmptyToBottom);
        this.originalData.sort(sortEmptyToBottom);

        // Ensure map is updated so Audit Log can map UUID back to visual row
        this._initRowMap();

        // Reset config only if it's a fresh load from the database
        if (isFreshLoad) {
            this.sheetConfigRow = null;
            this.sheetConfig = null;
        }

        // Setup/Extract __SHEET_CONFIG__ metadata row if present
        let sheetConfigRow = this.currentData.find(r => r && r.nama === '__SHEET_CONFIG__');
        if (!sheetConfigRow && this.originalData) {
            sheetConfigRow = this.originalData.find(r => r && r.nama === '__SHEET_CONFIG__');
        }

        if (sheetConfigRow) {
            this.sheetConfigRow = sheetConfigRow;
            let formulasObj = sheetConfigRow.formulas;
            if (formulasObj) {
                if (typeof formulasObj === 'string') {
                    try {
                        formulasObj = JSON.parse(formulasObj);
                    } catch (e) {
                        console.error('Failed to parse sheet config formulas:', e);
                        formulasObj = null;
                    }
                }
                if (formulasObj && typeof formulasObj === 'object') {
                    this.sheetConfig = formulasObj;
                }
            }
        }
        // If no config row found AND no existing sheetConfig, initialize empty
        if (!this.sheetConfigRow && !this.sheetConfig) {
            this.sheetConfig = {};
        }

        // Filter out the sheet config row from presentation data
        this.currentData = this.currentData.filter(r => r && r.nama !== '__SHEET_CONFIG__');
        if (this.originalData) {
            this.originalData = this.originalData.filter(r => r && r.nama !== '__SHEET_CONFIG__');
        }

        // Auto database self-healing cleanup: permanently clear stale numeric values in blank rows
        this.currentData.forEach(row => {
            if (row && row.id && !String(row.id).startsWith('preload_')) {
                if (!row.nama && !row.tanggal_pickup && !row.awb && !row.awb_sistem && !row.pengirim && !row.penerima && !row.sales && !row.jenis_barang && !row.tujuan && !row.nama_vendor) {
                    // Skip cleanup if the row has any formulas defined (e.g. subtotal row)
                    let parsedFormulas = row.formulas;
                    if (typeof parsedFormulas === 'string') {
                        try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
                    }
                    const hasFormulas = parsedFormulas && Object.values(parsedFormulas).some(v => typeof v === 'string' && (v.startsWith('=') || v === ' '));
                    if (hasFormulas) return;

                    const fieldsToClear = ['penjualan', 'total_biaya', 'profit', 'asuransi', 'asuransi_jasindo', 'nilai_barang', 'harga', 'surcharge', 'packing', 'handling', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops'];
                    let needsSave = false;
                    const updates = {};

                    fieldsToClear.forEach(f => {
                        if (row[f] !== null && row[f] !== 0 && row[f] !== undefined && row[f] !== '') {
                            row[f] = null;
                            updates[f] = null;
                            needsSave = true;
                        }
                    });

                    if (needsSave) {
                        console.log(`[AutoCleanup] Permanent clean-up of stale values in blank database row ${row.id}`, updates);
                        window.databaseManager.updateRow(row.id, updates).catch(err => {
                            console.error(`Failed to auto-clean blank row ${row.id}:`, err);
                        });
                    }
                }
            }
        });

        // Build O(1) Lookup Map for performance
        this.rowMap = new Map();
        this.currentData.forEach((row, i) => {
            if (row && row.id) {
                row._idx = i; // Store index for O(1) A1 mapping
                this.rowMap.set(String(row.id), row);
            }
        });

        // Initialize formula engine with current data state
        if (window.formulaEngine) {
            window.formulaEngine.rowMap = this.rowMap;
        }
        this._initializeFormulas();

        const tbody = document.getElementById('kpiTableBody');
        if (!tbody) return;

        const realCount = this.currentData.length;
        document.getElementById('rowCount').textContent = realCount + ' baris data';

        if (realCount === 0) {
            if (this.virtualScroller) {
                this.virtualScroller.setData([]);
            }
            if (!this.isReadOnlyUser()) {
                if (!this.isPreloading) {
                    // Auto preload 1000 rows
                    this.preloadEmptyRows(1000, 'fill');
                }
                tbody.innerHTML = `
                <tr>
                    <td colspan="38" style="text-align:center; padding: 60px 20px;">
                        <i class="fas fa-spinner fa-spin" style="font-size: 3rem; margin-bottom: 16px; color: var(--red);"></i>
                        <h3 style="margin-bottom: 8px; color: var(--text-primary);">Menyiapkan Lembar Kerja...</h3>
                        <p style="color: var(--text-muted);">Mohon tunggu, sedang menyiapkan 1000 baris untuk Anda.</p>
                    </td>
                </tr>
                `;
            } else {
                tbody.innerHTML = `
                <tr>
                    <td colspan="38" style="text-align:center; padding: 60px 20px;">
                        <div style="font-size: 3rem; margin-bottom: 16px;">📋</div>
                        <h3 style="margin-bottom: 8px; color: var(--text-primary);">Belum Ada Data</h3>
                        <p style="color: var(--text-muted); margin-bottom: 20px;">Sheet kosong dan Anda dalam mode Read-Only.</p>
                    </td>
                </tr>
                `;
            }

            const btn = document.getElementById('btnLoadMore');
            if (btn) btn.style.display = 'none';
            return;
        } else {
            // Auto-pad agar selalu memiliki setidaknya 1000 baris (terlihat infinite seperti sheet lainnya)
            if (realCount < 1000 && !this.isReadOnlyUser() && !this.isPreloading) {
                this.preloadEmptyRows(1000 - realCount, 'add');
            }
        }

        if (!this.virtualScroller) {
            this.virtualScroller = new VirtualScroller(
                document.querySelector('.spreadsheet-container'),
                tbody,
                this
            );
        }

        this.autoFitColumns();

        this.virtualScroller.setData(this.currentData);
        this.updateSortIndicators();
        this._updateLoadMoreButton();
        this.updateMissingDateWarning();

        // Default selection: select A1 if nothing is selected
        if (!this.activeCellPos || this.activeCellPos.r === -1) {
            setTimeout(() => {
                const firstTd = tbody.querySelector('td[data-field="tanggal_pickup"]');
                if (firstTd) {
                    this.selectCell(firstTd);
                }
            }, 150);
        }
    }

    // Helper to measure text width accurately using Canvas
    _getTextWidth(text, font) {
        if (!this.canvasContext) {
            const canvas = document.createElement("canvas");
            this.canvasContext = canvas.getContext("2d");
        }
        this.canvasContext.font = font || "13px Inter, sans-serif";
        return this.canvasContext.measureText(String(text)).width;
    }

    autoFitColumns(specificField = null) {
        if (!this.currentData || !this.currentData.length) return;
        const colWidths = {};
        const fields = [];
        
        // Get font from the first cell for accurate measurement
        const sampleCell = document.querySelector('#kpiTable tbody td');
        const font = sampleCell ? window.getComputedStyle(sampleCell).font : "13px Inter, sans-serif";
        
        document.querySelectorAll('#kpiTable thead th[data-field]').forEach(th => {
            const field = th.dataset.field;
            if (specificField && field !== specificField) return;
            fields.push(field);
            
            // Calculate width needed for the header text itself
            const headerText = th.textContent.trim();
            const headerWidth = this._getTextWidth(headerText, window.getComputedStyle(th).font || "bold 13px Inter") + 45; // 45px padding + sort icon
            
            if (!th.dataset.defaultWidth) {
                th.dataset.defaultWidth = th.style.minWidth ? parseInt(th.style.minWidth) : 100;
            }
            
            // Base width is the max of default HTML min-width and header text width
            colWidths[field] = Math.max(parseInt(th.dataset.defaultWidth), headerWidth); 
        });

        const maxCheck = Math.min(this.currentData.length, 5000);
        for (let i = 0; i < maxCheck; i++) {
            const row = this.currentData[i];
            if (!row || String(row.id).startsWith('preload_')) continue;
            for (const field of fields) {
                let val = this._fmt(row, field) || '';
                // Handle HTML content if the value is an object or formatted
                if (typeof val === 'string' && val.includes('<')) {
                    const temp = document.createElement('div');
                    temp.innerHTML = val;
                    val = temp.textContent;
                }
                if (val && colWidths[field] !== undefined) {
                    // Accurate width: Canvas measure + 32px padding/borders
                    const estWidth = this._getTextWidth(val, font) + 32; 
                    if (estWidth > colWidths[field]) {
                        colWidths[field] = estWidth;
                    }
                }
            }
        }

        document.querySelectorAll('#kpiTable thead th[data-field]').forEach(th => {
            const field = th.dataset.field;
            if (colWidths[field]) {
                const w = Math.min(800, Math.ceil(colWidths[field])) + 'px'; // Max width cap 800px
                th.style.minWidth = w;
                th.style.width = w;
                th.style.maxWidth = w;
                if (this.colWidths) this.colWidths[field] = w;
            }
        });
    }

    updateMissingDateWarning() {
        requestAnimationFrame(() => {
            // Only check core transaction identifiers. If all these are empty, 
            // it's likely a footer/subtotal row or a blank row, which doesn't need a date.
            const coreFieldsToCheck = [
                'nama', 'awb', 'pengirim', 'penerima', 'tujuan', 'asal_pickup', 'nama_vendor', 'sales', 'service', 'via', 'jenis_barang',
                'aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil', 'harga', 'surcharge', 'packing', 'handling', 
                'profit', 'total_biaya', 'asuransi', 'asuransi_jasindo', 'nilai_barang', 'ops', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv'
            ];

            const missingRows = [];

            this.currentData.forEach((row, idx) => {
                if (row && row.id && !String(row.id).startsWith('preload_')) {
                    let hasData = false;
                    for (const key of coreFieldsToCheck) {
                        const val = row[key];
                        if (val !== null && val !== undefined && String(val).trim() !== '' && val !== 0 && val !== '0') {
                            hasData = true;
                            break;
                        }
                    }

                    const isMissing = hasData && !row.tanggal_pickup;
                    if (isMissing) {
                        missingRows.push(idx + 1);
                    }
                }
            });

            let warnEl = document.getElementById('worksheetDateWarning');
            if (missingRows.length > 0) {
                if (!warnEl) {
                    warnEl = document.createElement('div');
                    warnEl.id = 'worksheetDateWarning';
                    // Smaller, compact, hovering on bottom right of the spreadsheet container to be less annoying
                    warnEl.className = 'worksheet-date-warning';
                    const parent = document.querySelector('.header-actions-group');
                    if (parent) {
                        parent.insertBefore(warnEl, parent.firstChild);
                    }
                }

                const limit = 3;
                const rowStr = missingRows.slice(0, limit).map(r => `#${r}`).join(', ');
                const moreStr = missingRows.length > limit ? ` & ${missingRows.length - limit} lain` : '';
                warnEl.innerHTML = `<i class="fas fa-exclamation-triangle warning-icon"></i><span class="warning-text"><b>Tgl Pickup Kosong:</b> Baris ${rowStr}${moreStr}</span><i class="fas fa-times warning-close" onclick="this.parentElement.style.display='none'; event.stopPropagation();"></i>`;
                warnEl.style.display = 'flex';
            } else if (warnEl) {
                warnEl.style.display = 'none';
            }
        });
    }

    createRowHTML(row, idx) {
        const rn = idx + 1;
        const id = row ? row.id : `preload_${Date.now()}_${idx}`;

        const profit = row ? (row.profit || 0) : 0;

        // CRM badge & status indicator
        const isCrm = row && row.source === 'crm';
        const rowStatus = row ? (row.row_status || 'completed') : 'completed';
        const statusClass = isCrm && rowStatus !== 'completed' ? ` crm-status-${rowStatus}` : '';
        const crmBadge = isCrm ? '<span class="crm-badge" title="Data dari CRM (Lead ' + (row.crm_lead_id || '') + ')">CRM</span>' : '';
        const statusDot = isCrm && rowStatus !== 'completed' ? '<span class="crm-status-dot crm-dot-' + rowStatus + '" title="' + this._getStatusLabel(rowStatus) + '"></span>' : '';

        return '<tr data-id="' + id + '" data-row="' + rn + '" data-idx="' + idx + '" class="spreadsheet-row' + statusClass + '" id="row-' + id + '">'
            + '<td class="col-index">' + statusDot + rn + crmBadge + '</td>'
            + this._td(id, 'tanggal_pickup', this._fmt(row, 'tanggal_pickup'), 'cell-date', idx, 1)
            + this._td(id, 'nama', this._fmt(row, 'nama'), '', idx, 2)
            + this._td(id, 'awb', this._fmt(row, 'awb'), '', idx, 3)
            + this._td(id, 'awb_sistem', this._fmt(row, 'awb_sistem'), '', idx, 4)
            + this._td(id, 'pengirim', this._fmt(row, 'pengirim'), '', idx, 5)
            + this._td(id, 'sales', this._fmt(row, 'sales'), '', idx, 6)
            + this._td(id, 'penerima', this._fmt(row, 'penerima'), '', idx, 7)
            + this._td(id, 'service', this._fmt(row, 'service'), '', idx, 8)
            + this._td(id, 'via', this._fmt(row, 'via'), '', idx, 9)
            + this._td(id, 'aktual', this._fmt(row, 'aktual'), 'cell-number', idx, 10)
            + this._td(id, 'vol', this._fmt(row, 'vol'), 'cell-number', idx, 11)
            + this._td(id, 'unit', this._fmt(row, 'unit'), 'cell-number', idx, 12)
            + this._td(id, 'kubik', this._fmt(row, 'kubik'), 'cell-number', idx, 13)

            + this._td(id, 'p', this._fmt(row, 'p'), 'cell-number', idx, 14)
            + this._td(id, 'l', this._fmt(row, 'l'), 'cell-number', idx, 15)
            + this._td(id, 't', this._fmt(row, 't'), 'cell-number', idx, 16)
            + this._td(id, 'koil', this._fmt(row, 'koil'), 'cell-number', idx, 17)
            + this._td(id, 'harga', this._fmt(row, 'harga'), 'cell-currency', idx, 18)
            + this._td(id, 'surcharge', this._fmt(row, 'surcharge'), 'cell-currency', idx, 19)
            + this._td(id, 'packing', this._fmt(row, 'packing'), 'cell-currency', idx, 20)
            + this._td(id, 'handling', this._fmt(row, 'handling'), 'cell-currency', idx, 21)
            + this._td(id, 'penjualan', this._fmt(row, 'penjualan'), 'cell-currency', idx, 22)
            + this._td(id, 'asal_pickup', this._fmt(row, 'asal_pickup'), '', idx, 23)
            + this._td(id, 'jenis_barang', this._fmt(row, 'jenis_barang'), '', idx, 24)
            + this._td(id, 'tujuan', this._fmt(row, 'tujuan'), '', idx, 25)
            + this._td(id, 'nama_vendor', this._fmt(row, 'nama_vendor'), '', idx, 26)
            + this._td(id, 'nama_vendor_ii', this._fmt(row, 'nama_vendor_ii'), '', idx, 27)
            + this._td(id, 'nama_vendor_iii', this._fmt(row, 'nama_vendor_iii'), '', idx, 28)
            + this._td(id, 'nama_vendor_iv', this._fmt(row, 'nama_vendor_iv'), '', idx, 29)
            + this._td(id, 'vendor_i', this._fmt(row, 'vendor_i'), 'cell-currency', idx, 30)
            + this._td(id, 'vendor_ii', this._fmt(row, 'vendor_ii'), 'cell-currency', idx, 31)
            + this._td(id, 'vendor_iii', this._fmt(row, 'vendor_iii'), 'cell-currency', idx, 32)
            + this._td(id, 'vendor_iv', this._fmt(row, 'vendor_iv'), 'cell-currency', idx, 33)
            + this._td(id, 'ops', this._fmt(row, 'ops'), 'cell-currency', idx, 34)
            + this._td(id, 'total_biaya', this._fmt(row, 'total_biaya'), 'cell-currency', idx, 35)
            + this._td(id, 'profit', this._fmt(row, 'profit'), 'cell-currency ' + (profit >= 0 ? 'cell-profit-positive' : 'cell-profit-negative'), idx, 36)
            + this._td(id, 'idx_profit', this._fmt(row, 'idx_profit'), 'cell-number ' + (profit >= 0 ? 'cell-profit-positive' : 'cell-profit-negative'), idx, 37)
            + this._td(id, 'asuransi', this._fmt(row, 'asuransi'), 'cell-currency', idx, 38)
            + this._td(id, 'nilai_barang', this._fmt(row, 'nilai_barang'), 'cell-currency', idx, 39)
            + this._td(id, 'asuransi_jasindo', this._fmt(row, 'asuransi_jasindo'), 'cell-currency', idx, 40)
            + '</tr>';
    }

    _getStatusLabel(status) {
        const labels = {
            'new': 'Baru (dari CRM) — Menunggu PIC Vendor',
            'vendor_filled': 'Vendor sudah diisi — Menunggu PIC Invoice',
            'invoiced': 'Invoice sudah diisi — Menunggu finalisasi',
            'completed': 'Selesai'
        };
        return labels[status] || status;
    }

    _fmt(row, field) {
        if (!row) return '';
        let val = row[field];
        if (val === null || val === undefined || val === '' || val === 0 || (typeof val === 'number' && isNaN(val))) return '';

        // If there's a formula that evaluates to a non-numeric string, use it
        const formula = row.formulas ? row.formulas[field] : null;
        if (formula && formula.startsWith('="')) {
            val = formula.substring(2, formula.length - 1);
        }

        // Check for explicit user format
        const fCfg = row.formats ? row.formats[field] : null;
        let type = typeof fCfg === 'string' ? fCfg : (fCfg ? fCfg.type : null);
        let dec = (typeof fCfg === 'object' && fCfg !== null) ? fCfg.decimals : null;

        if (type === 'currency') return this.fmtC(val, dec);
        if (type === 'number') return this.fmtNum(val, dec);
        if (type === 'percent') return this.fmtP(val, dec);
        if (type === 'none') return this.esc(val);

        // Fallback to default field types
        type = this.getFieldType(field);
        if (type === 'date') return this.fmtDate(val);
        if (['penjualan', 'total_biaya', 'profit', 'asuransi', 'asuransi_jasindo', 'nilai_barang', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops', 'harga', 'surcharge', 'packing', 'handling'].includes(field)) return this.fmtC(val, dec);
        if (field === 'idx_profit') return this.fmtP(val, dec);
        if (field === 'kubik') return this.fmtDec(val, dec);
        if (['unit', 'koil'].includes(field)) return this.fmtInt(val);
        if (['aktual', 'vol', 'p', 'l', 't'].includes(field)) return this.fmtNum(val, dec);
        return this.esc(val);
    }

    // ==================== COPY / PASTE / DELETE ====================

    copySelection() {
        if (!this.selectedRange || this.selectedRange.sr === -1) return;
        const { sr, er, sc, ec } = this.selectedRange;
        const cellData = [];
        let textData = '';

        for (let r = sr; r <= er; r++) {
            const rowData = [];
            const row = this.currentData[r];
            if (!row) continue;
            for (let c = sc; c <= ec; c++) {
                const f = window.formulaEngine.colToField[c];
                let val = row[f];
                if (val === null || val === undefined) val = '';

                const formula = row.formulas ? row.formulas[f] : null;
                const isRealFormula = typeof formula === 'string' && formula.trim().startsWith('=');
                if (isRealFormula) {
                    val = formula;
                } else if (f === 'tanggal_pickup' && val) {
                    // Use dd/mm/yyyy for clipboard to match display and common Excel locale
                    const parts = String(val).split('-');
                    if (parts.length === 3) val = `${parts[2]}/${parts[1]}/${parts[0]}`;
                }

                rowData.push(val);
            }
            cellData.push(rowData);
            textData += rowData.join('\t') + '\n';
        }

        this.clipboard = { textData, cellData, startCol: sc };
        navigator.clipboard.writeText(textData).catch(() => { });
        this.updateStatusBar(`${(er - sr + 1) * (ec - sc + 1)} cell dicopy`);
    }

    _getCopyValue(td) {
        const id = td.dataset.id, f = td.dataset.field;
        if (id && f && !id.startsWith('preload_')) return this.getRawValue(id, f);
        return td.querySelector('.cell-display')?.textContent || '';
    }

    _processPasteValue(v, id, field, targetRow) {
        let pv = typeof v === 'string' ? v : String(v || '');
        pv = pv.replace(/\s+/g, ' ').trim();
        let formula = null;

        if (pv.startsWith('=')) {
            formula = pv;
            if (window.formulaEngine) {
                pv = window.formulaEngine.evaluate(formula, id, field);
                if (pv === '#CIRCULAR' || pv === '#ERROR') {
                    if (['number', 'currency'].includes(this.getFieldType(field))) pv = 0;
                }
            }
        } else {
            if (window.formulaEngine && (this.getFieldType(field) === 'number' || this.getFieldType(field) === 'currency')) {
                pv = window.formulaEngine._getCellValueByA1_Logic(pv);
            } else if (this.getFieldType(field) === 'date' && pv) {
                if (window.Formatter && window.Formatter.parseDateRobust) {
                    pv = window.Formatter.parseDateRobust(pv);
                } else {
                    let p = pv.split(/[-/.]/);
                    if (p.length === 3) {
                        let d, m, y;
                        if (p[0].length === 4) [y, m, d] = p; else[d, m, y] = p;
                        if (y.length === 2) y = '20' + y;
                        pv = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
                    }
                }
            }
        }

        const ov = this.getRawValue(id, field);
        if (String(ov) !== String(pv) || formula) {
            if (targetRow) {
                if (targetRow.formulas && typeof targetRow.formulas === 'string') {
                    try { targetRow.formulas = JSON.parse(targetRow.formulas); } catch (e) { targetRow.formulas = {}; }
                }
                if (!targetRow.formulas) targetRow.formulas = {};
                if (formula) {
                    targetRow.formulas[field] = formula;
                } else {
                    const isComputed = ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'].includes(field);
                    if (isComputed) {
                        targetRow.formulas[field] = ' '; // Dummy space to prevent auto-recalc
                    } else {
                        delete targetRow.formulas[field];
                    }
                    if (window.formulaEngine && window.formulaEngine.unregisterFormula) {
                        window.formulaEngine.unregisterFormula(id, field);
                    }
                }
                this.queueSave(id, 'formulas', targetRow.formulas);
            }
            return { changed: true, oldValue: ov, newValue: pv };
        }
        return { changed: false };
    }

    autofillRange(sr, er, sc, ec) {
        if (sr === -1 || sc === -1) return;

        const sourceR = this.activeCellPos.r;
        const sourceC = this.activeCellPos.c;
        const sourceRow = this.currentData[sourceR];
        if (!sourceRow) return;

        const sourceField = window.formulaEngine.colToField[sourceC];
        if (!sourceField) return;

        const formula = sourceRow.formulas ? sourceRow.formulas[sourceField] : null;
        const rawVal = this.getRawValue(sourceRow.id, sourceField);
        const isRealFormula = typeof formula === 'string' && formula.trim().startsWith('=');

        const ba = [];

        if (er > sr && sc === ec) {
            // Vertical Fill Downwards
            for (let r = sr; r <= er; r++) {
                if (r === sourceR) continue;
                const targetRow = this.currentData[r];
                if (!targetRow) continue;
                const id = targetRow.id;
                if (!this.isCellEditable(id, sourceField)) continue;

                let pv = rawVal;
                let newFormula = null;

                if (isRealFormula) {
                    newFormula = this.adjustFormulaRow(formula, sourceR, r);
                    pv = window.formulaEngine.evaluate(newFormula, id, sourceField);
                    if (pv === '#CIRCULAR' || pv === '#ERROR') {
                        if (['number', 'currency'].includes(this.getFieldType(sourceField))) pv = 0;
                    }
                }

                const ov = this.getRawValue(id, sourceField);
                if (String(ov) !== String(pv) || newFormula) {
                    if (targetRow.formulas && typeof targetRow.formulas === 'string') {
                        try { targetRow.formulas = JSON.parse(targetRow.formulas); } catch (e) { targetRow.formulas = {}; }
                    }
                    if (!targetRow.formulas) targetRow.formulas = {};
                    if (newFormula) {
                        targetRow.formulas[sourceField] = newFormula;
                    } else {
                        const isComputed = ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'].includes(sourceField);
                        if (isComputed) {
                            targetRow.formulas[sourceField] = ' ';
                        } else {
                            delete targetRow.formulas[sourceField];
                        }
                    }
                    this.queueSave(id, 'formulas', targetRow.formulas);

                    ba.push({ id, field: sourceField, oldValue: ov, newValue: pv });
                    this.updateCellValue(id, sourceField, pv);
                    this.queueSave(id, sourceField, pv);
                }
            }
        } else if (ec > sc && sr === er) {
            // Horizontal Fill Rightwards
            for (let c = sc; c <= ec; c++) {
                if (c === sourceC) continue;
                const field = window.formulaEngine.colToField[c];
                const id = sourceRow.id;
                if (!field || !this.isCellEditable(id, field)) continue;

                // Protect subtotal cells
                let parsedFormulas = sourceRow.formulas;
                if (typeof parsedFormulas === 'string') {
                    try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
                }
                const isProtected = this.sheetConfig && this.sheetConfig.formulaProtectionEnabled === true;
                if (isProtected && parsedFormulas && typeof parsedFormulas[field] === 'string' && parsedFormulas[field].includes('SUBTOTAL')) continue;

                let pv = rawVal;
                let newFormula = null;

                if (isRealFormula) {
                    newFormula = this.adjustFormulaCol(formula, sourceC, c);
                    pv = window.formulaEngine.evaluate(newFormula, id, field);
                    if (pv === '#CIRCULAR' || pv === '#ERROR') {
                        if (['number', 'currency'].includes(this.getFieldType(field))) pv = 0;
                    }
                }

                const ov = this.getRawValue(id, field);
                if (String(ov) !== String(pv) || newFormula) {
                    if (sourceRow.formulas && typeof sourceRow.formulas === 'string') {
                        try { sourceRow.formulas = JSON.parse(sourceRow.formulas); } catch (e) { sourceRow.formulas = {}; }
                    }
                    if (!sourceRow.formulas) sourceRow.formulas = {};
                    if (newFormula) {
                        sourceRow.formulas[field] = newFormula;
                    } else {
                        const isComputed = ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'].includes(field);
                        if (isComputed) {
                            sourceRow.formulas[field] = ' ';
                        } else {
                            delete sourceRow.formulas[field];
                        }
                    }
                    this.queueSave(id, 'formulas', sourceRow.formulas);

                    ba.push({ id, field, oldValue: ov, newValue: pv });
                    this.updateCellValue(id, field, pv);
                    this.queueSave(id, field, pv);
                }
            }
        }

        if (ba.length) {
            this.history.push({ type: 'batch', actions: ba });

            this.renderTable(this.currentData);

            ba.forEach(a => {
                this.broadcastCellUpdate(a.id, a.field, a.newValue);
                this.updateRelatedCells(a.id);
            });
            this.flushSaveQueue();
            this.updateStatusBar(`✓ Berhasil mengisi ${ba.length} cell secara otomatis`);
        }
    }

    adjustFormulaRow(formulaStr, startRowIdx, targetRowIdx) {
        if (!formulaStr || !formulaStr.startsWith('=')) return formulaStr;
        const rowDelta = targetRowIdx - startRowIdx;

        return formulaStr.replace(/(\$?([A-Z]+))(\$?)([0-9]+)/gi, (match, colPart, colLetters, absoluteRowMarker, rowDigits) => {
            if (absoluteRowMarker === '$') return match;
            const oldRow = parseInt(rowDigits);
            const newRow = oldRow + rowDelta;
            return colPart + absoluteRowMarker + newRow;
        });
    }

    adjustFormulaCol(formulaStr, startColIdx, targetColIdx) {
        if (!formulaStr || !formulaStr.startsWith('=')) return formulaStr;
        const colDelta = targetColIdx - startColIdx;

        return formulaStr.replace(/(\$?)([A-Z]+)(\$?)([0-9]+)/gi, (match, absoluteColMarker, colLetters, absoluteRowMarker, rowDigits) => {
            if (absoluteColMarker === '$') return match;
            if (window.formulaEngine && window.formulaEngine._colNameToIndex) {
                const oldColIdx = window.formulaEngine._colNameToIndex(colLetters);
                const newColIdx = oldColIdx + colDelta;
                const newColLetters = window.formulaEngine._indexToColName(newColIdx);
                return absoluteColMarker + newColLetters + absoluteRowMarker + rowDigits;
            }
            return match;
        });
    }

    cutSelection() {
        if (!this.selectedRange || this.selectedRange.sr === -1) return;
        this.copySelection();
        this.deleteSelection();
    }

    pasteToActiveCell() {
        if (!this.clipboard) return;
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Paste diblokir — mode read-only.'); return; }

        const { sr, er, sc, ec } = this.selectedRange;
        if (sr === -1 || sc === -1) return;

        const clipboardRows = this.clipboard.cellData.length;
        const clipboardCols = this.clipboard.cellData[0].length;

        const ba = [];
        const isSingleCellCopy = (clipboardRows === 1 && clipboardCols === 1);

        // Tentukan rentang pengisian
        // Jika blok yang dipilih lebih besar dari clipboard dan clipboard cuma 1 sel, isi seluruh blok
        const targetEndRow = isSingleCellCopy ? er : (sr + clipboardRows - 1);
        const targetEndCol = isSingleCellCopy ? ec : (sc + clipboardCols - 1);

        for (let r = sr; r <= targetEndRow; r++) {
            if (r >= this.currentData.length) break;
            const targetRow = this.currentData[r];
            if (!targetRow) continue;

            for (let c = sc; c <= targetEndCol; c++) {
                const field = window.formulaEngine.colToField[c];
                if (!field || !this.isCellEditable(targetRow.id, field)) continue;

                // Ambil nilai dari clipboard (tiling logic)
                const clipboardRowIdx = (r - sr) % clipboardRows;
                const clipboardColIdx = (c - sc) % clipboardCols;
                const v = this.clipboard.cellData[clipboardRowIdx][clipboardColIdx];
                const id = targetRow.id;

                // Protect subtotal cells
                let parsedFormulas = targetRow.formulas;
                if (typeof parsedFormulas === 'string') {
                    try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
                }
                const isProtected = this.sheetConfig && this.sheetConfig.formulaProtectionEnabled === true;
                if (isProtected && parsedFormulas && typeof parsedFormulas[field] === 'string' && parsedFormulas[field].includes('SUBTOTAL')) continue;

                const res = this._processPasteValue(v, id, field, targetRow);
                if (res.changed) {
                    ba.push({ id, field, oldValue: res.oldValue, newValue: res.newValue });
                    this.updateCellValue(id, field, res.newValue);
                    this.queueSave(id, field, res.newValue);
                }
            }
        }

        if (ba.length) {
            this.history.push({ type: 'batch', actions: ba });

            this.renderTable(this.currentData);

            // BROADCAST: Kirim seluruh perubahan paste ke user lain
            ba.forEach(a => {
                this.broadcastCellUpdate(a.id, a.field, a.newValue);
                this.updateRelatedCells(a.id);
            });
        }
        this.flushSaveQueue();
        this.updateStatusBar('Data dipaste ke ' + ba.length + ' cell');

        requestAnimationFrame(() => {
            const targetTd = document.querySelector('.cell-active');
            if (targetTd) {
                this.activeCell = targetTd;
                this._updateFormulaBar(targetTd);
            }
        });
    }

    // Paste from external clipboard (Excel, Google Sheets, etc.)
    async pasteFromClipboard(pastedText = null, clipboardData = null) {
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Paste diblokir — mode read-only.'); return; }

        try {
            let text = pastedText;
            let rows = [];
            let htmlParsed = false;

            if (clipboardData && clipboardData.types && clipboardData.types.includes('text/html')) {
                try {
                    const htmlText = clipboardData.getData('text/html');
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(htmlText, 'text/html');
                    const table = doc.querySelector('table');
                    if (table) {
                        const trs = table.querySelectorAll('tr');
                        if (trs && trs.length > 0) {
                            rows = Array.from(trs).map(tr => {
                                const tds = tr.querySelectorAll('td, th');
                                return Array.from(tds).map(td => {
                                    let content = td.innerHTML.replace(/<br\s*[\/]?>/gi, ' ');
                                    content = content.replace(/<\/p>|<\/div>/gi, ' ');
                                    const tempDiv = document.createElement('div');
                                    tempDiv.innerHTML = content;
                                    let text = tempDiv.innerText || tempDiv.textContent || '';
                                    return text.replace(/\s+/g, ' ').trim();
                                });
                            });
                            // Clean up trailing empty row from HTML parse
                            if (rows.length > 0 && rows[rows.length - 1].length === 0) rows.pop();
                            htmlParsed = true;
                        }
                    }
                } catch (e) { }
            }

            if (!text && navigator.clipboard && navigator.clipboard.readText) {
                text = await navigator.clipboard.readText();
            }
            if (!text && !htmlParsed) { this.pasteToActiveCell(); return; }

            if (!htmlParsed) {
                rows = this.parseTSV(text);
            }

            if (!rows || !rows.length) return;

            // If this matches what we already have in clipboard, use internal paste
            if (this.clipboard && this.clipboard.textData && this.clipboard.textData.trim() === text.trim()) {
                this.pasteToActiveCell();
                return;
            }

            const { sr, er, sc, ec } = this.selectedRange;
            if (sr === -1 || sc === -1) {
                this.updateStatusBar('⚠ Pilih cell tujuan terlebih dahulu');
                return;
            }

            const clipboardRows = rows.length;
            const clipboardCols = rows[0].length;
            const isSingleCellCopy = (clipboardRows === 1 && clipboardCols === 1);

            const targetEndRow = isSingleCellCopy ? er : (sr + clipboardRows - 1);
            const targetEndCol = isSingleCellCopy ? ec : (sc + clipboardCols - 1);

            const ba = [];

            for (let r = sr; r <= targetEndRow; r++) {
                if (r >= this.currentData.length) break;
                const targetRow = this.currentData[r];
                if (!targetRow) continue;

                for (let c = sc; c <= targetEndCol; c++) {
                    const field = window.formulaEngine.colToField[c];
                    if (!field || !this.isCellEditable(targetRow.id, field)) continue;

                    const clipboardRowIdx = (r - sr) % clipboardRows;
                    const clipboardColIdx = (c - sc) % clipboardCols;
                    const v = rows[clipboardRowIdx][clipboardColIdx];
                    const id = targetRow.id;

                    // Protect subtotal cells
                    let parsedFormulas = targetRow.formulas;
                    if (typeof parsedFormulas === 'string') {
                        try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
                    }
                    const isProtected = this.sheetConfig && this.sheetConfig.formulaProtectionEnabled === true;
                    if (isProtected && parsedFormulas && typeof parsedFormulas[field] === 'string' && parsedFormulas[field].includes('SUBTOTAL')) continue;

                    const res = this._processPasteValue(v, id, field, targetRow);
                    if (res.changed) {
                        ba.push({ id, field, oldValue: res.oldValue, newValue: res.newValue });
                        this.updateCellValue(id, field, res.newValue);
                        this.updateRelatedCells(id);
                        this.queueSave(id, field, res.newValue);
                    }
                }
            }

            if (ba.length) {
                this.history.push({ type: 'batch', actions: ba });

                this.renderTable(this.currentData);

                // BROADCAST: Kirim perubahan paste eksternal
                ba.forEach(a => {
                    this.broadcastCellUpdate(a.id, a.field, a.newValue);
                });
            }
            this.flushSaveQueue();
            this.updateStatusBar(`✓ ${ba.length} cell dipaste dari clipboard`);

            requestAnimationFrame(() => {
                const targetTd = document.querySelector('.cell-active');
                if (targetTd) {
                    this.activeCell = targetTd;
                    this._updateFormulaBar(targetTd);
                }
            });
        } catch (err) {
            // Fallback to internal clipboard if external clipboard fails (permission denied)
            this.pasteToActiveCell();
        }
    }

    parseTSV(text) {
        const rows = [];
        let currentRow = [];
        let currentCell = '';
        let inQuotes = false;

        for (let i = 0; i < text.length; i++) {
            const c = text[i];
            const nc = text[i + 1];

            if (inQuotes) {
                if (c === '"' && nc === '"') {
                    currentCell += '"';
                    i++;
                } else if (c === '"') {
                    inQuotes = false;
                } else {
                    currentCell += c;
                }
            } else {
                if (c === '"' && currentCell === '') {
                    inQuotes = true;
                } else if (c === '\t') {
                    currentRow.push(currentCell);
                    currentCell = '';
                } else if (c === '\r' && nc === '\n') {
                    currentRow.push(currentCell);
                    rows.push(currentRow);
                    currentRow = [];
                    currentCell = '';
                    i++;
                } else if (c === '\n') {
                    currentRow.push(currentCell);
                    rows.push(currentRow);
                    currentRow = [];
                    currentCell = '';
                } else {
                    currentCell += c;
                }
            }
        }

        if (currentRow.length > 0 || currentCell !== '') {
            currentRow.push(currentCell);
            rows.push(currentRow);
        }

        if (rows.length > 0 && rows[rows.length - 1].length === 1 && rows[rows.length - 1][0] === '') {
            rows.pop();
        }

        return rows;
    }

    updateRelatedCells(rowId) {
        if (!window.formulaEngine || !window.calculationsManager) return false;
        const targetRow = this.currentData.find(r => r.id == rowId);
        if (!targetRow) return false;

        // Re-evaluate the entire row to catch AutoCalc updates after bulk edits (paste, delete, autofill)
        const updatedRow = window.calculationsManager.calculateRow(targetRow);
        let rowChanged = false;

        this.colConfig.forEach(col => {
            if (updatedRow[col.field] !== targetRow[col.field]) {
                targetRow[col.field] = updatedRow[col.field];
                this.queueSave(rowId, col.field, targetRow[col.field]);
                rowChanged = true;
            }
        });

        this.updateMissingDateWarning();
        return rowChanged;
    }

    deleteSelection() {
        const { sr, er, sc, ec } = this.selectedRange;
        if (sr === -1) return;
        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Penghapusan diblokir — mode read-only.'); return; }

        const dc = [], ai = new Set();
        const totalToProcess = (er - sr + 1) * (ec - sc + 1);
        // if (totalToProcess > 50) showToast(`Menghapus ${totalToProcess} cell...`, 'info');

        for (let r = sr; r <= er; r++) {
            const row = this.currentData[r];
            if (!row || String(row.id).startsWith('preload_')) continue;

            for (let c = sc; c <= ec; c++) {
                const field = window.formulaEngine.colToField[c];
                if (!field || !this.isCellEditable(row.id, field)) continue;

                // Protect subtotal cells
                let parsedFormulas = row.formulas;
                if (typeof parsedFormulas === 'string') {
                    try { parsedFormulas = JSON.parse(parsedFormulas); } catch (e) { parsedFormulas = null; }
                }
                const isProtected = this.sheetConfig && this.sheetConfig.formulaProtectionEnabled === true;
                if (isProtected && parsedFormulas && typeof parsedFormulas[field] === 'string' && parsedFormulas[field].includes('SUBTOTAL')) continue;

                const computedFields = ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo', 'kubik'];
                const isComputed = computedFields.includes(field);

                // For computed fields, pressing Delete should ONLY remove custom formula to restore AutoCalc.
                // If it doesn't have a custom formula, skip it entirely to save database load.
                let hasCustomFormula = false;
                while (row.formulas && typeof row.formulas === 'string') { 
                    try { 
                        let parsed = JSON.parse(row.formulas); 
                        if (typeof parsed === 'string' && parsed === row.formulas) break; 
                        row.formulas = parsed; 
                    } catch (e) { 
                        row.formulas = {}; 
                        break; 
                    } 
                }
                if (!row.formulas) row.formulas = {};
                
                if (isComputed) {
                    if (row.formulas[field]) {
                        hasCustomFormula = true;
                    } else {
                        continue; // Skip computed cells to keep AutoCalc alive and save DB load
                    }
                }

                const ov = row[field];
                let nv;
                const type = this.getFieldType(field);
                if (type === 'number') nv = null;
                else if (type === 'date') nv = null;
                else nv = '';

                // Optimization: if the cell is already empty, and there's no custom formula to remove, skip it!
                const isAlreadyEmpty = (ov === null || ov === '' || ov === undefined);
                if (isAlreadyEmpty && !hasCustomFormula) {
                    continue; 
                }

                let oldFormula = row.formulas[field];
                let newFormula = undefined;

                if (ov != nv || hasCustomFormula) { // Loose equality to catch null/undefined/empty
                    if (!isComputed) {
                        row[field] = nv;
                    }

                    if (row.formulas && row.formulas[field]) {
                        delete row.formulas[field];
                        this.queueSave(row.id, 'formulas', row.formulas);
                    }
                    newFormula = row.formulas[field];

                    if (window.formulaEngine && window.formulaEngine.unregisterFormula) {
                        window.formulaEngine.unregisterFormula(row.id, field);
                    }
                    
                    if (!isComputed) {
                        this.queueSave(row.id, field, nv);
                    }
                    
                    ai.add(row.id);
                    dc.push({ id: row.id, field, oldValue: ov, newValue: (isComputed ? ov : nv), oldFormula, newFormula });
                }
            }
        }

        if (dc.length > 0) {
            this.history.push({ type: 'batch', actions: dc });

            // Recalculate related cells before rendering so custom formula deletions reflect immediately
            ai.forEach(id => this.updateRelatedCells(id));

            this.renderTable(this.currentData);

            const isMassive = dc.length > 100;

            if (isMassive) {
                // Skip individual broadcast to prevent websocket crash on large deletes
                // Optional: send a single refresh event
                this.broadcastCellUpdate('BULK', 'refresh', Date.now());
                
                // Recalculate all formulas at once instead of one by one
                this._initializeFormulas();
            } else {
                // BROADCAST: Beritahu user lain bahwa sel-sel ini telah dihapus
                dc.forEach(a => {
                    this.broadcastCellUpdate(a.id, a.field, a.newValue);
                    // Trigger formula recalculation for any cells that depend on this deleted cell
                    if (window.formulaEngine) {
                        const cellA1 = window.formulaEngine._mapCellIdToA1(`${a.id}:${a.field}`);
                        if (cellA1) window.formulaEngine.recalculateDependents(cellA1);
                    }
                });
            }

            this.updateStatusBar(`✓ ${dc.length} cell berhasil dikosongkan`);
            // if (dc.length > 50) showToast(`${dc.length} cell berhasil dikosongkan`, 'success');
        } else {
            this.updateStatusBar('Cell sudah kosong');
        }
        this.flushSaveQueue();

        requestAnimationFrame(() => {
            const targetTd = document.querySelector('.cell-active');
            if (targetTd) {
                this.activeCell = targetTd;
                this._updateFormulaBar(targetTd);
            }
        });
    }

    async deleteActiveRow() {
        if (!this.activeCell) return;
        if (!window.authManager.isAdmin()) {
            showToast('Hanya Admin yang dapat menghapus seluruh baris.', 'warning');
            return;
        }
        const tr = this.activeCell.closest('tr'), id = tr?.dataset.id;
        if (!id || id.startsWith('preload_')) return;

        const confirmed = await showConfirm({
            title: 'Hapus Baris',
            message: 'Hapus baris ini dari database?\nData yang dihapus tidak bisa dikembalikan.',
            icon: 'danger',
            confirmText: 'Hapus',
            confirmClass: 'danger'
        });

        if (!confirmed) return;

        const dr = this.currentData.find(r => r.id == id);
        window.databaseManager.deleteRow(id).then(() => {
            this.currentData = this.currentData.filter(r => r.id != id);
            this.originalData = this.originalData.filter(r => r.id != id);
            this.history.push({ type: 'deleteRow', row: dr });
            this.activeCell = null;
            this.selectedCells = [];
            this.renderTable(this.currentData);
            // showToast('Baris berhasil dihapus', 'success');
        }).catch(err => {
            console.error(err);
            showToast('Gagal menghapus baris: ' + err.message, 'error');
        });
    }

    async deleteAllCells() {
        if (this.isReadOnlyUser()) {
            showToast('Anda tidak memiliki akses untuk menghapus data.', 'warning');
            return;
        }

        const confirmed = await showConfirm({
            title: 'Hapus Semua Cell',
            message: 'Anda yakin ingin mengosongkan seluruh worksheet ini?\nData yang dikosongkan masih bisa di-undo sementara menggunakan Ctrl+Z.',
            icon: 'warning',
            confirmText: 'Ya, Kosongkan',
            confirmClass: 'danger'
        });

        if (!confirmed) return;

        const maxCol = window.formulaEngine ? window.formulaEngine.colToField.length - 1 : 40;
        this.selectedRange = {
            sr: 0,
            er: this.currentData.length - 1,
            sc: 1,
            ec: maxCol
        };
        this.deleteSelection();
        this.clearSelection();
    }




    selectRow(tr) {
        const idx = parseInt(tr.dataset.idx);
        this.selectedRange = {
            sr: idx,
            er: idx,
            sc: 1,
            ec: window.formulaEngine.colToField.length - 1 // Max columns
        };
        this.activeCellPos = { r: idx, c: 1 };
        this._updateSelectionUI();
    }

    clearSelection() {
        this.selectedRange = { sr: -1, er: -1, sc: -1, ec: -1 };
        this.activeCellPos = { r: -1, c: -1 };
        this.activeCell = null;
        this.selectedCells = [];
        document.querySelectorAll('.cell-selected, .cell-active, .cell-editing').forEach(c => {
            c.classList.remove('cell-selected', 'cell-active', 'cell-editing');
        });
    }

    focusCell(rowIndex, colIndex) {
        const tbody = document.getElementById('kpiTableBody');
        if (!tbody) return;
        const row = tbody.children[rowIndex];
        if (!row) return;
        const cell = row.children[colIndex];
        if (!cell || cell.classList.contains('col-index') || cell.classList.contains('col-actions')) return;

        this.selectCell(cell);
        this.spreadsheetState.activeCell = { row: rowIndex, col: colIndex };

        // Scroll into view if needed
        const wrapper = document.querySelector('.table-wrapper');
        if (wrapper) {
            const cellRect = cell.getBoundingClientRect();
            const wrapperRect = wrapper.getBoundingClientRect();

            if (cellRect.top < wrapperRect.top || cellRect.bottom > wrapperRect.bottom) {
                cell.scrollIntoView({ block: 'nearest', inline: 'nearest' });
            }
            if (cellRect.left < wrapperRect.left || cellRect.right > wrapperRect.right) {
                cell.scrollIntoView({ block: 'nearest', inline: 'nearest' });
            }
        }
    }

    resetSheetView() {
        this.clearSelection();
        const wrapper = document.querySelector('.spreadsheet-container');
        if (wrapper) {
            wrapper.scrollTop = 0;
            wrapper.scrollLeft = 0;

            // Wait for VirtualScroller to re-render after scroll reset
            setTimeout(() => {
                const tbody = document.getElementById('kpiTableBody');
                if (!tbody) return;
                // Use class selector to ignore spacerTop/Bottom from VirtualScroller
                const firstRow = tbody.querySelector('tr.spreadsheet-row');
                if (firstRow) {
                    const firstTd = firstRow.querySelector('td[data-field="tanggal_pickup"]');
                    if (firstTd) {
                        this.selectCell(firstTd);
                        this.spreadsheetState.activeCell = { row: 0, col: 1 };
                        firstTd.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                    }
                }
            }, 50);
        }
    }

    moveActiveCell(d, silent) {
        let { r, c } = this.activeCellPos;
        if (r === -1) return;

        const maxCol = window.formulaEngine ? window.formulaEngine.colToField.length - 1 : 40;

        if (d === 'ArrowRight' || d === 'Tab') {
            c++;
            if (c > maxCol && d === 'Tab') { c = 1; r++; }
        } else if (d === 'ArrowLeft' || d === 'ShiftTab') {
            c--;
            if (c < 1 && d === 'ShiftTab') { c = maxCol; r--; }
        } else if (d === 'ArrowDown') {
            r++;
        } else if (d === 'ArrowUp') {
            r--;
        }

        // Bound checks
        r = Math.max(0, Math.min(this.currentData.length - 1, r));
        c = Math.max(1, Math.min(maxCol, c));

        this.activeCellPos = { r, c };
        this.selectedRange = { sr: r, er: r, sc: c, ec: c };

        if (!silent) {
            this.clearReferencedHighlights();
            this._updateSelectionUI();
            const targetTd = document.querySelector(`#kpiTableBody tr[data-idx="${r}"] td:nth-child(${c + 1})`);
            if (targetTd) {
                this.activeCell = targetTd;
                this._ensureVisible(targetTd, r, c);
                this._updateFormulaBar(targetTd);
            } else {
                // Cell is off-screen. Scroll container so the target row will be visible.
                const container = document.querySelector('.spreadsheet-container');
                if (container) {
                    // Measure actual sticky header height dynamically
                    const thead = container.querySelector('thead');
                    const theadH = thead ? thead.getBoundingClientRect().height : 60;
                    
                    if (r === 0) {
                        container.scrollTop = 0;
                    } else {
                        // Position row just below the sticky header
                        container.scrollTop = Math.max(0, r * 36 - theadH - 4);
                    }
                    if (c === 1) container.scrollLeft = 0;
                }
                
                // Force virtual scroller to render immediately so highlight isn't lost
                if (this.virtualScroller) {
                    this.virtualScroller._forceRender();
                    
                    // Re-fetch the newly rendered cell and ensure it's visible
                    const newTargetTd = document.querySelector(`#kpiTableBody tr[data-idx="${r}"] td:nth-child(${c + 1})`);
                    if (newTargetTd) {
                        this.activeCell = newTargetTd;
                        this._ensureVisible(newTargetTd, r, c);
                        this._updateFormulaBar(newTargetTd);
                    }
                }
            }
        }
    }

    _ensureVisible(td, r, c) {
        const container = document.querySelector('.spreadsheet-container');
        if (!container) return;

        const rect = td.getBoundingClientRect();
        const contRect = container.getBoundingClientRect();

        // Dynamically measure the actual sticky header height
        const thead = container.querySelector('thead');
        const theadH = thead ? thead.getBoundingClientRect().height : 60;
        
        // Measure actual scrollbar thickness
        const hScrollbarH = container.offsetHeight - container.clientHeight;
        
        const visibleTop = contRect.top + theadH;
        const visibleBottom = contRect.bottom - hScrollbarH;

        // Vertical check: cell must be fully within [visibleTop, visibleBottom]
        // Add 6px padding to account for 4px header shadow gap + outline width
        if (r === 0) {
            container.scrollTop = 0;
        } else if (rect.top < visibleTop + 6) {
            // Cell is behind the sticky header → scroll up so cell + outline sits below header
            container.scrollTop -= (visibleTop + 6 - rect.top);
        } else if (rect.bottom > visibleBottom - 6) {
            // Cell is below the visible area → scroll down so cell + outline sits above bottom
            container.scrollTop += (rect.bottom - (visibleBottom - 6));
        }

        // Horizontal check
        const indexWidth = 55;
        const vScrollbarW = container.offsetWidth - container.clientWidth;
        if (c === 1) {
            container.scrollLeft = 0;
        } else if (rect.left < contRect.left + indexWidth) {
            container.scrollLeft -= (contRect.left + indexWidth - rect.left);
        } else if (rect.right > contRect.right - vScrollbarW) {
            container.scrollLeft += (rect.right - (contRect.right - vScrollbarW));
        }
    }

    // ==================== EDIT CELL (FLOATING EDITOR) ====================

    startEditCell(td, overwrite = false, initialChar = '') {
        if (this.editingCell) this.saveCellEdit();
        const f = td.dataset.field, id = td.dataset.id;
        if (!id || !f) return;
        if (id.startsWith('preload_') && !overwrite) {
            console.log('[Table] Attempting to edit preloaded row. Forcing save first.');
            // This case shouldn't happen with real DB inserts but adding safety
            this.updateStatusBar('⚠ Baris belum siap.');
            return;
        }
        if (!this.isCellEditable(id, f)) return;

        const type = this.getFieldType(f);
        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
        let cv = this.getRawValue(id, f);

        // Show formula if exists
        const formula = (row && row.formulas) ? row.formulas[f] : null;
        const isRealFormula = typeof formula === 'string' && formula.trim().startsWith('=');
        if (isRealFormula) cv = formula;

        if (typeof cv === 'string' && cv.trim() === '') {
            cv = '';
        }

        this.editingCell = { td, field: f, id, type, originalValue: cv };

        // Ensure floating editor exists
        let editor = document.getElementById('cellFloatingEditor');
        if (!editor) {
            editor = document.createElement('div');
            editor.id = 'cellFloatingEditor';
            editor.className = 'cell-floating-editor';
            document.body.appendChild(editor);
        }

        const rect = td.getBoundingClientRect();
        editor.style.display = 'block';
        editor.style.left = rect.left + 'px';
        editor.style.top = rect.top + 'px';
        editor.style.width = rect.width + 'px';
        editor.style.height = rect.height + 'px';

        let ih;
        const displayValue = overwrite ? initialChar : (String(cv || ''));

        // Use text input for EVERYTHING to allow formulas and mixed content
        if (type === 'date' && !displayValue.startsWith('=')) {
            // Special formatting for date display while editing, if not a formula
            let dateVal = cv;
            if (cv && cv.includes('-')) {
                const parts = cv.split('-');
                if (parts.length === 3) dateVal = `${parts[2]}/${parts[1]}/${parts[0]}`;
            }
            ih = `<input type="text" class="cell-editor-input" value="${dateVal || ''}" placeholder="dd/mm/yyyy">`;
        } else {
            ih = `<input type="text" class="cell-editor-input" value="${this.esc(displayValue)}">`;
        }

        editor.innerHTML = ih;

        const inp = editor.querySelector('.cell-editor-input');
        if (inp) {
            requestAnimationFrame(() => {
                inp.focus();
                const len = inp.value.length;
                inp.setSelectionRange(len, len); // Place cursor at end, no full highlight
            });
            inp.addEventListener('keydown', (e) => {
                e.stopPropagation();

                // Autocomplete Navigation
                const list = this.autocompleteList;
                if (list && list.style.display === 'block') {
                    const items = list.querySelectorAll('.autocomplete-item');
                    let activeIdx = Array.from(items).findIndex(it => it.classList.contains('active'));

                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        items[activeIdx]?.classList.remove('active');
                        activeIdx = (activeIdx + 1) % items.length;
                        items[activeIdx]?.classList.add('active');
                        items[activeIdx]?.scrollIntoView({ block: 'nearest' });
                        return;
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        items[activeIdx]?.classList.remove('active');
                        activeIdx = (activeIdx - 1 + items.length) % items.length;
                        items[activeIdx]?.classList.add('active');
                        items[activeIdx]?.scrollIntoView({ block: 'nearest' });
                        return;
                    } else if (e.key === 'Enter' || e.key === 'Tab') {
                        const activeItem = list.querySelector('.autocomplete-item.active');
                        if (activeItem) {
                            e.preventDefault();
                            activeItem.onmousedown(); // Trigger the apply logic
                            return;
                        }
                    } else if (e.key === 'Escape') {
                        e.preventDefault();
                        this.hideAutocomplete();
                        return;
                    }
                }

                if (e.key === 'Enter') { e.preventDefault(); this.saveCellEdit(); this.moveActiveCell('ArrowDown'); }
                else if (e.key === 'Tab') { e.preventDefault(); this.saveCellEdit(); this.moveActiveCell(e.shiftKey ? 'ShiftTab' : 'Tab'); }
                else if (e.key === 'Escape') { e.preventDefault(); this.cancelCellEdit(); }
            });
            inp.addEventListener('input', () => {
                this.showAutocomplete(inp);
                this.highlightReferencedCells(inp.value);
                const fb = document.getElementById('formulaBar');
                if (fb) fb.value = inp.value;
            });
            inp.addEventListener('blur', (e) => {
                // Auto save on blur
                setTimeout(() => {
                    if (this.editingCell) {
                        this.clearReferencedHighlights();
                        this.saveCellEdit();
                    }
                }, 150);
            });
        }


        td.classList.add('cell-editing');
    }

    saveCellEdit() {
        if (!this.editingCell) return;
        const { td, field: f, id, originalValue: ov, type } = this.editingCell;

        this.clearReferencedHighlights();

        const editor = document.getElementById('cellFloatingEditor');
        const inp = editor?.querySelector('.cell-editor-input');
        if (!inp) { this.editingCell = null; return; }

        const raw = inp.value.trim();
        this.editingCell = null;
        if (editor) editor.style.display = 'none';

        this._processAndSaveValue(id, f, raw, ov, td, type);
    }

    _processAndSaveValue(id, f, raw, ov, td, type = null) {
        if (!type) type = this.getFieldType(f);
        let pv = raw;
        let formula = null;
        const numericFields = ['aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil', 'penjualan', 'nilai_barang', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops', 'asuransi', 'asuransi_jasindo', 'harga', 'surcharge', 'packing', 'handling'];

        if (raw.startsWith('=')) {
            formula = raw;
            pv = window.formulaEngine.evaluate(raw, id, f);
            if (pv === '#CIRCULAR' || pv === '#ERROR') {
                const msg = pv === '#CIRCULAR' ? '⚠ Referensi melingkar (Circular Reference)' : '⚠ Kesalahan Formula (#ERROR)';
                this.updateStatusBar(msg);
                // Convert to 0 for database storage if the column is numeric
                if (numericFields.includes(f)) pv = 0;
            }
        } else if (type === 'date') {
            if (!raw) {
                pv = null;
            } else {
                let parts = raw.split(/[-/]/);
                if (parts.length === 3) {
                    let d, m, y;
                    if (parts[0].length === 4) [y, m, d] = parts;
                    else[d, m, y] = parts;
                    if (y.length === 2) y = '20' + y;
                    pv = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
                } else {
                    pv = raw;
                }
            }
        } else {
            if (numericFields.includes(f)) {
                const n = window.Formatter ? window.Formatter.parseLocaleFloat(raw) : parseFloat(raw);
                if (!isNaN(n)) {
                    pv = n;
                } else if (raw !== '') {
                    // It's text in a numeric column! Save as text-formula to bypass DB numeric constraint
                    formula = `="${raw}"`;
                    pv = 0;
                } else {
                    pv = null; // Clear to null instead of 0
                }
            }
        }

        if (pv === ov && !formula) {
            this.cancelCellEdit();
            return;
        }

        // Store formula if present
        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
        let oldFormula = undefined;
        let newFormula = undefined;

        if (row) {
            while (row.formulas && typeof row.formulas === 'string') { try { let parsed = JSON.parse(row.formulas); if (typeof parsed === 'string' && parsed === row.formulas) break; row.formulas = parsed; } catch (e) { row.formulas = {}; break; } }
            if (!row.formulas) row.formulas = {};
            oldFormula = row.formulas[f];

            if (formula) {
                row.formulas[f] = formula;
            } else {
                const isComputed = ['penjualan', 'total_biaya', 'profit', 'idx_profit', 'asuransi', 'asuransi_jasindo'].includes(f);
                if (isComputed) {
                    row.formulas[f] = ' '; // Dummy space to prevent auto-recalc overwrite
                } else {
                    delete row.formulas[f];
                }
                if (window.formulaEngine && window.formulaEngine.unregisterFormula) {
                    window.formulaEngine.unregisterFormula(id, f);
                }
            }
            newFormula = row.formulas[f];
        }

        this.history.push({ type: 'batch', actions: [{ id, field: f, oldValue: ov, newValue: pv, oldFormula, newFormula }] });


        const oldData = row ? { ...row } : null; // AMBIL DATA LAMA DI SINI SEBELUM BERUBAH

        this.updateCellValue(id, f, pv);
        this.renderCellDisplay(td, f, id);
        if (td) td.classList.remove('cell-editing');
        document.querySelectorAll('.cell-editing').forEach(el => el.classList.remove('cell-editing'));

        // INSTANT BROADCAST: Kirim ke user lain seketika tanpa menunggu database
        this.broadcastCellUpdate(id, f, pv);

        // Recalculate dependents
        const cellA1 = window.formulaEngine._mapCellIdToA1(`${id}:${f}`);
        if (cellA1) window.formulaEngine.recalculateDependents(cellA1);

        this.updateRelatedCells(id);
        this.updateMissingDateWarning();
        this.directSave(id, f, pv, formula, oldData); // Kirim oldData ke fungsi save
    }

    broadcastCellUpdate(id, field, value) {
        if (!this.presenceChannel || !authManager.currentUser) return;
        this.presenceChannel.send({
            type: 'broadcast',
            event: 'cell_update',
            payload: {
                id: id,
                field: field,
                value: value,
                editor: authManager.currentUser.config?.name || authManager.currentUser.email
            }
        });
    }

    async directSave(id, f, v, formula, oldData = null) {
        this.setSyncStatus('syncing');
        if (this.activeSyncCount === undefined) this.activeSyncCount = 0;
        this.activeSyncCount++;
        try {
            const updates = { [f]: v };
            const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);

            if (row && row.formulas) updates.formulas = row.formulas;

            // Auto-progress CRM workflow status
            if (row && row.source === 'crm' && row.row_status !== 'completed') {
                const vendorFields = ['nama_vendor', 'nama_vendor_ii', 'nama_vendor_iii', 'nama_vendor_iv', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv'];
                const invoiceFields = ['penjualan', 'total_biaya', 'harga'];

                if (row.row_status === 'new' && vendorFields.includes(f) && v) {
                    updates.row_status = 'vendor_filled';
                    row.row_status = 'vendor_filled';
                } else if ((row.row_status === 'new' || row.row_status === 'vendor_filled') && invoiceFields.includes(f) && v) {
                    updates.row_status = 'invoiced';
                    row.row_status = 'invoiced';
                }
            }

            const updatedRow = await window.databaseManager.updateRow(id, updates, oldData);

            if (updatedRow) {
                this._syncLocalRow(updatedRow);
            }

            this.setSyncStatus('synced');
            this.updateStatusBar('✓ Tersimpan');

            if (this.activeCell?.dataset?.id == id) {
                this.showLastEditInfo(id);
            }
        } catch (err) {
            console.error('Save failed:', err);
            this.setSyncStatus('error');
            const msg = err.message || 'Gagal menyimpan';
            this.updateStatusBar('Gagal: ' + msg);
        } finally {
            this.activeSyncCount--;
        }
    }

    queueSave(id, f, v) {
        if (!this.saveQueue[id]) this.saveQueue[id] = {};
        this.saveQueue[id][f] = v;

        // Persist formulas if any
        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
        if (row && row.formulas) {
            this.saveQueue[id].formulas = row.formulas;
        }

        clearTimeout(this.saveTimer);
        this.saveTimer = setTimeout(() => this.flushSaveQueue(), 300);
    }

    async flushSaveQueue() {
        const q = { ...this.saveQueue };
        this.saveQueue = {};
        if (!Object.keys(q).length) return;
        this.setSyncStatus('syncing');
        if (this.activeSyncCount === undefined) this.activeSyncCount = 0;
        this.activeSyncCount++;
        let errCount = 0;
        try {
            const keys = Object.keys(q);
            if (keys.length > 1 && window.databaseManager && typeof window.databaseManager.updateRowsBulk === 'function') {
                // BULK UPDATE PATH
                const bulkData = [];
                for (const id of keys) {
                    const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
                    if (row) {
                        bulkData.push({ id, updates: q[id], oldData: { ...row } });
                    }
                }

                try {
                    const updatedRows = await window.databaseManager.updateRowsBulk(bulkData);
                    if (updatedRows && updatedRows.length > 0) {
                        updatedRows.forEach(updatedRow => this._syncLocalRow(updatedRow));
                    }
                } catch (e) {
                    errCount = keys.length;
                    keys.forEach(id => {
                        if (!this.saveQueue[id]) this.saveQueue[id] = {};
                        Object.assign(this.saveQueue[id], q[id]);
                    });
                }
            } else {
                // SEQUENTIAL UPDATE PATH (1 row or fallback)
                for (const [id, u] of Object.entries(q)) {
                    try {
                        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
                        const oldData = row ? { ...row } : null;
                        const updatedRow = await window.databaseManager.updateRow(id, u, oldData);
                        if (updatedRow) {
                            this._syncLocalRow(updatedRow);
                        }
                    } catch (e) {
                        errCount++;
                        if (!this.saveQueue[id]) this.saveQueue[id] = {};
                        Object.assign(this.saveQueue[id], u);
                    }
                }
            }
            this.setSyncStatus(errCount > 0 ? 'error' : 'synced');
            if (errCount > 0) {
                this.updateStatusBar('⚠ ' + errCount + ' baris gagal disimpan');
            }

            if (this.activeCell?.dataset?.id) {
                this.showLastEditInfo(this.activeCell.dataset.id);
            }
        } finally {
            this.activeSyncCount--;
        }
    }

    /**
     * Sync satu row dari database response ke local data
     * Menyimpan updated_by, updated_at, dan semua field lainnya
     */
    _syncLocalRow(dbRow) {
        if (!dbRow || !dbRow.id) return;

        // Ensure formulas column is parsed from JSON string to object
        if (dbRow.formulas && typeof dbRow.formulas === 'string') {
            try {
                dbRow.formulas = JSON.parse(dbRow.formulas);
            } catch (e) {
                console.error('Failed to parse formulas in _syncLocalRow:', e);
            }
        }

        const idStr = String(dbRow.id);

        // Update in-memory map O(1)
        const row = this.rowMap ? this.rowMap.get(idStr) : null;
        if (row) {
            Object.assign(row, dbRow);
        } else {
            // Fallback for new rows or if map isn't ready
            const i = this.currentData.findIndex(r => r && r.id == dbRow.id);
            if (i !== -1) Object.assign(this.currentData[i], dbRow);
        }

        const j = this.originalData.findIndex(r => r && r.id == dbRow.id);
        if (j !== -1) Object.assign(this.originalData[j], dbRow);
    }

    cancelCellEdit() {
        if (!this.editingCell) {
            const editor = document.getElementById('cellFloatingEditor');
            if (editor) editor.style.display = 'none';
            return;
        }

        this.clearReferencedHighlights();

        const { td, field: f, id } = this.editingCell;
        this.editingCell = null;
        this.renderCellDisplay(td, f, id);
        if (td) td.classList.remove('cell-editing');
        document.querySelectorAll('.cell-editing').forEach(el => el.classList.remove('cell-editing'));
        const editor = document.getElementById('cellFloatingEditor');
        if (editor) editor.style.display = 'none';
    }

    // ==================== HIGHLIGHT REFERENCED CELLS ====================

    highlightReferencedCells(formula) {
        this.clearReferencedHighlights();
        if (!formula || !formula.startsWith('=') || !window.formulaEngine) return;

        // Enhanced regex to capture operator and A1 reference
        // Group 1: Operator (+, -, *, /, (, :, ,)
        // Group 2: A1 Reference
        const refRegex = /([+\-*/(:,])?([A-Z]+\d+)/g;
        let match;
        while ((match = refRegex.exec(formula.toUpperCase())) !== null) {
            const operator = match[1];
            const a1 = match[2];

            let cls = 'cell-referenced'; // Default Blue (SUM, starts, ranges)
            if (operator === '+') cls = 'cell-ref-add';
            else if (operator === '-') cls = 'cell-ref-sub';
            else if (operator === '*') cls = 'cell-ref-mul';
            else if (operator === '/') cls = 'cell-ref-div';

            const cellId = window.formulaEngine._mapA1ToCellId(a1);
            if (cellId) {
                const [rowId, field] = cellId.split(':');
                const td = document.querySelector(`td[data-id="${rowId}"][data-field="${field}"]`);
                if (td) td.classList.add(cls);
            }
        }
    }

    clearReferencedHighlights() {
        const classes = ['cell-referenced', 'cell-ref-add', 'cell-ref-sub', 'cell-ref-mul', 'cell-ref-div'];
        document.querySelectorAll(classes.map(c => '.' + c).join(',')).forEach(el => {
            el.classList.remove(...classes);
        });
    }

    updateCellValue(id, f, v) {
        const idStr = String(id);

        // Ensure formulas column is parsed from JSON string to object
        if (f === 'formulas' && typeof v === 'string') {
            try {
                v = JSON.parse(v);
            } catch (e) {
                console.error('Failed to parse formulas in updateCellValue:', e);
            }
        }

        const row = this.rowMap ? this.rowMap.get(idStr) : null;
        if (row) {
            row[f] = v;
        } else {
            const i = this.currentData.findIndex(r => r && r.id == id);
            if (i !== -1) this.currentData[i][f] = v;
        }

        const j = this.originalData.findIndex(r => r && r.id == id);
        if (j !== -1) this.originalData[j][f] = v;
    }

    renderCellDisplay(td, f, id) {
        const idStr = String(id);
        let row = this.rowMap ? this.rowMap.get(idStr) : null;
        if (!row) row = (this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id));
        if (!row) return;

        const dv = this._fmt(row, f);
        let cn = 'cell-display';
        const type = this.getFieldType(f);
        if (type === 'date') cn += ' cell-date';
        else if (type === 'number') {
            if (['penjualan', 'total_biaya', 'profit', 'asuransi', 'asuransi_jasindo', 'nilai_barang', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops', 'harga', 'surcharge', 'packing', 'handling'].includes(f)) cn += ' cell-currency';
            else cn += ' cell-number';
        }

        let errorMsg = null;
        if (window.formulaEngine && window.formulaEngine.cellErrors) {
            errorMsg = window.formulaEngine.cellErrors.get(`${idStr}:${f}`);
            if (errorMsg) {
                cn += ' cell-error';
                td.title = errorMsg === '#CIRCULAR' ? '⚠ Referensi melingkar (Circular Reference)' : '⚠ Kesalahan Formula (#ERROR)';
            } else {
                td.removeAttribute('title'); // clean up previous error
            }
        }

        if (f === 'profit' || f === 'idx_profit') {
            const p = parseFloat(row.profit) || 0;
            cn += p >= 0 ? ' cell-profit-positive' : ' cell-profit-negative';
        }

        const isEditable = this.isCellEditable(id, f);
        if (isEditable) {
            td.classList.remove('cell-readonly');
        } else {
            td.classList.add('cell-readonly');
        }

        let fObj = row.formulas;
        while (typeof fObj === 'string') { try { let parsed = JSON.parse(fObj); if (typeof parsed === 'string' && parsed === fObj) break; fObj = parsed; } catch (e) { fObj = null; break; } }

        let hasComment = fObj && fObj.__comments && fObj.__comments[f];
        let commentHTML = hasComment ? `<div class="cell-comment-indicator" data-comment="${fObj.__comments[f].replace(/"/g, '&quot;')}"></div>` : '';
        td.removeAttribute('data-comment');

        if (fObj && fObj.__formats && fObj.__formats[f]) {
            const format = fObj.__formats[f];
            if (format.locked) td.classList.add('cell-locked'); else td.classList.remove('cell-locked');
            td.style.fontWeight = format.bold ? 'bold' : '';
            td.style.fontStyle = format.italic ? 'italic' : '';
            td.style.textDecoration = format.underline ? 'underline' : '';
            if (format.bgColor) {
                td.style.setProperty('background-color', format.bgColor, 'important');
            } else {
                td.style.removeProperty('background-color');
            }
            const alignStyle = format.align ? ` style="text-align:${format.align};width:100%;height:100%;display:flex;align-items:center;justify-content:${format.align === 'right' ? 'flex-end' : (format.align === 'center' ? 'center' : 'flex-start')};"` : '';
            td.innerHTML = '<div class="' + cn + (isEditable ? '' : ' cell-readonly') + '"' + alignStyle + '>' + dv + '</div>' + commentHTML;
        } else {
            td.classList.remove('cell-locked');
            td.style.fontWeight = '';
            td.style.fontStyle = '';
            td.style.textDecoration = '';
            td.style.removeProperty('background-color');
            td.innerHTML = '<div class="' + cn + (isEditable ? '' : ' cell-readonly') + '">' + dv + '</div>' + commentHTML;
        }
    }

    updateRelatedCells(id) {
        const row = this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id);
        if (!row) return;

        // Ensure row.formulas is parsed as a proper object
        while (row.formulas && typeof row.formulas === 'string') { try { let parsed = JSON.parse(row.formulas); if (typeof parsed === 'string' && parsed === row.formulas) break; row.formulas = parsed; } catch (e) { row.formulas = {}; break; } }

        // Skip subtotal rows from automatic cell dependency updates
        const isSubtotal = row.formulas && Object.values(row.formulas).some(v => typeof v === 'string' && v.includes('SUBTOTAL'));
        if (isSubtotal) return;

        // 1. Define hasFormula respecting visual exclusions AND manual overrides
        const hasFormula = (field) => {
            if (window.formulaEngine && window.formulaEngine.isRowExcludedForField(row, field)) return true;
            return row.formulas && row.formulas[field] !== undefined;
        };

        // Use calculationsManager to compute calculated fields instead of hardcoding them
        const computedRow = window.calculationsManager.calculateRow(row);
        const computed = {
            penjualan: computedRow.penjualan,
            total_biaya: computedRow.total_biaya,
            asuransi: computedRow.asuransi,
            asuransi_jasindo: computedRow.asuransi_jasindo,
            profit: computedRow.profit,
            idx_profit: computedRow.idx_profit
        };
        const changedFields = [];

        // 2. Update local row object and UI cell display if changed
        Object.entries(computed).forEach(([field, val]) => {
            // Check if there is NO manual formula or override/exclusion for this field
            if (hasFormula(field)) return;

            const oldVal = row[field];
            // Loose comparison to handle null vs 0 vs undefined
            if (oldVal != val && !(oldVal === null && val === 0) && !(oldVal === 0 && val === null)) {
                row[field] = val;
                changedFields.push(field);

                // Update cell DOM if on screen
                const td = document.querySelector(`td[data-id="${id}"][data-field="${field}"]`);
                if (td) {
                    this.renderCellDisplay(td, field, id);
                }

                // Broadcast cell update to other clients
                this.broadcastCellUpdate(id, field, val);

                // Recalculate formula dependents of this cell
                const cellA1 = window.formulaEngine._mapCellIdToA1(`${id}:${field}`);
                if (cellA1) {
                    window.formulaEngine.recalculateDependents(cellA1);
                }

                // Unify calculated field update into the same save queue to prevent race conditions
                this.queueSave(id, field, val);
            }
        });
    }

    // ==================== REAL-TIME POLLING ====================
    startRealtimeSync() {
        if (this.syncInterval) clearInterval(this.syncInterval);
        
        // Poll setiap 3 detik
        this.syncInterval = setInterval(async () => {
            if (!window.activeSheetId || this.isPreloading || !this.currentData || this.currentData.length === 0) return;
            
            // Cari ID terbesar khusus untuk baris dari CRM (agar tidak ter-skip oleh ID baris kosong)
            let maxCrmId = 0;
            this.currentData.forEach(r => { 
                if (r && r.id && r.source === 'crm' && r.id > maxCrmId) {
                    maxCrmId = r.id; 
                }
            });
            
            try {
                // Fetch baris CRM baru yang ID-nya lebih besar dari maxCrmId
                const newData = await window.databaseManager.fetchNewData(window.activeSheetId, maxCrmId);
                if (newData && newData.length > 0) {
                    console.log(`[RealTime] Mendapatkan ${newData.length} baris baru!`);
                    
                    let inserted = 0;
                    for (let i = 0; i < newData.length; i++) {
                        const newRow = newData[i];
                        
                        // Pastikan baris belum ada
                        if (this.currentData.some(r => r && r.id === newRow.id)) continue;
                        
                        // Cari baris kosong pertama dari atas
                        let emptyIndex = this.currentData.findIndex(r => r && r.id && !r.tanggal_pickup && !r.nama);
                        
                        if (emptyIndex !== -1) {
                            // Replace baris kosong dengan baris baru
                            this.currentData[emptyIndex] = newRow;
                            if (this.originalData) this.originalData[emptyIndex] = JSON.parse(JSON.stringify(newRow));
                        } else {
                            // Jika tidak ada baris kosong, tambahkan di bawah
                            this.currentData.push(newRow);
                            if (this.originalData) this.originalData.push(JSON.parse(JSON.stringify(newRow)));
                        }
                        inserted++;
                    }
                    
                    if (inserted > 0) {
                        this._initRowMap();
                        this._initializeFormulas();
                        if (this.virtualScroller) {
                            this.virtualScroller.setData(this.currentData);
                        }
                        // Tampilkan toast hijau
                        const toast = document.createElement('div');
                        toast.className = 'toast show';
                        toast.style.backgroundColor = 'var(--success)';
                        toast.innerHTML = `<i class="fas fa-check-circle"></i> ${inserted} data Lead baru dari CRM berhasil disinkronisasi!`;
                        document.body.appendChild(toast);
                        setTimeout(() => toast.remove(), 4000);
                    }
                }
            } catch (err) {
                console.warn('[RealTime] Error polling:', err);
                if (err.message && (err.message.includes('401') || err.message.includes('403'))) {
                    console.warn('[RealTime] Unauthorized or session expired. Stopping realtime sync.');
                    clearInterval(this.syncInterval);
                }
            }
        }, 3000);
    }

    // ==================== INITIALIZATION ====================

    ctb(r) { return window.formulaEngine.compute('total_biaya', r); }
    cp(r) { return window.formulaEngine.compute('profit', r); }
    cpj(r) { return window.formulaEngine.compute('penjualan', r); }
    gpc(r) { return this.cp(r) >= 0 ? 'cell-profit-positive' : 'cell-profit-negative'; }

    // ==================== LAST EDIT INFO ====================

    showLastEditInfo(id) {
        const el = document.getElementById('lastEditInfo');
        if (!el) return;
        if (!id || id.startsWith('preload_')) { el.textContent = ''; return; }
        const row = (this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id));
        if (!row) { el.textContent = ''; return; }
        const ub = row.updated_by || '-';
        const ua = row.updated_at
            ? new Date(row.updated_at).toLocaleString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '-';
        el.innerHTML = '<i class="fas fa-pen" style="font-size:0.65rem;"></i> Edit terakhir: ' + ub + ' — ' + ua;
    }

    // ==================== REMOTE SYNC ====================

    updateRemoteCell(id, f, v, editor) {
        if (this.editingCell?.id == id && this.editingCell?.field == f) return;
        this.updateCellValue(id, f, v);
        
        const user = window.authManager?.currentUser;
        const currentUser = user ? (user.config?.name || user.email || 'Unknown') : null;
        const isSelf = editor && currentUser && editor === currentUser;

        const td = document.querySelector('td[data-field="' + f + '"][data-id="' + id + '"]');
        if (td && !td.classList.contains('cell-editing')) {
            this.renderCellDisplay(td, f, id);
            this.updateRelatedCells(id);
            const cd = td.querySelector('.cell-display');
            if (cd && !isSelf) {
                cd.classList.add('cell-remote-edit');
                if (editor) cd.title = 'Diedit oleh: ' + editor;
                setTimeout(() => cd.classList.remove('cell-remote-edit'), 2000);
            }
        }
        if (this.activeCell?.dataset?.id == id) {
            this.showLastEditInfo(id);
        }
    }

    addRemoteRow(row) {
        if (this.currentData.some(r => r && r.id == row.id)) return;
        this.currentData.push(row);
        this.originalData.push(row);
        const activeId = this.editingCell?.id;
        const activeField = this.editingCell?.field;
        this.renderTable(this.currentData);
        if (activeId && activeField) {
            const ntd = document.querySelector('td[data-id="' + activeId + '"][data-field="' + activeField + '"]');
            if (ntd) {
                ntd.classList.add('cell-editing');
                this.editingCell.td = ntd;
                const input = ntd.querySelector('input');
                if (input) input.focus();
            }
        }
    }

    // ==================== DATA HELPERS ====================

    getRawValue(id, f) {
        const r = (this.rowMap ? this.rowMap.get(String(id)) : this.currentData.find(r => r && r.id == id));
        if (!r) return '';
        const v = r[f];
        return v === null || v === undefined ? '' : v;
    }

    getFieldType(f) {
        if (f === 'tanggal_pickup') return 'date';
        const numFields = ['harga', 'surcharge', 'packing', 'handling', 'penjualan', 'aktual', 'vol', 'nilai_barang', 'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv', 'ops', 'asuransi', 'asuransi_jasindo', 'total_biaya', 'profit', 'unit', 'koil', 'kubik', 'p', 'l', 't', 'idx_profit'];
        if (numFields.includes(f)) return 'number';
        return 'text';
    }

    // ==================== FORMAT HELPERS ====================

    fmtDate(d) {
        if (!d) return '';
        const parts = String(d).split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return this.esc(d);
    }

    fmtNum(n, decimals = null) {
        const v = parseFloat(n);
        if (isNaN(v) || v === 0) return '0';
        const d = decimals !== null ? decimals : 3;
        return new Intl.NumberFormat('en-US', { minimumFractionDigits: 0, maximumFractionDigits: d }).format(v);
    }

    fmtInt(n) {
        const v = parseInt(n);
        if (isNaN(v) || v === 0) return '0';
        return String(v);
    }

    fmtDec(n, decimals = null) {
        const v = parseFloat(n);
        if (isNaN(v)) return '0.0000';
        const d = decimals !== null ? decimals : 4;
        return v.toFixed(d);
    }

    fmtC(a, decimals = null) {
        const v = parseFloat(a) || 0;
        const d = decimals !== null ? decimals : 0;
        const numStr = new Intl.NumberFormat('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
        return '<span class="rp-label">Rp</span><span class="rp-value">' + numStr + '</span>';
    }

    _td(id, f, v, cn, ridx, cidx) {
        const isSelected = ridx >= this.selectedRange.sr && ridx <= this.selectedRange.er && cidx >= this.selectedRange.sc && cidx <= this.selectedRange.ec;
        const isActive = ridx === this.activeCellPos.r && cidx === this.activeCellPos.c;
        const sClass = isSelected ? ' cell-selected' : '';
        const aClass = isActive ? ' cell-active' : '';
        const roClass = !this.isCellEditable(id, f) ? ' cell-readonly' : '';

        const row = this.currentData[ridx];
        let inlineStyle = '';
        let extCls = '';
        let alignStyle = '';
        let titleAttr = '';

        if (window.formulaEngine && window.formulaEngine.cellErrors) {
            const errorMsg = window.formulaEngine.cellErrors.get(`${id}:${f}`);
            if (errorMsg) {
                extCls += ' cell-error';
                titleAttr = errorMsg === '#CIRCULAR' ? ' title="⚠ Referensi melingkar (Circular Reference)"' : ' title="⚠ Kesalahan Formula (#ERROR)"';
            }
        }
        let fObj = row ? row.formulas : null;
        while (typeof fObj === 'string') { try { let parsed = JSON.parse(fObj); if (typeof parsed === 'string' && parsed === fObj) break; fObj = parsed; } catch (e) { fObj = null; break; } }

        if (fObj && fObj.__formats && fObj.__formats[f]) {
            const format = fObj.__formats[f];
            if (format.locked) extCls += ' cell-locked';
            if (format.bold) inlineStyle += 'font-weight:bold;';
            if (format.italic) inlineStyle += 'font-style:italic;';
            if (format.underline) inlineStyle += 'text-decoration:underline;';
            if (format.bgColor) inlineStyle += `background-color:${format.bgColor} !important;`;

            if (format.align) {
                const justify = format.align === 'right' ? 'flex-end' : (format.align === 'center' ? 'center' : 'flex-start');
                alignStyle = ` style="text-align:${format.align};width:100%;height:100%;display:flex;align-items:center;justify-content:${justify};"`;
            }
        }
        let commentHTML = '';
        if (fObj && fObj.__comments && fObj.__comments[f]) {
            commentHTML = `<div class="cell-comment-indicator" data-comment="${fObj.__comments[f].replace(/"/g, '&quot;')}"></div>`;
        }

        return `<td data-id="${id}" data-field="${f}" class="${cn}${sClass}${aClass}${roClass}${extCls}"${titleAttr} style="${inlineStyle}">
            <div class="cell-display ${cn}"${alignStyle}>${v}</div>${commentHTML}
        </td>`;
    }

    isColEditable(f) {
        if (!f || !window.authManager) return false;
        return window.authManager.canEdit(null, f);
    }

    isCellEditable(rowOrId, field) {
        if (!field) return false;

        let row = null;
        if (typeof rowOrId === 'object' && rowOrId !== null) {
            row = rowOrId;
        } else if (rowOrId) {
            row = this.rowMap ? this.rowMap.get(String(rowOrId)) : this.currentData.find(r => r && r.id == rowOrId);
        }

        if (!this.isColEditable(field)) return false;

        let formulasObj = row ? row.formulas : null;
        if (formulasObj && typeof formulasObj === 'string') {
            try { formulasObj = JSON.parse(formulasObj); } catch (e) { formulasObj = {}; }
        }

        // Check if locked via format toggle
        if (formulasObj && formulasObj.__formats && formulasObj.__formats[field] && formulasObj.__formats[field].locked) {
            return false;
        }

        const cfg = this.sheetConfig ? this.sheetConfig[field] : null;
        if (cfg && cfg.autoCalc === true) {
            if (row) {
                if (window.formulaEngine && window.formulaEngine.isRowExcludedForField(row, field)) {
                    return true;
                }
                if (formulasObj) {
                    if (typeof formulasObj === 'string') {
                        try { formulasObj = JSON.parse(formulasObj); } catch (e) { formulasObj = null; }
                    }
                    if (formulasObj && formulasObj[field] !== undefined) {
                        return true;
                    }
                }
            }
            return false;
        }

        return true;
    }

    isReadOnlyUser() {
        if (!window.authManager) return true;
        return !window.authManager.hasAnyEditPermission();
    }

    fmtP(n, decimals = null) {
        if (n === null || n === undefined || n === '') return '';
        if (typeof n === 'string' && n.startsWith('#')) return n;
        const v = parseFloat(n);
        if (isNaN(v) || v === 0) return '';
        if (!isFinite(v)) return '—';
        const d = decimals !== null ? decimals : 0;
        return (v * 100).toFixed(d) + '%';
    }

    esc(t) {
        const m = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return String(t || '').replace(/[&<>"']/g, c => m[c]);
    }

    // ==================== PRESENCE & REMOTE CURSOR ====================

    initPresence() {
        const user = authManager.currentUser;
        if (!user) return;

        // Cleanup existing channel if any
        if (this.presenceChannel) {
            supabaseClient.removeChannel(this.presenceChannel);
        }

        this.presenceChannel = supabaseClient.channel('spreadsheet_presence', {
            config: {
                presence: { key: (typeof TAB_ID !== 'undefined' && TAB_ID) ? TAB_ID : ('tab_' + Math.random().toString(36).substr(2, 5)) },
                broadcast: { self: false, ack: false }
            }
        });

        console.log('📡 Spreadsheet Realtime Channel Initialized:', this.presenceChannel.topic);

        this.presenceChannel
            .on('presence', { event: 'sync' }, () => {
                const state = this.presenceChannel.presenceState();
                this.renderRemoteCursors();
            })
            .on('broadcast', { event: 'cell_update' }, ({ payload }) => {
                // INSTANT UPDATE: Terima data langsung dari browser user lain (mili-detik)
                console.log('⚡ Received Instant Broadcast:', payload);
                const { id, field, value, editor } = payload;
                this.updateRemoteCell(id, field, value, editor);
            })
            .on('postgres_changes', {
                event: '*',
                schema: 'public',
                table: window.databaseManager.tableName
            }, (payload) => {
                // DATABASE SYNC: Pastikan data akurat dengan apa yang tersimpan di DB
                console.log('📊 DB Realtime Update:', payload.eventType, payload.new);
                if (payload.eventType === 'UPDATE' || payload.eventType === 'INSERT') {
                    const row = payload.new;
                    if (row && row.id) {
                        const isUpdate = this.currentData.some(r => r && r.id == row.id);
                        if (isUpdate) {
                            // Update existing fields that might have changed
                            Object.keys(row).forEach(field => {
                                if (field !== 'id') this.updateRemoteCell(row.id, field, row[field], row.updated_by);
                            });
                        } else {
                            this.addRemoteRow(row);
                        }
                    }
                }
            })
            .subscribe(async (status) => {
                if (status === 'SUBSCRIBED') {
                    await this.broadcastPresence();
                }
            });
    }

    async broadcastPresence() {
        if (!this.presenceChannel || !authManager.currentUser) return;

        const user = authManager.currentUser;
        const state = {
            name: user.config?.name || user.email,
            email: user.email,
            selection: { ...this.selectedRange },
            activeCell: { ...this.activeCellPos },
            color: this.getUserColor(user.email),
            updated_at: new Date().getTime()
        };

        try {
            await this.presenceChannel.track(state);
        } catch (e) {
            console.error('❌ Failed to track presence:', e.message);
        }
    }

    renderRemoteCursors() {
        const presences = this.presenceChannel.presenceState();
        const myTab = typeof TAB_ID !== 'undefined' ? TAB_ID : null;

        // Bersihkan cursor lama
        document.querySelectorAll('.remote-cursor, .cell-remote-selected').forEach(el => {
            el.classList.remove('cell-remote-selected');
            el.style.removeProperty('--remote-color');
            if (el.classList.contains('remote-cursor')) el.remove();
        });

        if (!this._remotePos) this._remotePos = {};

        Object.keys(presences).forEach(tabId => {
            if (tabId === myTab) return;
            const state = presences[tabId][0];
            if (!state || !state.selection) return;

            const { sr, er, sc, ec } = state.selection;
            const { r, c } = state.activeCell;
            const color = state.color || '#ff0000';

            // Detect movement
            const posKey = `${r}:${c}`;
            const isMoving = this._remotePos[tabId] && this._remotePos[tabId] !== posKey;
            this._remotePos[tabId] = posKey;

            // Highlight Range
            document.querySelectorAll('#kpiTableBody tr.spreadsheet-row').forEach(tr => {
                const ridx = parseInt(tr.dataset.idx);
                if (ridx >= sr && ridx <= er) {
                    for (let cidx = sc; cidx <= ec; cidx++) {
                        const td = tr.cells[cidx];
                        if (td) {
                            td.classList.add('cell-remote-selected');
                            td.style.setProperty('--remote-color', color);
                        }
                    }
                }
            });

            // Draw Cursor on Active Cell
            const activeTr = document.querySelector(`#kpiTableBody tr[data-idx="${r}"]`);
            if (activeTr) {
                const activeTd = activeTr.cells[c];
                if (activeTd) {
                    const cursor = document.createElement('div');
                    cursor.className = 'remote-cursor' + (isMoving ? ' is-moving' : '');
                    cursor.style.setProperty('--remote-color', color);

                    // Prevent label from being cut off by the sticky header
                    const rect = activeTd.getBoundingClientRect();
                    const isTooHigh = rect.top < 180; // Approximate threshold for sticky header + toolbar

                    cursor.innerHTML = `<span class="remote-cursor-label ${isTooHigh ? 'label-bottom' : ''}" style="background:${color}">${state.name}</span>`;
                    activeTd.appendChild(cursor);

                    // Remove movement class after 3 seconds
                    if (isMoving) {
                        setTimeout(() => cursor.classList.remove('is-moving'), 3000);
                    }
                }
            }
        });
    }

    removeRemoteCursor(email) {
        // Otomatis terhandle oleh renderRemoteCursors saat event 'leave' mentrigger 'sync'
        this.renderRemoteCursors();
    }

    getUserColor(email) {
        let hash = 0;
        for (let i = 0; i < email.length; i++) {
            hash = email.charCodeAt(i) + ((hash << 5) - hash);
        }
        const colors = ['#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#03a1f4', '#00bcd4', '#009688', '#4caf50', '#8bc34a', '#ffc107', '#ff9800', '#ff5722'];
        return colors[Math.abs(hash) % colors.length];
    }

    // ==================== UI STATUS ====================

    setSyncStatus(s) {
        const d = document.getElementById('syncDot'), t = document.getElementById('syncText');
        if (d) d.className = 'sync-dot ' + s;
        if (t) t.textContent = { synced: 'Tersimpan', syncing: 'Menyimpan...', error: 'Error!' }[s] || s;
    }

    // ==================== CUSTOM FORMULA DIALOG ====================

    showCustomFormulaDialog() {
        if (!this.activeCell && !this.selectedCells.length) {
            this.updateStatusBar('⚠ Pilih cell terlebih dahulu');
            return;
        }

        // Remove existing dialog if any
        const existing = document.getElementById('customFormulaDialog');
        if (existing) existing.remove();

        const td = this.activeCell || this.selectedCells[0];
        const f = td?.dataset?.field;
        const id = td?.dataset?.id;
        const currentVal = (f && id) ? this.getRawValue(id, f) : 0;

        const dialog = document.createElement('div');
        dialog.id = 'customFormulaDialog';
        dialog.className = 'custom-formula-overlay';
        dialog.innerHTML = `
            <div class="custom-formula-modal">
                <div class="custom-formula-header">
                    <span><i class="fas fa-calculator" style="color:var(--red)"></i> Custom Formula</span>
                    <button onclick="document.getElementById('customFormulaDialog').remove()" class="btn-close-formula">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="custom-formula-body">
                    <div class="formula-hint">
                        <i class="fas fa-info-circle" style="color:#3b82f6"></i>
                        Nilai saat ini: <strong>${currentVal}</strong> | Gunakan <code>x</code> untuk merujuk nilai sel
                    </div>
                    <div class="formula-examples">
                        <span class="formula-chip" onclick="document.getElementById('formulaInput').value='x * 1.1'">× 1.1</span>
                        <span class="formula-chip" onclick="document.getElementById('formulaInput').value='x + 1000'">+ 1000</span>
                        <span class="formula-chip" onclick="document.getElementById('formulaInput').value='x - 500'">- 500</span>
                        <span class="formula-chip" onclick="document.getElementById('formulaInput').value='x / 2'">÷ 2</span>
                        <span class="formula-chip" onclick="document.getElementById('formulaInput').value='x * 10 / 100'">10%</span>
                        <span class="formula-chip" onclick="document.getElementById('formulaInput').value='x * 1.05'">+5%</span>
                    </div>
                    <div class="formula-input-row">
                        <span class="formula-eq">ƒ =</span>
                        <input type="text" id="formulaInput" class="formula-input" placeholder="Contoh: x * 1.1 atau x + 500 atau x * 20%" value="">
                    </div>
                    <div id="formulaPreview" class="formula-preview">Preview: —</div>
                </div>
                <div class="custom-formula-footer">
                    <button class="btn-formula-cancel" onclick="document.getElementById('customFormulaDialog').remove()">Batal</button>
                    <button class="btn-formula-apply" onclick="tableManager.applyCustomFormula()">
                        <i class="fas fa-check"></i> Terapkan ke ${this.selectedCells.length > 1 ? this.selectedCells.length + ' Cell' : 'Cell Ini'}
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(dialog);

        const input = document.getElementById('formulaInput');
        const preview = document.getElementById('formulaPreview');

        const evalFormula = (expr, val) => {
            try {
                const xVal = parseFloat(val) || 0;
                // Replace x with value and handle %
                const safe = expr.replace(/(\d+)\s*%/g, '($1/100)').replace(/\bx\b/g, String(xVal));
                // Only allow safe math chars
                if (/[^0-9+\-*/.() ]/.test(safe)) return null;
                // eslint-disable-next-line no-new-func
                const result = Function('"use strict"; return (' + safe + ')')();
                return isNaN(result) ? null : result;
            } catch { return null; }
        };

        input.addEventListener('input', () => {
            const result = evalFormula(input.value, currentVal);
            preview.textContent = result !== null ? `Preview: ${result.toLocaleString('en-US')}` : 'Preview: Formula tidak valid';
            preview.style.color = result !== null ? '#22c55e' : '#ef4444';
        });

        setTimeout(() => { input.focus(); }, 100);

        // Close on overlay click
        dialog.addEventListener('click', (e) => { if (e.target === dialog) dialog.remove(); });

        // Allow Enter key
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); this.applyCustomFormula(); }
            if (e.key === 'Escape') { e.preventDefault(); dialog.remove(); }
        });
    }

    applyCustomFormula() {
        const input = document.getElementById('formulaInput');
        if (!input) return;
        const expr = input.value.trim();
        if (!expr) return;

        if (this.isReadOnlyUser()) { this.updateStatusBar('⚠ Mode read-only.'); return; }

        const evalFormula = (expr, val) => {
            try {
                const xVal = parseFloat(val) || 0;
                const safe = expr.replace(/(\d+)\s*%/g, '($1/100)').replace(/\bx\b/g, String(xVal));
                if (/[^0-9+\-*/.() ]/.test(safe)) return null;
                // eslint-disable-next-line no-new-func
                const result = Function('"use strict"; return (' + safe + ')')();
                return isNaN(result) ? null : result;
            } catch { return null; }
        };

        const targets = this.selectedCells.length > 0 ? this.selectedCells : (this.activeCell ? [this.activeCell] : []);
        const ba = [];
        const ai = new Set();

        targets.forEach(td => {
            const id = td.dataset.id, f = td.dataset.field;
            if (!id || !f || id.startsWith('preload_')) return;
            if (!this.isColEditable(f)) return;
            if (this.getFieldType(f) !== 'number') return;
            const ov = this.getRawValue(id, f);
            const result = evalFormula(expr, ov);
            if (result === null) return;
            const pv = Math.round(result * 100) / 100; // Round to 2 decimals
            ba.push({ id, field: f, oldValue: ov, newValue: pv });
            this.updateCellValue(id, f, pv);
            this.renderCellDisplay(td, f, id);
            this.queueSave(id, f, pv);
            ai.add(id);
        });

        if (ba.length) { this.history.push({ type: 'batch', actions: ba }); }
        ai.forEach(id => this.updateRelatedCells(id));
        this.flushSaveQueue();
        this.updateStatusBar(`✓ Formula diterapkan ke ${ba.length} cell`);

        const dialog = document.getElementById('customFormulaDialog');
        if (dialog) dialog.remove();
    }

    _initFormulaAutocomplete() {
        const list = document.createElement('div');
        list.id = 'formulaAutocomplete';
        list.className = 'formula-autocomplete';
        list.style.display = 'none';
        document.body.appendChild(list);
        this.autocompleteList = list;

        this.formulaTemplates = [
            { name: 'SUM', hint: 'SUM(range)', template: 'SUM(' },
            { name: 'AVERAGE', hint: 'AVERAGE(range)', template: 'AVERAGE(' },
            { name: 'COUNT', hint: 'COUNT(range)', template: 'COUNT(' },
            { name: 'COUNTA', hint: 'COUNTA(range)', template: 'COUNTA(' },
            { name: 'MAX', hint: 'MAX(range)', template: 'MAX(' },
            { name: 'MIN', hint: 'MIN(range)', template: 'MIN(' },
            { name: 'IF', hint: 'IF(test, true, false)', template: 'IF(' },
            { name: 'SUBTOTAL', hint: 'SUBTOTAL(fn, range)', template: 'SUBTOTAL(' },
            { name: 'PRODUCT', hint: 'PRODUCT(range)', template: 'PRODUCT(' },
            { name: 'ROUND', hint: 'ROUND(val, digits)', template: 'ROUND(' },
            { name: 'IFERROR', hint: 'IFERROR(val, fallback)', template: 'IFERROR(' },
            { name: 'ABS', hint: 'ABS(value)', template: 'ABS(' }
        ];

        document.addEventListener('mousedown', (e) => {
            if (this.autocompleteList && !this.autocompleteList.contains(e.target)) {
                this.hideAutocomplete();
            }
        });
    }

    showAutocomplete(input) {
        const val = input.value;
        if (!val.startsWith('=')) { this.hideAutocomplete(); return; }

        // Extract the last part after operators or commas
        let parts = val.split(/[\+\-\*\/\(\,]/);
        let lastPart = parts.pop().toUpperCase();

        // If it starts with =, remove it for comparison
        if (lastPart.startsWith('=')) lastPart = lastPart.substring(1);

        if (lastPart.length < 1) { this.hideAutocomplete(); return; }

        const matches = Object.keys(window.formulaEngine.functionMetadata)
            .filter(name => name.startsWith(lastPart))
            .map(name => ({ name, ...window.formulaEngine.functionMetadata[name] }));

        if (matches.length === 0) { this.hideAutocomplete(); return; }

        const rect = input.getBoundingClientRect();
        this.autocompleteList.style.left = rect.left + 'px';
        this.autocompleteList.style.top = (rect.bottom + window.scrollY + 5) + 'px';
        this.autocompleteList.style.minWidth = '320px';
        this.autocompleteList.style.display = 'block';
        this.autocompleteList.style.zIndex = '10001';

        this.autocompleteList.innerHTML = matches.map((m, idx) => `
            <div class="autocomplete-item ${idx === 0 ? 'active' : ''}" 
                 data-template="${m.name}(" 
                 data-lastpart="${lastPart}"
                 onmousedown="tableManager.applyAutocomplete(this.dataset.template, this.dataset.lastpart)">
                <div class="auto-header">
                    <span class="auto-name">${m.name}</span>
                    <span class="auto-syntax">${m.syntax}</span>
                </div>
                <div class="auto-desc">${m.desc}</div>
                <div class="auto-example">Contoh: <code>${m.example}</code></div>
            </div>
        `).join('');
    }

    applyAutocomplete(template, lastPart) {
        // Find input (formulaBar or cellFloatingEditor input)
        const input = document.activeElement;
        if (!input || (input.id !== 'formulaBar' && !input.classList.contains('cell-editor-input'))) return;

        const val = input.value;
        const index = val.toUpperCase().lastIndexOf(lastPart);
        if (index !== -1) {
            input.value = val.substring(0, index) + template;
            input.focus();
            this.hideAutocomplete();
        }
    }

    hideAutocomplete() {
        if (this.autocompleteList) this.autocompleteList.style.display = 'none';
    }

    _insertReferenceIntoEditor(inp, ref, isReplacingLast = false) {
        const val = inp.value;
        const pos = inp.selectionStart;

        if (isReplacingLast) {
            // Replace the last A1:A1 or A1 reference being built
            const lastPartMatch = val.match(/([A-Z]+\d+(:[A-Z]+\d+)?)$/);
            if (lastPartMatch) {
                inp.value = val.substring(0, lastPartMatch.index) + ref;
            } else {
                inp.value = val + ref;
            }
        } else {
            // Check if we should add a comma/operator or just append
            const lastChar = val.slice(-1);
            const needsSeparator = val.length > 1 && !['(', ',', '+', '-', '*', '/', ':'].includes(lastChar);
            const separator = needsSeparator ? ',' : '';

            inp.value = val.substring(0, pos) + separator + ref + val.substring(pos);
        }

        inp.focus();
        this.highlightReferencedCells(inp.value);
        const fb = document.getElementById('formulaBar');
        if (fb) fb.value = inp.value;
    }

    updateStatusBar(m) {
        const el = document.getElementById('cellInfo');
        if (el) el.textContent = m;
    }
}

// ==================== VIRTUAL SCROLLER ====================
class VirtualScroller {
    constructor(container, tbody, tableManager) {
        this.container = container;
        this.tbody = tbody;
        this.tableManager = tableManager;
        this.ROW_HEIGHT = 36; // Approx height per row
        this.OVERSCAN = 35; // Increase overscan to buffer more rows natively
        this.data = [];
        this.totalRows = 0;
        this.scrollTop = 0;
        this.renderedStart = -1;
        this.renderedEnd = -1;
        this.isRendering = false;

        this.spacerTop = document.createElement('tr');
        this.spacerTop.innerHTML = '<td colspan="42" style="padding:0; border:0; height:0px;"></td>';
        this.spacerBottom = document.createElement('tr');
        this.spacerBottom.innerHTML = '<td colspan="42" style="padding:0; border:0; height:0px;"></td>';

        this.container.addEventListener('scroll', () => {
            if (!this.isRendering) {
                requestAnimationFrame(() => this._checkRender());
            }
        }, { passive: true });
    }

    setData(data) {
        this.data = data;
        this.totalRows = data.length;
        this.scrollTop = this.container.scrollTop;
        this.renderedStart = -1;
        this.renderedEnd = -1;
        this._checkRender(true);
    }

    _checkRender(force = false) {
        if (this.totalRows === 0) return;

        const scrollTop = this.container.scrollTop;
        const viewportH = this.container.clientHeight || 600;
        
        const currentStart = Math.floor(scrollTop / this.ROW_HEIGHT);
        const currentEnd = Math.ceil((scrollTop + viewportH) / this.ROW_HEIGHT);

        // Render only if forced, or getting close to the edge of the overscan (within 15 rows)
        if (force || this.renderedStart === -1 || currentStart < this.renderedStart + 15 || currentEnd > this.renderedEnd - 15) {
            this._render(currentStart, currentEnd, force);
        }
    }

    /**
     * Force an immediate synchronous render based on current scroll position.
     * Used by keyboard navigation to guarantee the target row is in DOM.
     */
    _forceRender() {
        if (this.totalRows === 0) return;
        const scrollTop = this.container.scrollTop;
        const viewportH = this.container.clientHeight || 600;
        const currentStart = Math.floor(scrollTop / this.ROW_HEIGHT);
        const currentEnd = Math.ceil((scrollTop + viewportH) / this.ROW_HEIGHT);
        this._render(currentStart, currentEnd, true);
    }

    /**
     * Engine render Virtual Scroller
     * Fungsi ini bertugas menggambar tabel hanya pada rentang (range) sel yang terlihat
     * di layar pengguna, untuk mencegah freeze pada dataset 100.000+ baris.
     */
    _render(currentStart, currentEnd, force = false) {
        this.isRendering = true;
        
        let start = currentStart - this.OVERSCAN;
        let end = currentEnd + this.OVERSCAN;

        start = Math.max(0, start);
        end = Math.min(this.totalRows - 1, end);

        // Skip DOM update only if range unchanged AND this is NOT a forced render
        if (!force && start === this.renderedStart && end === this.renderedEnd) {
            this.isRendering = false;
            return;
        }

        this.renderedStart = start;
        this.renderedEnd = end;

        let html = '';
        for (let i = start; i <= end; i++) {
            html += this.tableManager.createRowHTML(this.data[i], i);
        }

        this.tbody.innerHTML = html;

        const topHeight = start * this.ROW_HEIGHT;
        const bottomHeight = Math.max(0, (this.totalRows - 1 - end) * this.ROW_HEIGHT);

        this.spacerTop.querySelector('td').style.height = topHeight + 'px';
        this.spacerBottom.querySelector('td').style.height = bottomHeight + 'px';

        this.tbody.prepend(this.spacerTop);
        this.tbody.append(this.spacerBottom);

        this._reapplySelection();
        this.isRendering = false;
    }

    _reapplySelection() {
        const { sr, er, sc, ec } = this.tableManager.selectedRange;
        const ap = this.tableManager.activeCellPos;

        // Clear all
        this.tbody.querySelectorAll('.cell-active, .cell-selected, .cell-editing, .row-active').forEach(el => {
            el.classList.remove('cell-active', 'cell-selected', 'cell-editing', 'row-active');
        });

        // 1. Re-apply Active Cell
        if (ap.r !== -1) {
            const tr = this.tbody.querySelector(`tr[data-idx="${ap.r}"]`);
            if (tr) {
                const td = tr.cells[ap.c];
                if (td) {
                    td.classList.add('cell-active');
                    tr.classList.add('row-active');
                    this.tableManager.activeCell = td;
                }
            }
        }

        // 2. Re-apply Selected Range
        if (sr !== -1) {
            this.tbody.querySelectorAll('tr.spreadsheet-row').forEach(tr => {
                const ridx = parseInt(tr.dataset.idx);
                if (ridx >= sr && ridx <= er) {
                    for (let cidx = sc; cidx <= ec; cidx++) {
                        const td = tr.cells[cidx];
                        if (td && !td.classList.contains('col-index') && !td.classList.contains('col-actions')) {
                            td.classList.add('cell-selected');
                        }
                    }
                }
            });
        }

        // 3. Re-apply Remote Cursors (Presence)
        if (this.tableManager.presenceChannel) {
            this.tableManager.renderRemoteCursors();
        }

        // 4. Re-position the highlight overlay
        if (this.tableManager.selectionManager) {
            this.tableManager.selectionManager._updateHighlightOverlay(this.tableManager.activeCell);
        }
    }
}

// Global instance initialization with race condition protection
function initTableManager() {
    if (!window.tableManager) {
        window.tableManager = new TableManager();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTableManager);
} else {
    initTableManager();
}



