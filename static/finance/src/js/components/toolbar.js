/**
 * SPREADSHEET TOOLBAR v2.0
 */
class SpreadsheetToolbar {
    constructor(tableManager) {
        this.tableManager = tableManager;
        this.el = null;
    }

    init() {
        this._buildToolbar();
        this._bindEvents();
    }

    _buildToolbar() {
        const container = document.querySelector('.toolbar-container');
        if (!container) return;

        // Prevent double toolbar by clearing previous ones
        container.innerHTML = '';

        this.el = document.createElement('div');
        this.el.className = 'spreadsheet-toolbar';
        this.el.innerHTML = `
            <div class="toolbar-group">
                <div class="sync-indicator">
                    <span class="sync-dot synced" id="syncDot"></span>
                    <span id="syncText" class="sync-text">Tersimpan</span>
                </div>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
                <button class="btn-toolbar" data-action="undo" title="Undo (Ctrl+Z)"><i class="ph-duotone ph-arrow-u-up-left"></i></button>
                <button class="btn-toolbar" data-action="redo" title="Redo (Ctrl+Y)"><i class="ph-duotone ph-arrow-u-up-right"></i></button>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
                <button class="btn-toolbar" data-style="bold" title="Bold (Ctrl+B)"><i class="ph-bold ph-text-b"></i></button>
                <button class="btn-toolbar" data-style="italic" title="Italic (Ctrl+I)"><i class="ph-bold ph-text-italic"></i></button>
                <button class="btn-toolbar" data-style="underline" title="Underline (Ctrl+U)"><i class="ph-bold ph-text-underline"></i></button>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
                <button class="btn-toolbar" data-format="currency" title="Format Currency"><i class="ph-duotone ph-coins"></i></button>
                <button class="btn-toolbar" data-format="percent" title="Format Percent"><i class="ph-duotone ph-percent"></i></button>
                <button class="btn-toolbar" data-format="number" title="Format Number"><i class="ph-duotone ph-hash"></i></button>
            </div>

            <div class="toolbar-divider"></div>
            <div class="toolbar-group" style="position: relative;">
                <button class="btn-toolbar" id="btnColorPalette" title="Fill Color"><i class="ph-duotone ph-paint-bucket"></i></button>
                <div id="colorPaletteDropdown" class="color-palette-dropdown hidden">
                    <div class="color-swatch" style="border: 1px solid #ddd;" data-color="" title="Reset"></div>
                    <div class="color-swatch" style="background-color: #000000;" data-color="#000000" title="Black"></div>
                    <div class="color-swatch" style="background-color: #434343;" data-color="#434343" title="Dark Gray 4"></div>
                    <div class="color-swatch" style="background-color: #666666;" data-color="#666666" title="Dark Gray 3"></div>
                    <div class="color-swatch" style="background-color: #999999;" data-color="#999999" title="Dark Gray 2"></div>
                    <div class="color-swatch" style="background-color: #b7b7b7;" data-color="#b7b7b7" title="Dark Gray 1"></div>
                    <div class="color-swatch" style="background-color: #cccccc;" data-color="#cccccc" title="Gray"></div>
                    <div class="color-swatch" style="background-color: #d9d9d9;" data-color="#d9d9d9" title="Light Gray 1"></div>
                    <div class="color-swatch" style="background-color: #efefef;" data-color="#efefef" title="Light Gray 2"></div>
                    <div class="color-swatch" style="background-color: #f3f3f3;" data-color="#f3f3f3" title="Light Gray 3"></div>
                    
                    <div class="color-swatch" style="background-color: #980000;" data-color="#980000" title="Red Berry"></div>
                    <div class="color-swatch" style="background-color: #ff0000;" data-color="#ff0000" title="Red"></div>
                    <div class="color-swatch" style="background-color: #ff9900;" data-color="#ff9900" title="Orange"></div>
                    <div class="color-swatch" style="background-color: #ffff00;" data-color="#ffff00" title="Yellow"></div>
                    <div class="color-swatch" style="background-color: #00ff00;" data-color="#00ff00" title="Green"></div>
                    <div class="color-swatch" style="background-color: #00ffff;" data-color="#00ffff" title="Cyan"></div>
                    <div class="color-swatch" style="background-color: #4a86e8;" data-color="#4a86e8" title="Cornflower Blue"></div>
                    <div class="color-swatch" style="background-color: #0000ff;" data-color="#0000ff" title="Blue"></div>
                    <div class="color-swatch" style="background-color: #9900ff;" data-color="#9900ff" title="Purple"></div>
                    <div class="color-swatch" style="background-color: #ff00ff;" data-color="#ff00ff" title="Magenta"></div>
                    
                    <div class="color-swatch" style="background-color: #e6b8af;" data-color="#e6b8af" title="Light Red 3"></div>
                    <div class="color-swatch" style="background-color: #f4cccc;" data-color="#f4cccc" title="Light Red 2"></div>
                    <div class="color-swatch" style="background-color: #fce5cd;" data-color="#fce5cd" title="Light Orange"></div>
                    <div class="color-swatch" style="background-color: #fff2cc;" data-color="#fff2cc" title="Light Yellow"></div>
                    <div class="color-swatch" style="background-color: #d9ead3;" data-color="#d9ead3" title="Light Green"></div>
                    <div class="color-swatch" style="background-color: #d0e0e3;" data-color="#d0e0e3" title="Light Cyan"></div>
                    <div class="color-swatch" style="background-color: #c9daf8;" data-color="#c9daf8" title="Light Cornflower Blue"></div>
                    <div class="color-swatch" style="background-color: #cfe2f3;" data-color="#cfe2f3" title="Light Blue"></div>
                    <div class="color-swatch" style="background-color: #d9d2e9;" data-color="#d9d2e9" title="Light Purple"></div>
                    <div class="color-swatch" style="background-color: #ead1dc;" data-color="#ead1dc" title="Light Magenta"></div>
                </div>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
                <button class="btn-toolbar" data-action="lock" title="Lock Cell"><i class="ph-duotone ph-lock"></i></button>
                <button class="btn-toolbar" id="btnFormulaProtect" data-action="toggle-formula-protection" title="Perlindungan Rumus: OFF (Hati-hati saat hapus massal)"><i class="ph-duotone ph-shield"></i></button>
            </div>
            <div class="toolbar-divider"></div>
            <div class="toolbar-group">
                <button class="btn-toolbar" data-action="find" title="Find & Replace (Ctrl+F)"><i class="ph-duotone ph-magnifying-glass"></i></button>
                <button class="btn-toolbar" data-action="auto-calc-config" title="Auto-Calc Config"><i class="ph-duotone ph-calculator"></i></button>
                <button class="btn-toolbar" data-action="import" title="Import Excel (Tambah Data Baru)"><i class="ph-duotone ph-file-arrow-up"></i></button>
                <button class="btn-toolbar" data-action="export" title="Export Excel"><i class="ph-duotone ph-file-xls"></i></button>
            </div>
        `;
        container.appendChild(this.el);
    }

    _bindEvents() {
        this.el.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;

            const action = btn.dataset.action;
            const style = btn.dataset.style;
            const format = btn.dataset.format;

            if (action) this._handleAction(action, btn);
            if (style) this._handleStyle(style);
            if (format) this._handleFormat(format);
        });

        const btnColorPalette = this.el.querySelector('#btnColorPalette');
        const colorPaletteDropdown = this.el.querySelector('#colorPaletteDropdown');

        if (btnColorPalette && colorPaletteDropdown) {
            btnColorPalette.addEventListener('click', (e) => {
                e.stopPropagation();
                if (colorPaletteDropdown.classList.contains('hidden')) {
                    const rect = btnColorPalette.getBoundingClientRect();
                    colorPaletteDropdown.style.top = (rect.bottom + 4) + 'px';
                    colorPaletteDropdown.style.left = rect.left + 'px';
                    colorPaletteDropdown.classList.remove('hidden');
                } else {
                    colorPaletteDropdown.classList.add('hidden');
                }
            });

            colorPaletteDropdown.addEventListener('click', (e) => {
                const swatch = e.target.closest('.color-swatch');
                if (swatch) {
                    const color = swatch.dataset.color;
                    this._handleStyle('backgroundColor', color);
                    colorPaletteDropdown.classList.add('hidden');
                }
            });

            document.addEventListener('click', (e) => {
                if (!colorPaletteDropdown.contains(e.target) && e.target !== btnColorPalette && !btnColorPalette.contains(e.target)) {
                    colorPaletteDropdown.classList.add('hidden');
                }
            });
        }
    }

    _handleAction(action, btn) {
        if (action === 'undo') this.tableManager.history.undo();
        if (action === 'redo') this.tableManager.history.redo();
        if (action === 'find') this.tableManager.openFind();
        if (action === 'export' && typeof window.exportToExcel === 'function') window.exportToExcel();
        if (action === 'import') document.getElementById('fileImportExcel').click();
        if (action === 'auto-calc-config') this.openAutoCalcConfigModal(btn);
        if (action === 'lock' && typeof this.tableManager.toggleLockCells === 'function') this.tableManager.toggleLockCells();
        if (action === 'toggle-formula-protection') this.toggleFormulaProtection(btn);
    }

    toggleFormulaProtection(btn) {
        if (!this.tableManager) return;
        
        if (!this.tableManager.sheetConfig) {
            this.tableManager.sheetConfig = {};
        }
        
        const currentState = this.tableManager.sheetConfig.formulaProtectionEnabled === true;
        const newState = !currentState;
        
        this.tableManager.sheetConfig.formulaProtectionEnabled = newState;
        
        if (this.tableManager.sheetConfigRow) {
            this.tableManager.queueSave(this.tableManager.sheetConfigRow.id, 'formulas', JSON.stringify(this.tableManager.sheetConfig));
            this.tableManager.flushSaveQueue();
        } else {
            this._saveConfigRowAsync(this.tableManager.sheetConfig);
        }
        
        if (typeof this.tableManager.updateHeaderIndicators === 'function') {
            this.tableManager.updateHeaderIndicators();
        }
        
        if (newState) {
            if (typeof showToast === 'function') showToast('Perlindungan rumus DIAKTIFKAN untuk sheet ini', 'success');
        } else {
            if (typeof showToast === 'function') showToast('Perlindungan rumus DINONAKTIFKAN untuk sheet ini', 'warning');
        }
    }

    async _saveConfigRowAsync(newConfig) {
        try {
            const rowData = {
                nama: '__SHEET_CONFIG__',
                formulas: newConfig,
                sheet_id: window.activeSheetId || 1
            };
            const newRow = await window.databaseManager.insertRow(rowData);
            this.tableManager.sheetConfigRow = newRow;
        } catch (e) {
            console.error('Failed to create sheet config row for protection toggle', e);
        }
    }

    openAutoCalcConfigModal(btn) {
        // Toggle behavior: if already open, close it and exit
        const existingDropdown = document.getElementById('autoCalcConfigDropdown');
        if (existingDropdown) {
            document.querySelectorAll('#autoCalcConfigDropdown, #autoCalcDropdownOverlay, .glass-dropdown-container, .glass-dropdown-overlay').forEach(el => el.remove());
            return;
        }

        // Clean up any stray remnants before initializing a new one
        document.querySelectorAll('#autoCalcConfigDropdown, #autoCalcDropdownOverlay, .glass-dropdown-container, .glass-dropdown-overlay').forEach(el => el.remove());

        if (!btn) {
            btn = this.el.querySelector('[data-action="auto-calc-config"]');
        }

        const overlay = document.createElement('div');
        overlay.id = 'autoCalcDropdownOverlay';
        overlay.className = 'glass-dropdown-overlay';
        overlay.addEventListener('click', () => {
            document.querySelectorAll('#autoCalcConfigDropdown, #autoCalcDropdownOverlay, .glass-dropdown-container, .glass-dropdown-overlay').forEach(el => el.remove());
        });
        document.body.appendChild(overlay);

        const dropdown = document.createElement('div');
        dropdown.id = 'autoCalcConfigDropdown';
        dropdown.className = 'glass-dropdown-container';

        const rect = btn.getBoundingClientRect();
        const buttonCenter = rect.left + rect.width / 2;

        // Premium centering dropdown behavior with responsive adaptive width
        const dropdownWidth = Math.min(720, window.innerWidth - 30);
        let dropdownLeft = rect.left + rect.width / 2 - dropdownWidth / 2;

        // Prevent overflow on the right side
        if (dropdownLeft + dropdownWidth > window.innerWidth - 15) {
            dropdownLeft = window.innerWidth - dropdownWidth - 15;
        }
        // Prevent overflow on the left side
        if (dropdownLeft < 15) {
            dropdownLeft = 15;
        }

        dropdown.style.top = `${rect.bottom + 8}px`;
        dropdown.style.left = `${dropdownLeft}px`;

        const arrowLeft = buttonCenter - dropdownLeft;

        const config = this.tableManager.sheetConfig || {};

        const getCfg = (col, defTemp) => config[col] || { autoCalc: true, template: defTemp };

        const penjualan = getCfg('penjualan', 'standard_cargo');
        const total_biaya = getCfg('total_biaya', 'vendor_ops');
        const profit = getCfg('profit', 'penjualan_minus_cost');
        const asuransi = getCfg('asuransi', 'nilai_barang_02');
        const asuransi_jasindo = getCfg('asuransi_jasindo', 'nilai_barang_01');
        const manualRows = config.manualRows || '';

        dropdown.innerHTML = `
            <style>
                .glass-dropdown-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 9999;
                    background: transparent;
                }
                .glass-dropdown-container {
                    position: fixed;
                    background: #ffffff;
                    border: 1px solid var(--red);
                    border-radius: 10px;
                    width: ${dropdownWidth}px;
                    padding: 18px 20px 16px;
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.14), 0 2px 8px rgba(0,0,0,0.06);
                    color: var(--text-primary);
                    font-family: 'Inter', system-ui, -apple-system, sans-serif;
                    z-index: 10000;
                    box-sizing: border-box;
                    animation: dropdownFadeIn 0.18s cubic-bezier(0.16, 1, 0.3, 1);
                    max-height: calc(100vh - 100px);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }
                /* Perfect border masking with a single elegant rotated square */
                .glass-dropdown-container::before {
                    content: '';
                    position: absolute;
                    top: -7px;
                    left: ${arrowLeft}px;
                    width: 12px;
                    height: 12px;
                    background: #ffffff;
                    border-left: 1px solid var(--red);
                    border-top: 1px solid var(--red);
                    border-right: 1px solid transparent;
                    border-bottom: 1px solid transparent;
                    transform: rotate(45deg);
                    margin-left: -6px;
                    z-index: 10002;
                }
                @keyframes dropdownFadeIn {
                    from { opacity: 0; transform: translateY(-8px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .glass-dropdown-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                    border-bottom: 1px solid #e1e4e8;
                    padding-bottom: 10px;
                }
                .glass-dropdown-header h2 {
                    margin: 0;
                    font-size: 0.95rem;
                    font-weight: 600;
                    color: var(--red);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .glass-dropdown-close {
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    font-size: 1rem;
                    cursor: pointer;
                    transition: color 0.15s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 4px;
                }
                .glass-dropdown-close:hover {
                    color: var(--red);
                }
                .glass-dropdown-columns {
                    display: flex;
                    gap: 24px;
                }
                .glass-dropdown-col-left {
                    flex: 1.15;
                    border-right: 1px solid #e1e4e8;
                    padding-right: 20px;
                    max-height: 400px;
                    overflow-y: auto;
                }
                .glass-dropdown-col-right {
                    flex: 0.85;
                    display: flex;
                    flex-direction: column;
                }
                .column-title {
                    font-size: 0.78rem;
                    font-weight: 600;
                    color: #57606a;
                    margin: 0 0 12px 0;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .glass-dropdown-col-left::-webkit-scrollbar {
                    width: 5px;
                }
                .glass-dropdown-col-left::-webkit-scrollbar-thumb {
                    background: #d0d7de;
                    border-radius: 3px;
                }
                .glass-dropdown-col-left::-webkit-scrollbar-thumb:hover {
                    background: #8c959f;
                }
                
                .config-item-row {
                    background: transparent;
                    border: none;
                    border-bottom: 1px solid #f0f0f0;
                    padding: 12px 4px;
                    margin-bottom: 0;
                }
                .config-item-row:last-child {
                    border-bottom: none;
                }
                .config-row-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .config-label-container {
                    display: flex;
                    flex-direction: column;
                    gap: 2px;
                }
                .config-item-title {
                    font-weight: 500;
                    font-size: 0.85rem;
                    color: var(--text-primary);
                }
                .config-item-field {
                    font-size: 0.7rem;
                    color: var(--text-muted);
                }
                .config-row-bottom {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    margin-top: 8px;
                }
                
                /* Custom Premium Radio Dots */
                .config-radio-group {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    margin-top: 8px;
                }
                .config-radio-option {
                    display: flex;
                    align-items: center;
                    cursor: pointer;
                    font-size: 0.78rem;
                    color: var(--text-primary);
                    position: relative;
                    padding: 4px 0;
                    user-select: none;
                }
                .config-radio-option input[type="radio"] {
                    position: absolute;
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                .radio-dot {
                    height: 16px;
                    width: 16px;
                    background-color: #ffffff;
                    border: 1.5px solid #d0d7de;
                    border-radius: 50%;
                    margin-right: 10px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    transition: border-color 0.2s, background-color 0.2s, box-shadow 0.2s;
                    flex-shrink: 0;
                }
                .config-radio-option:hover .radio-dot {
                    border-color: var(--red);
                    box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.1);
                }
                .config-radio-option input[type="radio"]:checked + .radio-dot {
                    border-color: var(--red);
                    background-color: #ffffff;
                }
                .config-radio-option input[type="radio"]:checked + .radio-dot::after {
                    content: "";
                    width: 8px;
                    height: 8px;
                    background-color: var(--red);
                    border-radius: 50%;
                    display: block;
                    animation: radioScaleIn 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }
                @keyframes radioScaleIn {
                    from { transform: scale(0); }
                    to { transform: scale(1); }
                }
                .radio-label {
                    font-weight: 400;
                    margin-right: 6px;
                }
                .info-trigger {
                    color: var(--text-muted);
                    font-size: 0.78rem;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    transition: color 0.15s;
                    position: relative;
                    margin-left: 6px;
                }
                .info-trigger:hover {
                    color: var(--red);
                }
                
                /* Premium CSS Tooltip */
                .info-trigger[data-tooltip]::before {
                    content: "Formula Template:\\A" attr(data-tooltip);
                    position: absolute;
                    bottom: 135%;
                    left: 50%;
                    transform: translateX(-50%) scale(0.95);
                    background: #1e293b;
                    color: #ffffff;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 0.7rem;
                    font-family: 'Inter', system-ui, sans-serif;
                    white-space: pre-wrap;
                    width: max-content;
                    max-width: 260px;
                    min-width: 160px;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.2s, transform 0.2s;
                    z-index: 10003;
                    font-style: normal;
                    font-weight: 500;
                    line-height: 1.4;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                .info-trigger[data-tooltip]::after {
                    content: '';
                    position: absolute;
                    bottom: 120%;
                    left: 50%;
                    transform: translateX(-50%);
                    border-width: 6px;
                    border-style: solid;
                    border-color: #1e293b transparent transparent transparent;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.2s;
                    z-index: 10003;
                }
                .info-trigger:hover[data-tooltip]::before {
                    opacity: 1;
                    transform: translateX(-50%) scale(1);
                }
                .info-trigger:hover[data-tooltip]::after {
                    opacity: 1;
                }

                .config-select {
                    background: #ffffff;
                    border: 1px solid #d0d7de;
                    color: var(--text-primary);
                    padding: 5px 8px;
                    border-radius: 4px;
                    font-size: 0.78rem;
                    outline: none;
                    cursor: pointer;
                    width: 100%;
                    transition: border-color 0.15s, box-shadow 0.15s;
                }
                .config-select:focus {
                    border-color: var(--red);
                    box-shadow: 0 0 0 2px rgba(204, 0, 0, 0.1);
                }
                
                .glass-dropdown-footer {
                    display: flex;
                    justify-content: flex-end;
                    gap: 8px;
                    margin-top: 16px;
                    border-top: 1px solid #e1e4e8;
                    padding-top: 12px;
                }
                .btn-glass-cancel {
                    background: #ffffff;
                    border: 1px solid #d0d7de;
                    color: #57606a;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.78rem;
                    font-weight: 500;
                    transition: background-color 0.15s, border-color 0.15s;
                }
                .btn-glass-cancel:hover {
                    background-color: #f6f8fa;
                    border-color: #8c959f;
                }
                .btn-glass-save {
                    background: var(--red, #cf222e);
                    border: 1px solid var(--red, #cf222e);
                    color: #ffffff;
                    padding: 8px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.82rem;
                    font-weight: 600;
                    transition: all 0.2s;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    font-family: 'Inter', system-ui, sans-serif;
                }
                .btn-glass-save:hover {
                    background: #a91b22;
                    border-color: #a91b22;
                }

                /* ===== TAB BAR ===== */
                .autocalc-tab-bar {
                    display: flex;
                    gap: 0;
                    margin-bottom: 0;
                    border-bottom: 2px solid #e1e4e8;
                    overflow-x: auto;
                    scrollbar-width: none;
                }
                .autocalc-tab-bar::-webkit-scrollbar { display: none; }
                .autocalc-tab-btn {
                    background: none;
                    border: none;
                    border-bottom: 2px solid transparent;
                    margin-bottom: -2px;
                    padding: 8px 14px;
                    font-size: 0.75rem;
                    font-weight: 500;
                    color: #57606a;
                    cursor: pointer;
                    white-space: nowrap;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    transition: color 0.15s, border-color 0.15s;
                    font-family: 'Inter', system-ui, sans-serif;
                }
                .autocalc-tab-btn:hover {
                    color: var(--red);
                    background: rgba(204, 0, 0, 0.04);
                }
                .autocalc-tab-btn.active {
                    color: var(--red);
                    border-bottom-color: var(--red);
                    font-weight: 600;
                }
                .autocalc-tab-btn i { font-size: 0.7rem; }

                /* ===== TAB CONTENT ===== */
                .autocalc-body {
                    flex: 1;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    min-height: 0;
                }
                .autocalc-tab-content {
                    display: none;
                    padding: 14px 2px 4px;
                    max-height: 380px;
                    overflow-y: auto;
                    scrollbar-width: thin;
                    scrollbar-color: #d0d7de transparent;
                }
                .autocalc-tab-content::-webkit-scrollbar { width: 4px; }
                .autocalc-tab-content::-webkit-scrollbar-thumb { background: #d0d7de; border-radius: 4px; }
                .autocalc-tab-content.active { display: block; }

                /* ===== SECTION TITLE ===== */
                .config-section-title {
                    font-size: 0.7rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.6px;
                    color: #57606a;
                    margin: 0 0 8px 0;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                .config-section-title i { color: var(--red); font-size: 0.65rem; }

                /* ===== AUTO-CALC TOGGLE SWITCH ===== */
                .autocalc-toggle-bar {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 8px 12px;
                    margin-bottom: 12px;
                    background: #f6f8fa;
                    border: 1.5px solid #e1e4e8;
                    border-radius: 8px;
                    transition: border-color 0.2s, background 0.2s;
                }
                .autocalc-toggle-bar.active {
                    border-color: rgba(204, 0, 0, 0.4);
                    background: rgba(204, 0, 0, 0.05);
                }
                .autocalc-toggle-bar.inactive {
                    border-color: #ef4444;
                    background: #fef2f2;
                }
                .autocalc-toggle-label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.78rem;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                .autocalc-toggle-label i {
                    font-size: 0.72rem;
                }
                .autocalc-toggle-bar.active .autocalc-toggle-label i { color: var(--red); }
                .autocalc-toggle-bar.inactive .autocalc-toggle-label i { color: #ef4444; }
                .autocalc-toggle-status {
                    font-size: 0.68rem;
                    font-weight: 600;
                    padding: 2px 8px;
                    border-radius: 100px;
                    letter-spacing: 0.3px;
                }
                .autocalc-toggle-bar.active .autocalc-toggle-status {
                    color: var(--red);
                    background: rgba(204, 0, 0, 0.1);
                }
                .autocalc-toggle-bar.inactive .autocalc-toggle-status {
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.1);
                }
                /* Toggle Switch */
                .toggle-switch {
                    position: relative;
                    width: 36px;
                    height: 20px;
                    flex-shrink: 0;
                }
                .toggle-switch input { opacity: 0; width: 0; height: 0; }
                .toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background-color: #d0d7de;
                    border-radius: 20px;
                    transition: background-color 0.25s;
                }
                .toggle-slider::before {
                    content: '';
                    position: absolute;
                    height: 16px; width: 16px;
                    left: 2px; bottom: 2px;
                    background-color: white;
                    border-radius: 50%;
                    transition: transform 0.25s;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
                }
                .toggle-switch input:checked + .toggle-slider {
                    background-color: var(--red);
                }
                .toggle-switch input:checked + .toggle-slider::before {
                    transform: translateX(16px);
                }
                .formula-config-area-disabled {
                    opacity: 0.35;
                    pointer-events: none;
                    filter: grayscale(0.5);
                    transition: opacity 0.25s, filter 0.25s;
                }

                /* ===== FORMULA TYPE SELECTOR (Preset / Kustom) ===== */
                .formula-type-selector {
                    display: flex;
                    gap: 0;
                    border: 1.5px solid #d0d7de;
                    border-radius: 6px;
                    overflow: hidden;
                    margin-bottom: 12px;
                }
                .formula-type-btn {
                    flex: 1;
                    padding: 6px 10px;
                    background: #f6f8fa;
                    border: none;
                    border-right: 1px solid #d0d7de;
                    font-size: 0.72rem;
                    font-weight: 500;
                    color: #57606a;
                    cursor: pointer;
                    transition: background 0.15s, color 0.15s;
                    font-family: 'Inter', system-ui, sans-serif;
                    white-space: nowrap;
                }
                .formula-type-btn:last-child { border-right: none; }
                .formula-type-btn:hover { background: #eaeef2; color: var(--red); }
                .formula-type-btn.active {
                    background: var(--red);
                    color: #ffffff;
                    font-weight: 600;
                }

                /* ===== PRESET CARDS ===== */
                .presets-container {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    margin-bottom: 4px;
                }
                .preset-option {
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                    padding: 10px 12px;
                    border: 1.5px solid #e1e4e8;
                    border-radius: 7px;
                    cursor: pointer;
                    transition: border-color 0.15s, background 0.15s;
                    user-select: none;
                    font-family: 'Inter', system-ui, sans-serif;
                }
                .preset-option:hover {
                    border-color: var(--red);
                    background: rgba(204, 0, 0, 0.03);
                }
                .preset-option.selected {
                    border-color: var(--red);
                    background: rgba(204, 0, 0, 0.05);
                }
                .preset-option input[type="radio"] {
                    accent-color: var(--red);
                    width: 14px;
                    height: 14px;
                    margin-top: 2px;
                    flex-shrink: 0;
                    cursor: pointer;
                }
                .preset-info {
                    display: flex;
                    flex-direction: column;
                    gap: 3px;
                    min-width: 0;
                }
                .preset-name {
                    font-size: 0.78rem;
                    font-weight: 600;
                    color: var(--text-primary);
                    line-height: 1.3;
                }
                .preset-option.selected .preset-name { color: var(--red); }
                .preset-desc {
                    font-size: 0.69rem;
                    color: #57606a;
                    line-height: 1.4;
                }
                .preset-desc code {
                    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                    font-size: 0.66rem;
                    background: rgba(0,0,0,0.05);
                    padding: 1px 4px;
                    border-radius: 3px;
                    color: #d63910;
                }

                /* ===== CUSTOM FORMULA PANEL ===== */
                .custom-formula-container {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    margin-bottom: 4px;
                }
                .variables-badge-title {
                    font-size: 0.68rem;
                    font-weight: 600;
                    color: #57606a;
                    text-transform: uppercase;
                    letter-spacing: 0.4px;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                .variables-badge-title i { color: var(--red); }
                .custom-formula-textarea {
                    width: 100%;
                    min-height: 58px;
                    max-height: 90px;
                    padding: 8px 10px;
                    border: 1.5px solid #d0d7de;
                    border-radius: 6px;
                    font-size: 0.75rem;
                    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                    color: var(--text-primary);
                    background: #f6f8fa;
                    resize: vertical;
                    outline: none;
                    transition: border-color 0.15s, box-shadow 0.15s;
                    box-sizing: border-box;
                    line-height: 1.5;
                }
                .custom-formula-textarea:focus {
                    border-color: var(--red);
                    background: #fff;
                    box-shadow: 0 0 0 2.5px rgba(204, 0, 0, 0.1);
                }
                .badge-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 5px;
                }
                .var-badge {
                    display: inline-flex;
                    align-items: center;
                    padding: 3px 9px;
                    background: rgba(204, 0, 0, 0.08);
                    color: var(--red, #cf222e);
                    border: 1px solid rgba(204, 0, 0, 0.2);
                    border-radius: 100px;
                    font-size: 0.68rem;
                    font-weight: 600;
                    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                    cursor: pointer;
                    transition: background 0.15s, color 0.15s, transform 0.12s;
                    user-select: none;
                }
                .var-badge:hover {
                    background: var(--red, #cf222e);
                    color: #fff;
                    transform: translateY(-1px);
                }
                .var-badge:active { transform: translateY(0); }

                /* ===== EXCLUSIONS INPUT ===== */
                .exclusions-container { margin-top: 4px; }
                .exclusions-input-wrapper {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }
                .exclusions-input {
                    width: 100%;
                    padding: 7px 10px;
                    border: 1.5px solid #d0d7de;
                    border-radius: 6px;
                    font-size: 0.75rem;
                    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                    color: var(--text-primary);
                    background: #ffffff;
                    outline: none;
                    transition: border-color 0.15s, box-shadow 0.15s;
                    box-sizing: border-box;
                }
                .exclusions-input:focus {
                    border-color: var(--red);
                    box-shadow: 0 0 0 2.5px rgba(204, 0, 0, 0.1);
                }
                .exclusions-guide {
                    font-size: 0.68rem;
                    color: #57606a;
                    line-height: 1.5;
                    padding: 6px 8px;
                    background: #f6f8fa;
                    border-radius: 5px;
                    border-left: 2px solid var(--red);
                }
                .exclusions-guide code {
                    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                    font-size: 0.65rem;
                    background: rgba(0,0,0,0.06);
                    padding: 1px 4px;
                    border-radius: 3px;
                    color: #d63910;
                }

                /* ===== FORMULA CONFIG AREA ANIMATION ===== */
                [class^="formula-config-area-"] {
                    border-top: 1px solid #f0f0f0;
                    padding-top: 12px;
                    margin-top: 4px;
                }
            </style>

            <div class="glass-dropdown-header">
                <h2><i class="fas fa-calculator"></i> Konfigurasi Perhitungan Otomatis</h2>
                <button class="glass-dropdown-close" id="btnCloseAutoCalc"><i class="fas fa-times"></i></button>
            </div>

            <!-- Segmented horizontal tabs representing columns -->
            <div class="autocalc-tab-bar">
                <button class="autocalc-tab-btn active" data-tab="tab-penjualan">
                    <i class="fas fa-cash-register"></i> Penjualan
                </button>
                <button class="autocalc-tab-btn" data-tab="tab-total_biaya">
                    <i class="fas fa-file-invoice-dollar"></i> Total Biaya
                </button>
                <button class="autocalc-tab-btn" data-tab="tab-asuransi">
                    <i class="fas fa-shield-alt"></i> Asuransi
                </button>
                <button class="autocalc-tab-btn" data-tab="tab-asuransi_jasindo">
                    <i class="fas fa-umbrella"></i> Jasindo
                </button>
                <button class="autocalc-tab-btn" data-tab="tab-profit">
                    <i class="fas fa-coins"></i> Profit
                </button>
            </div>

            <div class="autocalc-body">
                <!-- TAB 1: PENJUALAN -->
                <div class="autocalc-tab-content active" id="tab-penjualan">
                    <div class="autocalc-toggle-bar ${penjualan.autoCalc !== false ? 'active' : 'inactive'}">
                        <span class="autocalc-toggle-label"><i class="fas fa-bolt"></i> Rumus Otomatis</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="autocalc-toggle-status">${penjualan.autoCalc !== false ? 'AKTIF' : 'NONAKTIF'}</span>
                            <label class="toggle-switch">
                                <input type="checkbox" class="autocalc-toggle" data-field="penjualan" ${penjualan.autoCalc !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="formula-config-area-penjualan ${penjualan.autoCalc === false ? 'formula-config-area-disabled' : ''}">
                        <h4 class="config-section-title"><i class="fas fa-code"></i> Sumber Rumus</h4>
                        <div class="formula-type-selector">
                            <button class="formula-type-btn ${(!penjualan.formula || penjualan.template === 'custom_preset') ? 'active' : ''}" data-type="preset" data-field="penjualan">
                                Template Bawaan (Preset)
                            </button>
                            <button class="formula-type-btn ${(penjualan.formula && penjualan.template !== 'custom_preset') ? 'active' : ''}" data-type="custom" data-field="penjualan">
                                Formula Kustom (Kustom Rumus)
                            </button>
                        </div>

                        <!-- Presets Panel -->
                        <div class="presets-panel-penjualan" style="display: ${(!penjualan.formula || penjualan.template === 'custom_preset') ? 'block' : 'none'};">
                            <div class="presets-container">
                                <label class="preset-option ${penjualan.template === 'standard_cargo' ? 'selected' : ''}">
                                    <input type="radio" name="preset_penjualan" value="standard_cargo" ${penjualan.template === 'standard_cargo' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Standard Cargo (MAX Berat)</span>
                                        <span class="preset-desc">Rumus: <code>(Harga * MAX(Aktual, Vol)) + Surcharge + Packing + Handling</code></span>
                                    </div>
                                </label>
                                <label class="preset-option ${penjualan.template === 'double_charge' ? 'selected' : ''}">
                                    <input type="radio" name="preset_penjualan" value="double_charge" ${penjualan.template === 'double_charge' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Double Charge (Aktual + Volume)</span>
                                        <span class="preset-desc">Rumus: <code>(Harga * Aktual) + (Harga * Vol) + Surcharge + Packing + Handling</code></span>
                                    </div>
                                </label>
                                <label class="preset-option ${penjualan.template === 'actual_only' ? 'selected' : ''}">
                                    <input type="radio" name="preset_penjualan" value="actual_only" ${penjualan.template === 'actual_only' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Hanya Berat Aktual</span>
                                        <span class="preset-desc">Rumus: <code>(Harga * Aktual) + Surcharge + Packing + Handling</code></span>
                                    </div>
                                </label>
                                <label class="preset-option ${penjualan.template === 'volume_only' ? 'selected' : ''}">
                                    <input type="radio" name="preset_penjualan" value="volume_only" ${penjualan.template === 'volume_only' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Hanya Berat Volume</span>
                                        <span class="preset-desc">Rumus: <code>(Harga * Vol) + Surcharge + Packing + Handling</code></span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Custom Formula Panel -->
                        <div class="custom-formula-panel-penjualan" style="display: ${(penjualan.formula && penjualan.template !== 'custom_preset') ? 'block' : 'none'};">
                            <div class="custom-formula-container">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="variables-badge-title" style="margin-bottom:0;"><i class="fas fa-edit"></i> Edit Rumus Kustom</span>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        
                                        <button class="btn-save-custom-formula" data-field="penjualan" style="padding:2px 8px; font-size:0.7rem; font-weight:600; border-radius:4px; background:#28a745; color:white; border:none; cursor:pointer;"><i class="fas fa-save"></i> Simpan ke Preset Bawaan</button>
                                    </div>
                                </div>
                                <textarea class="custom-formula-textarea" id="formula_penjualan" placeholder="Masukkan rumus baru disini, contoh: = (harga * aktual) + surcharge">${penjualan.formula || ''}</textarea>
                                
                                <span class="variables-badge-title"><i class="fas fa-tags"></i> Klik Badge untuk Memasukkan Variabel</span>
                                <div class="badge-container">
                                    <span class="var-badge" data-field="penjualan" data-val="harga">harga</span>
                                    <span class="var-badge" data-field="penjualan" data-val="aktual">aktual</span>
                                    <span class="var-badge" data-field="penjualan" data-val="vol">vol</span>
                                    <span class="var-badge" data-field="penjualan" data-val="surcharge">surcharge</span>
                                    <span class="var-badge" data-field="penjualan" data-val="packing">packing</span>
                                    <span class="var-badge" data-field="penjualan" data-val="handling">handling</span>
                                    <span class="var-badge" data-field="penjualan" data-val="nilai_barang">nilai_barang</span>
                                    <span class="var-badge" data-field="penjualan" data-val="kubik">kubik</span>
                                    <span class="var-badge" data-field="penjualan" data-val="unit">unit</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Visual row exclusions per-field -->
                    <h4 class="config-section-title"><i class="fas fa-ban"></i> Pengecualian Baris (Row Exceptions)</h4>
                    <div class="exclusions-container">
                        <div class="exclusions-input-wrapper">
                            <input type="text" class="exclusions-input" id="exclude_penjualan" value="${penjualan.excludeRows || ''}" placeholder="Contoh: 1-5, 8, 12">
                            <span class="exclusions-guide">
                                <strong>Panduan Pengisian:</strong> Masukkan nomor baris spreadsheet (kolom # paling kiri) yang dikecualikan dari otomatisasi kolom <strong>Penjualan</strong>.<br>
                                Gunakan tanda koma untuk baris terpisah (e.g. <code>3, 5</code>) atau tanda hubung untuk rentang baris (e.g. <code>10-15</code>).
                            </span>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: TOTAL BIAYA -->
                <div class="autocalc-tab-content" id="tab-total_biaya">
                    <div class="autocalc-toggle-bar ${total_biaya.autoCalc !== false ? 'active' : 'inactive'}">
                        <span class="autocalc-toggle-label"><i class="fas fa-bolt"></i> Rumus Otomatis</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="autocalc-toggle-status">${total_biaya.autoCalc !== false ? 'AKTIF' : 'NONAKTIF'}</span>
                            <label class="toggle-switch">
                                <input type="checkbox" class="autocalc-toggle" data-field="total_biaya" ${total_biaya.autoCalc !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="formula-config-area-total_biaya ${total_biaya.autoCalc === false ? 'formula-config-area-disabled' : ''}">
                        <h4 class="config-section-title"><i class="fas fa-code"></i> Sumber Rumus</h4>
                        <div class="formula-type-selector">
                            <button class="formula-type-btn ${(!total_biaya.formula || total_biaya.template === 'custom_preset') ? 'active' : ''}" data-type="preset" data-field="total_biaya">
                                Template Bawaan (Preset)
                            </button>
                            <button class="formula-type-btn ${(total_biaya.formula && total_biaya.template !== 'custom_preset') ? 'active' : ''}" data-type="custom" data-field="total_biaya">
                                Formula Kustom (Kustom Rumus)
                            </button>
                        </div>

                        <!-- Presets Panel -->
                        <div class="presets-panel-total_biaya" style="display: ${(!total_biaya.formula || total_biaya.template === 'custom_preset') ? 'block' : 'none'};">
                            <div class="presets-container">
                                <label class="preset-option selected">
                                    <input type="radio" name="preset_total_biaya" value="vendor_ops" checked>
                                    <div class="preset-info">
                                        <span class="preset-name">Vendor & Operational Cost (Standard)</span>
                                        <span class="preset-desc">Rumus: <code>Vendor I + Vendor II + Vendor III + Vendor IV + Ops</code></span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Custom Formula Panel -->
                        <div class="custom-formula-panel-total_biaya" style="display: ${(total_biaya.formula && total_biaya.template !== 'custom_preset') ? 'block' : 'none'};">
                            <div class="custom-formula-container">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="variables-badge-title" style="margin-bottom:0;"><i class="fas fa-edit"></i> Edit Rumus Kustom</span>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        
                                        <button class="btn-save-custom-formula" data-field="total_biaya" style="padding:2px 8px; font-size:0.7rem; font-weight:600; border-radius:4px; background:#28a745; color:white; border:none; cursor:pointer;"><i class="fas fa-save"></i> Simpan ke Preset Bawaan</button>
                                    </div>
                                </div>
                                <textarea class="custom-formula-textarea" id="formula_total_biaya" placeholder="Contoh: = vendor_i + vendor_ii + vendor_iii + ops">${total_biaya.formula || ''}</textarea>
                                
                                <span class="variables-badge-title"><i class="fas fa-tags"></i> Klik Badge untuk Memasukkan Variabel</span>
                                <div class="badge-container">
                                    <span class="var-badge" data-field="total_biaya" data-val="vendor_i">vendor_i</span>
                                    <span class="var-badge" data-field="total_biaya" data-val="vendor_ii">vendor_ii</span>
                                    <span class="var-badge" data-field="total_biaya" data-val="vendor_iii">vendor_iii</span>
                                    <span class="var-badge" data-field="total_biaya" data-val="vendor_iv">vendor_iv</span>
                                    <span class="var-badge" data-field="total_biaya" data-val="ops">ops</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Visual row exclusions per-field -->
                    <h4 class="config-section-title"><i class="fas fa-ban"></i> Pengecualian Baris (Row Exceptions)</h4>
                    <div class="exclusions-container">
                        <div class="exclusions-input-wrapper">
                            <input type="text" class="exclusions-input" id="exclude_total_biaya" value="${total_biaya.excludeRows || ''}" placeholder="Contoh: 1-5, 8, 12">
                            <span class="exclusions-guide">
                                <strong>Panduan Pengisian:</strong> Masukkan nomor baris spreadsheet yang dikecualikan dari otomatisasi kolom <strong>Total Biaya</strong>.
                            </span>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: ASURANSI -->
                <div class="autocalc-tab-content" id="tab-asuransi">
                    <div class="autocalc-toggle-bar ${asuransi.autoCalc !== false ? 'active' : 'inactive'}">
                        <span class="autocalc-toggle-label"><i class="fas fa-bolt"></i> Rumus Otomatis</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="autocalc-toggle-status">${asuransi.autoCalc !== false ? 'AKTIF' : 'NONAKTIF'}</span>
                            <label class="toggle-switch">
                                <input type="checkbox" class="autocalc-toggle" data-field="asuransi" ${asuransi.autoCalc !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="formula-config-area-asuransi ${asuransi.autoCalc === false ? 'formula-config-area-disabled' : ''}">
                        <h4 class="config-section-title"><i class="fas fa-code"></i> Sumber Rumus</h4>
                        <div class="formula-type-selector">
                            <button class="formula-type-btn ${(!asuransi.formula || asuransi.template === 'custom_preset') ? 'active' : ''}" data-type="preset" data-field="asuransi">
                                Template Bawaan (Preset)
                            </button>
                            <button class="formula-type-btn ${(asuransi.formula && asuransi.template !== 'custom_preset') ? 'active' : ''}" data-type="custom" data-field="asuransi">
                                Formula Kustom (Kustom Rumus)
                            </button>
                        </div>

                        <!-- Presets Panel -->
                        <div class="presets-panel-asuransi" style="display: ${(!asuransi.formula || asuransi.template === 'custom_preset') ? 'block' : 'none'};">
                            <div class="presets-container">
                                <label class="preset-option ${asuransi.template === 'nilai_barang_02' ? 'selected' : ''}">
                                    <input type="radio" name="preset_asuransi" value="nilai_barang_02" ${asuransi.template === 'nilai_barang_02' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Standard (0.2% Nilai Barang)</span>
                                        <span class="preset-desc">Rumus: <code>Nilai Barang * 0.2%</code></span>
                                    </div>
                                </label>
                                <label class="preset-option ${asuransi.template === 'nilai_barang_none' ? 'selected' : ''}">
                                    <input type="radio" name="preset_asuransi" value="nilai_barang_none" ${asuransi.template === 'nilai_barang_none' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Tanpa Asuransi (0)</span>
                                        <span class="preset-desc">Rumus: <code>0</code></span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Custom Formula Panel -->
                        <div class="custom-formula-panel-asuransi" style="display: ${(asuransi.formula && asuransi.template !== 'custom_preset') ? 'block' : 'none'};">
                            <div class="custom-formula-container">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="variables-badge-title" style="margin-bottom:0;"><i class="fas fa-edit"></i> Edit Rumus Kustom</span>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        
                                        <button class="btn-save-custom-formula" data-field="asuransi" style="padding:2px 8px; font-size:0.7rem; font-weight:600; border-radius:4px; background:#28a745; color:white; border:none; cursor:pointer;"><i class="fas fa-save"></i> Simpan ke Preset Bawaan</button>
                                    </div>
                                </div>
                                <textarea class="custom-formula-textarea" id="formula_asuransi" placeholder="Contoh: = nilai_barang * 0.002">${asuransi.formula || ''}</textarea>
                                
                                <span class="variables-badge-title"><i class="fas fa-tags"></i> Klik Badge untuk Memasukkan Variabel</span>
                                <div class="badge-container">
                                    <span class="var-badge" data-field="asuransi" data-val="nilai_barang">nilai_barang</span>
                                    <span class="var-badge" data-field="asuransi" data-val="aktual">aktual</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Visual row exclusions per-field -->
                    <h4 class="config-section-title"><i class="fas fa-ban"></i> Pengecualian Baris (Row Exceptions)</h4>
                    <div class="exclusions-container">
                        <div class="exclusions-input-wrapper">
                            <input type="text" class="exclusions-input" id="exclude_asuransi" value="${asuransi.excludeRows || ''}" placeholder="Contoh: 1-5, 8, 12">
                            <span class="exclusions-guide">
                                <strong>Panduan Pengisian:</strong> Masukkan nomor baris spreadsheet yang dikecualikan dari otomatisasi kolom <strong>Asuransi</strong>.
                            </span>
                        </div>
                    </div>
                </div>

                <!-- TAB 4: ASURANSI JASINDO -->
                <div class="autocalc-tab-content" id="tab-asuransi_jasindo">
                    <div class="autocalc-toggle-bar ${asuransi_jasindo.autoCalc !== false ? 'active' : 'inactive'}">
                        <span class="autocalc-toggle-label"><i class="fas fa-bolt"></i> Rumus Otomatis</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="autocalc-toggle-status">${asuransi_jasindo.autoCalc !== false ? 'AKTIF' : 'NONAKTIF'}</span>
                            <label class="toggle-switch">
                                <input type="checkbox" class="autocalc-toggle" data-field="asuransi_jasindo" ${asuransi_jasindo.autoCalc !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="formula-config-area-asuransi_jasindo ${asuransi_jasindo.autoCalc === false ? 'formula-config-area-disabled' : ''}">
                        <h4 class="config-section-title"><i class="fas fa-code"></i> Sumber Rumus</h4>
                        <div class="formula-type-selector">
                            <button class="formula-type-btn ${(!asuransi_jasindo.formula || asuransi_jasindo.template === 'custom_preset') ? 'active' : ''}" data-type="preset" data-field="asuransi_jasindo">
                                Template Bawaan (Preset)
                            </button>
                            <button class="formula-type-btn ${(asuransi_jasindo.formula && asuransi_jasindo.template !== 'custom_preset') ? 'active' : ''}" data-type="custom" data-field="asuransi_jasindo">
                                Formula Kustom (Kustom Rumus)
                            </button>
                        </div>

                        <!-- Presets Panel -->
                        <div class="presets-panel-asuransi_jasindo" style="display: ${(!asuransi_jasindo.formula || asuransi_jasindo.template === 'custom_preset') ? 'block' : 'none'};">
                            <div class="presets-container">
                                <label class="preset-option ${asuransi_jasindo.template === 'nilai_barang_01' ? 'selected' : ''}">
                                    <input type="radio" name="preset_asuransi_jasindo" value="nilai_barang_01" ${asuransi_jasindo.template === 'nilai_barang_01' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Standard (0.1% Nilai Barang)</span>
                                        <span class="preset-desc">Rumus: <code>Nilai Barang * 0.1%</code></span>
                                    </div>
                                </label>
                                <label class="preset-option ${asuransi_jasindo.template === 'nilai_barang_none' ? 'selected' : ''}">
                                    <input type="radio" name="preset_asuransi_jasindo" value="nilai_barang_none" ${asuransi_jasindo.template === 'nilai_barang_none' ? 'checked' : ''}>
                                    <div class="preset-info">
                                        <span class="preset-name">Tanpa Jasindo (0)</span>
                                        <span class="preset-desc">Rumus: <code>0</code></span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Custom Formula Panel -->
                        <div class="custom-formula-panel-asuransi_jasindo" style="display: ${(asuransi_jasindo.formula && asuransi_jasindo.template !== 'custom_preset') ? 'block' : 'none'};">
                            <div class="custom-formula-container">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="variables-badge-title" style="margin-bottom:0;"><i class="fas fa-edit"></i> Edit Rumus Kustom</span>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        
                                        <button class="btn-save-custom-formula" data-field="asuransi_jasindo" style="padding:2px 8px; font-size:0.7rem; font-weight:600; border-radius:4px; background:#28a745; color:white; border:none; cursor:pointer;"><i class="fas fa-save"></i> Simpan ke Preset Bawaan</button>
                                    </div>
                                </div>
                                <textarea class="custom-formula-textarea" id="formula_asuransi_jasindo" placeholder="Contoh: = nilai_barang * 0.001">${asuransi_jasindo.formula || ''}</textarea>
                                
                                <span class="variables-badge-title"><i class="fas fa-tags"></i> Klik Badge untuk Memasukkan Variabel</span>
                                <div class="badge-container">
                                    <span class="var-badge" data-field="asuransi_jasindo" data-val="nilai_barang">nilai_barang</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Visual row exclusions per-field -->
                    <h4 class="config-section-title"><i class="fas fa-ban"></i> Pengecualian Baris (Row Exceptions)</h4>
                    <div class="exclusions-container">
                        <div class="exclusions-input-wrapper">
                            <input type="text" class="exclusions-input" id="exclude_asuransi_jasindo" value="${asuransi_jasindo.excludeRows || ''}" placeholder="Contoh: 1-5, 8, 12">
                            <span class="exclusions-guide">
                                <strong>Panduan Pengisian:</strong> Masukkan nomor baris spreadsheet yang dikecualikan dari otomatisasi kolom <strong>Asuransi Jasindo</strong>.
                            </span>
                        </div>
                    </div>
                </div>

                <!-- TAB 5: PROFIT & MARGIN -->
                <div class="autocalc-tab-content" id="tab-profit">
                    <div class="autocalc-toggle-bar ${profit.autoCalc !== false ? 'active' : 'inactive'}">
                        <span class="autocalc-toggle-label"><i class="fas fa-bolt"></i> Rumus Otomatis</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="autocalc-toggle-status">${profit.autoCalc !== false ? 'AKTIF' : 'NONAKTIF'}</span>
                            <label class="toggle-switch">
                                <input type="checkbox" class="autocalc-toggle" data-field="profit" ${profit.autoCalc !== false ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="formula-config-area-profit ${profit.autoCalc === false ? 'formula-config-area-disabled' : ''}">
                        <h4 class="config-section-title"><i class="fas fa-code"></i> Sumber Rumus</h4>
                        <div class="formula-type-selector">
                            <button class="formula-type-btn ${(!profit.formula || profit.template === 'custom_preset') ? 'active' : ''}" data-type="preset" data-field="profit">
                                Template Bawaan (Preset)
                            </button>
                            <button class="formula-type-btn ${(profit.formula && profit.template !== 'custom_preset') ? 'active' : ''}" data-type="custom" data-field="profit">
                                Formula Kustom (Kustom Rumus)
                            </button>
                        </div>

                        <!-- Presets Panel -->
                        <div class="presets-panel-profit" style="display: ${(!profit.formula || profit.template === 'custom_preset') ? 'block' : 'none'};">
                            <div class="presets-container">
                                <label class="preset-option selected">
                                    <input type="radio" name="preset_profit" value="penjualan_minus_cost" checked>
                                    <div class="preset-info">
                                        <span class="preset-name">Penjualan - Cost - Jasindo (Standard)</span>
                                        <span class="preset-desc">Rumus: <code>Penjualan - Total Biaya - Asuransi Jasindo</code></span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Custom Formula Panel -->
                        <div class="custom-formula-panel-profit" style="display: ${(profit.formula && profit.template !== 'custom_preset') ? 'block' : 'none'};">
                            <div class="custom-formula-container">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="variables-badge-title" style="margin-bottom:0;"><i class="fas fa-edit"></i> Edit Rumus Kustom</span>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        
                                        <button class="btn-save-custom-formula" data-field="profit" style="padding:2px 8px; font-size:0.7rem; font-weight:600; border-radius:4px; background:#28a745; color:white; border:none; cursor:pointer;"><i class="fas fa-save"></i> Simpan ke Preset Bawaan</button>
                                    </div>
                                </div>
                                <textarea class="custom-formula-textarea" id="formula_profit" placeholder="Contoh: = penjualan - total_biaya - asuransi_jasindo">${profit.formula || ''}</textarea>
                                
                                <span class="variables-badge-title"><i class="fas fa-tags"></i> Klik Badge untuk Memasukkan Variabel</span>
                                <div class="badge-container">
                                    <span class="var-badge" data-field="profit" data-val="penjualan">penjualan</span>
                                    <span class="var-badge" data-field="profit" data-val="total_biaya">total_biaya</span>
                                    <span class="var-badge" data-field="profit" data-val="asuransi_jasindo">asuransi_jasindo</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Visual row exclusions per-field -->
                    <h4 class="config-section-title"><i class="fas fa-ban"></i> Pengecualian Baris (Row Exceptions)</h4>
                    <div class="exclusions-container">
                        <div class="exclusions-input-wrapper">
                            <input type="text" class="exclusions-input" id="exclude_profit" value="${profit.excludeRows || ''}" placeholder="Contoh: 1-5, 8, 12">
                            <span class="exclusions-guide">
                                <strong>Panduan Pengisian:</strong> Masukkan nomor baris spreadsheet yang dikecualikan dari otomatisasi kolom <strong>Profit</strong> & <strong>Margin Percent</strong>.
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="glass-dropdown-footer">
                <button class="btn-glass-cancel" id="btnCancelAutoCalc">Batal</button>
                <button class="btn-glass-save" id="btnSaveAutoCalc">Simpan & Terapkan</button>
            </div>
        `;

        document.body.appendChild(dropdown);

        const closeDropdown = () => {
            document.querySelectorAll('#autoCalcConfigDropdown, #autoCalcDropdownOverlay, .glass-dropdown-container, .glass-dropdown-overlay').forEach(el => el.remove());
        };

        dropdown.querySelector('#btnCloseAutoCalc').addEventListener('click', closeDropdown);
        dropdown.querySelector('#btnCancelAutoCalc').addEventListener('click', closeDropdown);

        // 1. Interactive Tabs Switching Logic
        const tabs = dropdown.querySelectorAll('.autocalc-tab-btn');
        tabs.forEach(tabBtn => {
            tabBtn.addEventListener('click', () => {
                // Deactivate all tabs
                dropdown.querySelectorAll('.autocalc-tab-btn, .autocalc-tab-content').forEach(el => el.classList.remove('active'));

                // Activate clicked tab
                tabBtn.classList.add('active');
                const contentId = tabBtn.dataset.tab;
                dropdown.querySelector(`#${contentId}`).classList.add('active');
            });
        });


        // 2. Fields array used by multiple event sections below
        const fields = ['penjualan', 'total_biaya', 'asuransi', 'asuransi_jasindo', 'profit'];

        // 2b. Toggle switch event listeners (Aktif/Nonaktif per column)
        dropdown.querySelectorAll('.autocalc-toggle').forEach(toggle => {
            toggle.addEventListener('change', () => {
                const f = toggle.dataset.field;
                const bar = toggle.closest('.autocalc-toggle-bar');
                const configArea = dropdown.querySelector(`.formula-config-area-${f}`);
                const statusSpan = bar.querySelector('.autocalc-toggle-status');
                if (toggle.checked) {
                    bar.classList.remove('inactive');
                    bar.classList.add('active');
                    statusSpan.textContent = 'AKTIF';
                    if (configArea) configArea.classList.remove('formula-config-area-disabled');
                } else {
                    bar.classList.remove('active');
                    bar.classList.add('inactive');
                    statusSpan.textContent = 'NONAKTIF';
                    if (configArea) configArea.classList.add('formula-config-area-disabled');
                }
            });
        });

        // 3. Interactive Formula Type (Preset vs Custom) Toggling Logic
        dropdown.querySelectorAll('.formula-type-btn').forEach(btnEl => {
            btnEl.addEventListener('click', () => {
                const f = btnEl.dataset.field;
                const type = btnEl.dataset.type;

                // Deactivate brothers in selector
                dropdown.querySelectorAll(`.formula-type-btn[data-field="${f}"]`).forEach(el => el.classList.remove('active'));
                btnEl.classList.add('active');

                // Toggle visibility of panels
                const presetPanel = dropdown.querySelector(`.presets-panel-${f}`);
                const customPanel = dropdown.querySelector(`.custom-formula-panel-${f}`);

                if (type === 'preset') {
                    presetPanel.style.display = 'block';
                    customPanel.style.display = 'none';
                } else {
                    presetPanel.style.display = 'none';
                    customPanel.style.display = 'block';
                }
            });
        });

        // 4. Clickable Variable Badges Text Insertion Helper
        const insertTextAtCursor = (textarea, text) => {
            const startPos = textarea.selectionStart;
            const endPos = textarea.selectionEnd;
            const originalValue = textarea.value;
            textarea.value = originalValue.substring(0, startPos) + text + originalValue.substring(endPos);
            textarea.focus();
            textarea.selectionStart = textarea.selectionEnd = startPos + text.length;
        };

        dropdown.querySelectorAll('.var-badge').forEach(badge => {
            badge.addEventListener('click', () => {
                const f = badge.dataset.field;
                const val = badge.dataset.val;
                const textarea = dropdown.querySelector(`#formula_${f}`);
                if (textarea) {
                    insertTextAtCursor(textarea, ` ${val} `);
                }
            });
        });

        // 5. Preset UI styling selection
        fields.forEach(f => {
            const presetRadios = dropdown.querySelectorAll(`input[name="preset_${f}"]`);
            presetRadios.forEach(radio => {
                radio.addEventListener('change', () => {
                    dropdown.querySelectorAll(`input[name="preset_${f}"]`).forEach(r => {
                        r.closest('.preset-option').classList.remove('selected');
                    });
                    if (radio.checked) {
                        radio.closest('.preset-option').classList.add('selected');
                    }
                });
            });
        });

        // 5. Custom Formula Save/Load Logic
        const loadSavedFormulas = () => {
            const currentConfig = this.tableManager.sheetConfig || {};

            fields.forEach(f => {
                const container = dropdown.querySelector(`.presets-panel-${f} .presets-container`);
                if (!container) return;

                container.querySelectorAll('.custom-preset-option').forEach(el => el.remove());

                let saved = [];
                try {
                    const raw = localStorage.getItem(`custom_formulas_${f}`);
                    if (raw) saved = JSON.parse(raw);
                } catch (e) { }

                const cfg = currentConfig[f] || {};

                saved.forEach((item, index) => {
                    const isChecked = (cfg.template === 'custom_preset' && cfg.formula === item.formula) ? 'checked' : '';
                    const label = document.createElement('label');
                    label.className = 'preset-option custom-preset-option ' + (isChecked ? 'selected' : '');
                    label.innerHTML = `
                        <input type="radio" name="preset_${f}" value="${item.formula}" data-iscustom="true" ${isChecked}>
                        <div class="preset-info" style="flex:1;">
                            <span class="preset-name">${item.name} <span style="font-size:0.65rem; padding:1px 4px; background:#e0f2fe; color:#0369a1; border-radius:4px; margin-left:4px;">Kustom</span></span>
                            <span class="preset-desc">Rumus: <code>${item.formula}</code></span>
                        </div>
                        <button class="btn-delete-preset" data-field="${f}" data-idx="${index}" style="margin-left:8px; padding:2px 6px; font-size:0.7rem; border-radius:4px; background:#fee2e2; color:#ef4444; border:1px solid #fca5a5; cursor:pointer;" title="Hapus Preset"><i class="fas fa-trash"></i></button>
                    `;
                    container.appendChild(label);
                });
            });

            // Re-bind radio change events for new elements
            dropdown.querySelectorAll('.custom-preset-option input[type="radio"]').forEach(radio => {
                radio.addEventListener('change', () => {
                    const f = radio.name.replace('preset_', '');
                    dropdown.querySelectorAll(`input[name="preset_${f}"]`).forEach(r => {
                        r.closest('.preset-option').classList.remove('selected');
                    });
                    radio.closest('.preset-option').classList.add('selected');
                });
            });

            // Bind delete events
            dropdown.querySelectorAll('.btn-delete-preset').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const f = btn.dataset.field;
                    const idx = parseInt(btn.dataset.idx);

                    if (confirm('Yakin ingin menghapus preset kustom ini?')) {
                        let saved = [];
                        try { saved = JSON.parse(localStorage.getItem(`custom_formulas_${f}`) || '[]'); } catch (e) { }
                        saved.splice(idx, 1);
                        localStorage.setItem(`custom_formulas_${f}`, JSON.stringify(saved));
                        loadSavedFormulas();
                    }
                });
            });
        };

        loadSavedFormulas();

        dropdown.querySelectorAll('.btn-save-custom-formula').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const targetBtn = e.target.closest('button');
                const f = targetBtn.dataset.field;
                const textarea = dropdown.querySelector(`#formula_${f}`);
                if (!textarea) return;

                const formulaStr = textarea.value.trim();
                if (!formulaStr) {
                    alert('Rumus kustom masih kosong! Ketikkan rumus terlebih dahulu.');
                    return;
                }

                const name = prompt('Masukkan nama untuk preset rumus ini:');
                if (!name) return;

                let saved = [];
                try {
                    const raw = localStorage.getItem(`custom_formulas_${f}`);
                    if (raw) saved = JSON.parse(raw);
                } catch (e) { }

                const existingIdx = saved.findIndex(s => s.name.toLowerCase() === name.toLowerCase());
                if (existingIdx !== -1) {
                    if (confirm(`Preset dengan nama "${name}" sudah ada. Timpa rumus lama dengan yang baru?`)) {
                        saved[existingIdx].formula = formulaStr;
                    } else {
                        return;
                    }
                } else {
                    saved.push({ name, formula: formulaStr });
                }

                localStorage.setItem(`custom_formulas_${f}`, JSON.stringify(saved));
                loadSavedFormulas();
                alert(`Rumus "${name}" berhasil disimpan dan bisa dipilih kembali dari dropdown!`);
            });
        });

        // 6. Save configuration to sheet configurations and recalculate table rows
        dropdown.querySelector('#btnSaveAutoCalc').addEventListener('click', async () => {
            this.tableManager.updateStatusBar('Menyimpan konfigurasi perhitungan otomatis...');

            const getFieldConfig = (f, defTemplate) => {
                const toggleCheckbox = dropdown.querySelector(`.autocalc-toggle[data-field="${f}"]`);
                const isAutoCalc = toggleCheckbox ? toggleCheckbox.checked : false;

                let selectedTemplate = defTemplate;
                const presetRadio = dropdown.querySelector(`input[name="preset_${f}"]:checked`);

                let isCustomPreset = false;
                let customPresetFormula = '';

                if (presetRadio) {
                    if (presetRadio.dataset.iscustom === 'true') {
                        isCustomPreset = true;
                        customPresetFormula = presetRadio.value;
                        selectedTemplate = 'custom_preset';
                    } else {
                        selectedTemplate = presetRadio.value;
                    }
                }

                const isCustomFormulaActive = dropdown.querySelector(`.formula-type-btn[data-field="${f}"][data-type="custom"]`).classList.contains('active');
                const formulaTextVal = dropdown.querySelector(`#formula_${f}`).value.trim();

                let finalFormula = '';
                if (isAutoCalc) {
                    if (isCustomFormulaActive) {
                        finalFormula = formulaTextVal;
                    } else if (isCustomPreset) {
                        finalFormula = customPresetFormula;
                    }
                }

                const excludeRowsVal = dropdown.querySelector(`#exclude_${f}`).value.trim();

                return {
                    autoCalc: isAutoCalc,
                    template: selectedTemplate,
                    formula: finalFormula,
                    excludeRows: excludeRowsVal
                };
            };

            const penjualanCfg = getFieldConfig('penjualan', 'standard_cargo');
            const totalBiayaCfg = getFieldConfig('total_biaya', 'vendor_ops');
            const asuransiCfg = getFieldConfig('asuransi', 'nilai_barang_02');
            const jasindoCfg = getFieldConfig('asuransi_jasindo', 'nilai_barang_01');
            const profitCfg = getFieldConfig('profit', 'penjualan_minus_cost');

            const newConfig = {
                penjualan: penjualanCfg,
                total_biaya: totalBiayaCfg,
                asuransi: asuransiCfg,
                asuransi_jasindo: jasindoCfg,
                profit: profitCfg,
                idx_profit: {
                    autoCalc: profitCfg.autoCalc
                }
            };

            console.log('[AutoCalc] Saving config:', JSON.stringify(newConfig, null, 2));

            try {
                const oldConfig = JSON.parse(JSON.stringify(this.tableManager.sheetConfig || {}));

                // 1. Save config to database
                if (this.tableManager.sheetConfigRow) {
                    const id = this.tableManager.sheetConfigRow.id;
                    const updatedRow = await window.databaseManager.updateRow(id, { formulas: newConfig });
                    this.tableManager.sheetConfigRow = updatedRow || this.tableManager.sheetConfigRow;
                    if (this.tableManager.sheetConfigRow) {
                        this.tableManager.sheetConfigRow.formulas = newConfig;
                    }
                } else {
                    const rowData = {
                        nama: '__SHEET_CONFIG__',
                        formulas: newConfig,
                        sheet_id: window.activeSheetId || 1
                    };
                    const newRow = await window.databaseManager.insertRow(rowData);
                    this.tableManager.sheetConfigRow = newRow;
                }

                // 2. Apply config in memory BEFORE recalculation
                this.tableManager.sheetConfig = newConfig;

                // Check for real manual overrides (not just dummy ' ')
                let hasRealOverrides = false;
                this.tableManager.currentData.forEach(row => {
                    if (!row || !row.id || String(row.id).startsWith('preload_')) return;
                    if (row.formulas) {
                        let parsed = row.formulas;
                        if (typeof parsed === 'string') {
                            try { parsed = JSON.parse(parsed); } catch (e) { parsed = {}; }
                        }
                        Object.keys(newConfig).forEach(f => {
                            const wasAutoCalc = oldConfig[f]?.autoCalc || false;
                            const isNowAutoCalc = newConfig[f]?.autoCalc || false;
                            const isNewlyTurnedOn = isNowAutoCalc && !wasAutoCalc;
                            const isTemplateChanged = isNowAutoCalc && (newConfig[f]?.template !== oldConfig[f]?.template || newConfig[f]?.formula !== oldConfig[f]?.formula);

                            if ((isNewlyTurnedOn || isTemplateChanged) && parsed[f] !== undefined && parsed[f] !== ' ') {
                                hasRealOverrides = true;
                            }
                        });
                    }
                });

                let wipeAll = false;
                if (hasRealOverrides) {
                    wipeAll = await showConfirm({
                        title: 'Konfirmasi Penghapusan Override',
                        message: 'Ditemukan rumus/angka manual (override) pada baris yang Anda ubah ke Rumus Otomatis.\n\nApakah Anda ingin MENGHAPUS rumus manual tersebut dan menerapkan Rumus Otomatis ini secara menyeluruh?\n\n(Pilih OK untuk menerapkan rumus ke seluruh baris, atau Batal untuk mempertahankan angka manual Anda.)',
                        icon: 'warning',
                        confirmText: 'OK',
                        cancelText: 'Batal'
                    });
                }

                // Clear manual clear overrides (' ') for fields that are now autoCalc,
                // and optionally clear all real overrides if wipeAll is true
                this.tableManager.currentData.forEach(row => {
                    if (!row || !row.id || String(row.id).startsWith('preload_')) return;
                    if (row.formulas) {
                        let parsed = row.formulas;
                        if (typeof parsed === 'string') {
                            try { parsed = JSON.parse(parsed); } catch (e) { parsed = {}; }
                        }
                        let changed = false;
                        Object.keys(newConfig).forEach(f => {
                            const wasAutoCalc = oldConfig[f]?.autoCalc || false;
                            const isNowAutoCalc = newConfig[f]?.autoCalc || false;
                            const isNewlyTurnedOn = isNowAutoCalc && !wasAutoCalc;
                            const isTemplateChanged = isNowAutoCalc && (newConfig[f]?.template !== oldConfig[f]?.template || newConfig[f]?.formula !== oldConfig[f]?.formula);

                            if (isNowAutoCalc && parsed[f] !== undefined) {
                                if (parsed[f] === ' ' || (wipeAll && (isNewlyTurnedOn || isTemplateChanged))) {
                                    delete parsed[f];
                                    changed = true;
                                }
                            }
                        });

                        if (changed) {
                            row.formulas = parsed;
                            this.tableManager.queueSave(row.id, 'formulas', parsed);
                        }
                    }
                });

                // 3. Render table immediately (this calls _initializeFormulas internally)
                //    which recalculates all values AND re-renders with proper cell locking
                this.tableManager.renderTable(this.tableManager.currentData);

                // 4. After render, save computed values to DB in background (only changed ones)
                const computedFields = ['penjualan', 'total_biaya', 'asuransi', 'asuransi_jasindo', 'profit', 'idx_profit'];
                const saveQueue = {};
                this.tableManager.currentData.forEach(row => {
                    if (!row || !row.id || String(row.id).startsWith('preload_')) return;
                    const updates = {};
                    let hasChanges = false;
                    computedFields.forEach(field => {
                        const val = row[field];
                        if (val !== undefined && val !== null && val !== 0 && val !== '') {
                            updates[field] = val;
                            hasChanges = true;
                        }
                    });
                    if (this.tableManager.saveQueue[row.id] && this.tableManager.saveQueue[row.id].formulas) {
                        updates.formulas = this.tableManager.saveQueue[row.id].formulas;
                        hasChanges = true;
                        delete this.tableManager.saveQueue[row.id].formulas;
                    }
                    if (hasChanges) {
                        saveQueue[row.id] = updates;
                    }
                });

                // Batch save in background without blocking UI
                const ids = Object.keys(saveQueue);
                if (ids.length > 0) {
                    (async () => {
                        for (const id of ids) {
                            try {
                                await window.databaseManager.updateRow(id, saveQueue[id]);
                            } catch (e) {
                                console.warn('Background save failed for row', id, e);
                            }
                        }
                        this.tableManager.setSyncStatus('synced');
                    })();
                }

                this.tableManager.updateStatusBar('✓ Konfigurasi berhasil disimpan dan diterapkan!');
                closeDropdown();

            } catch (err) {
                console.error('Failed to save sheet configuration:', err);
                this.tableManager.updateStatusBar('⚠ Gagal menyimpan konfigurasi perhitungan.');
            }
        });
    }
    _handleStyle(type, value) {
        const cells = Array.from(document.querySelectorAll('.cell-selected, .cell-active'));
        if (!cells.length) return;

        cells.forEach(td => {
            const id = td.dataset.id, f = td.dataset.field;
            if (!id || !f || id.startsWith('preload_')) return;
            const row = this.tableManager.rowMap ? this.tableManager.rowMap.get(String(id)) : this.tableManager.currentData.find(r => r && r.id == id);
            if (row) {
                if (!row.formulas) row.formulas = {};
                if (!row.formulas.__formats) row.formulas.__formats = {};
                let fCfg = row.formulas.__formats[f] || {};

                if (type === 'bold') fCfg.bold = !fCfg.bold;
                if (type === 'italic') fCfg.italic = !fCfg.italic;
                if (type === 'underline') fCfg.underline = !fCfg.underline;
                if (type === 'backgroundColor') fCfg.bgColor = value;

                row.formulas.__formats[f] = fCfg;
                this.tableManager.renderCellDisplay(td, f, id);
                this.tableManager.queueSave(id, 'formulas', row.formulas);
            }
        });

        this.tableManager.updateStatusBar(`Style applied: ${type}`);
    }

    _handleFormat(type) {
        const cells = Array.from(document.querySelectorAll('.cell-selected, .cell-active'));
        if (!cells.length) return;

        cells.forEach(td => {
            const id = td.dataset.id, f = td.dataset.field;
            if (!id || !f || id.startsWith('preload_')) return;

            const row = this.tableManager.rowMap ? this.tableManager.rowMap.get(String(id)) : this.tableManager.currentData.find(r => r && r.id == id);
            if (row) {
                if (!row.formats) row.formats = {};
                // If it's already an object of the same type, keep the decimals
                if (typeof row.formats[f] === 'object' && row.formats[f] !== null && row.formats[f].type === type) {
                    // type stays same
                } else {
                    row.formats[f] = { type: type, decimals: null };
                }
                this.tableManager.renderCellDisplay(td, f, id);
                this.tableManager.queueSave(id, f, row[f]); // Trigger save which includes formats
            }
        });

        this.tableManager.updateStatusBar(`Format ${type} diterapkan ke ${cells.length} cell`);
    }
}

window.SpreadsheetToolbar = SpreadsheetToolbar;
