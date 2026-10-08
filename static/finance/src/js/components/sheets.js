/**
 * SHEETS MANAGER
 * Features: switch, rename, add, duplicate, delete, move left/right, drag-to-reorder
 */

class SheetsManager {
    constructor() {
        this.sheets = [];
        window.activeSheetId = null;
        this._activeMenuId = null;
        this._dragSrcIndex = null;
        this._closeMenuHandler = null;
        this._isAdding = false; // Fix double sheet bug
    }

    async init() {
        await this.loadSheets();
        this.setupEventListeners();
    }

    async loadSheets(fileId = null) {
        try {
            const fid = fileId || (window.yearlyFileManager ? window.yearlyFileManager.activeFileId : null);
            this.sheets = await databaseManager.fetchSheets(fid);

            if (!this.sheets || this.sheets.length === 0) {
                this.sheets = [];
                if (fid) {
                    console.log('No sheets found for file', fid, ', creating default sheet "Januari"');
                    const newSheet = await databaseManager.addSheet('Januari', fid);
                    if (newSheet) {
                        this.sheets.push(newSheet);
                        window.activeSheetId = newSheet.id;
                    }
                }
            }

            if (this.sheets.length > 0) {
                // Ignore localStorage and always prioritize 'Januari' or first sheet
                const janSheet = this.sheets.find(s => s.name.toLowerCase() === 'januari');
                if (janSheet) {
                    window.activeSheetId = janSheet.id;
                } else {
                    window.activeSheetId = this.sheets[0].id;
                }
            }

            this.renderTabs();
        } catch (error) {
            console.error('Gagal memuat sheets:', error);
        }
    }

    renderTabs() {
        const container = document.getElementById('sheetsList');
        if (!container) return;

        container.innerHTML = this.sheets.map((sheet, idx) => `
            <div class="sheet-tab ${sheet.id === window.activeSheetId ? 'active' : ''}"
                 data-id="${sheet.id}" data-index="${idx}" draggable="true" title="${sheet.name}">
                <span class="sheet-name" ondblclick="sheetsManager.startRename(${sheet.id})">${sheet.name}</span>
                <i class="fas fa-caret-down sheet-dropdown-icon" data-sheet-id="${sheet.id}"></i>
            </div>
        `).join('');

        container.querySelectorAll('.sheet-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                if (e.target.closest('.sheet-dropdown-icon') || e.target.tagName.toLowerCase() === 'input') return;
                const id = parseInt(tab.dataset.id);
                if (id !== window.activeSheetId) this.switchSheet(id);
            });

            const caretIcon = tab.querySelector('.sheet-dropdown-icon');
            if (caretIcon) {
                caretIcon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const id = parseInt(tab.dataset.id);
                    this.showSheetDropdown(e, id);
                });
            }

            tab.addEventListener('dragstart', (e) => {
                this._dragSrcIndex = parseInt(tab.dataset.index);
                tab.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });
            tab.addEventListener('dragend', () => {
                tab.classList.remove('dragging');
                container.querySelectorAll('.sheet-tab').forEach(t => t.classList.remove('drag-over'));
            });
            tab.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                container.querySelectorAll('.sheet-tab').forEach(t => t.classList.remove('drag-over'));
                tab.classList.add('drag-over');
            });
            tab.addEventListener('drop', (e) => {
                e.preventDefault();
                const targetIndex = parseInt(tab.dataset.index);
                if (this._dragSrcIndex !== null && this._dragSrcIndex !== targetIndex) {
                    this._reorderSheets(this._dragSrcIndex, targetIndex);
                }
            });
        });

        if (this._closeMenuHandler) document.removeEventListener('click', this._closeMenuHandler);
        this._closeMenuHandler = () => this.hideSheetDropdown();
        document.addEventListener('click', this._closeMenuHandler);
    }

    showSheetDropdown(e, id) {
        e.stopPropagation();
        this.hideSheetDropdown();

        const idx = this.sheets.findIndex(s => s.id === id);
        const sheet = this.sheets[idx];
        if (!sheet) return;

        const canEdit = authManager.hasAnyEditPermission();
        const isFirst = idx === 0;
        const isLast = idx === this.sheets.length - 1;
        const isOnly = this.sheets.length === 1;

        const menu = document.createElement('div');
        menu.id = 'sheetDropdownMenu';
        menu.className = 'sheet-context-menu';

        const items = [
            { icon: 'fa-i-cursor', label: 'Rename', action: `sheetsManager.startRename(${id})`, disabled: !canEdit },
            { icon: 'fa-copy', label: 'Duplicate Sheet', action: `sheetsManager.duplicateSheet(${id})`, disabled: !canEdit },
            { divider: true },
            { icon: 'fa-arrow-left', label: 'Pindah ke Kiri', action: `sheetsManager.moveSheet(${id},'left')`, disabled: isFirst || !canEdit },
            { icon: 'fa-arrow-right', label: 'Pindah ke Kanan', action: `sheetsManager.moveSheet(${id},'right')`, disabled: isLast || !canEdit },
            { divider: true },
            { icon: 'fa-trash-alt', label: 'Hapus Sheet', action: `sheetsManager.deleteSheet(${id})`, disabled: isOnly || !canEdit, danger: true },
        ];

        menu.innerHTML = items.map(item => {
            if (item.divider) return `<div class="sheet-menu-divider"></div>`;
            return `<div class="sheet-menu-item ${item.disabled ? 'disabled' : ''} ${item.danger ? 'danger' : ''}"
                onclick="${item.disabled ? '' : item.action + '; sheetsManager.hideSheetDropdown();'}">
                <i class="fas ${item.icon}"></i><span>${item.label}</span></div>`;
        }).join('');

        document.body.appendChild(menu);

        // Force reflow agar getBoundingClientRect akurat
        menu.offsetHeight;
        const mRect = menu.getBoundingClientRect();

        // Cari tab element langsung dari event target (lebih akurat daripada mencari by ID)
        const tabEl = e.target.closest('.sheet-tab');
        if (!tabEl) {
            console.error('Sheet tab element not found for event:', e);
            menu.remove();
            return;
        }

        const tabRect = tabEl.getBoundingClientRect();

        // Posisikan persis di atas tab yang diklik
        let top = tabRect.top - mRect.height - 6;
        let left = tabRect.left + (tabRect.width / 2) - (mRect.width / 2);

        // Jika tidak muat di atas, tampil di bawah
        if (top < 0) {
            top = tabRect.bottom + 6;
        }

        // Jangan keluar kanan layar
        if (left + mRect.width > window.innerWidth - 8) {
            left = window.innerWidth - mRect.width - 8;
        }
        // Jangan keluar kiri layar
        if (left < 4) left = 4;

        menu.style.cssText = `position:fixed;top:${top}px;left:${left}px;z-index:9999;`;
        menu.addEventListener('click', ev => ev.stopPropagation());
    }

    hideSheetDropdown() {
        const m = document.getElementById('sheetDropdownMenu');
        if (m) m.remove();
        this._activeMenuId = null;
    }

    async switchSheet(id) {
        if (window.tableManager && typeof window.tableManager.flushSaveQueue === 'function') {
            try {
                await window.tableManager.flushSaveQueue();
            } catch (err) {
                console.error('Failed to flush save queue before switching sheet:', err);
            }
        }
        window.activeSheetId = id;
        localStorage.setItem('pcf-active-sheet-id', id);
        if (typeof _dataLoaded !== 'undefined') _dataLoaded = false;
        this.renderTabs();
        tableManager.updateStatusBar('Memuat sheet...');
        const data = await databaseManager.fetchAllData(id);
        tableManager.renderTable(data);
        
        if (!authManager.isReadOnlyUser()) {
            const currentCount = data.length;
            if (currentCount === 0) {
                await tableManager.preloadEmptyRows(1000, 'fill');
            }
        }
        
        tableManager.updateStatusBar('✓ Sheet dimuat');
        
        // UX: Scroll reset and cell focus
        if (typeof tableManager !== 'undefined' && typeof tableManager.resetSheetView === 'function') {
            // Need a slight delay to ensure DOM is fully rendered after renderTable
            setTimeout(() => {
                tableManager.resetSheetView();
            }, 100);
        }
    }

    async addSheet(forcedName = null) {
        if (!authManager.hasAnyEditPermission()) {
            showToast('Anda tidak memiliki izin untuk menambah sheet.', 'warning');
            return;
        }

        if (this._isAdding) return; // Debounce / Lock

        const fileId = window.yearlyFileManager ? window.yearlyFileManager.activeFileId : null;
        if (!fileId) {
            showToast('Pilih file tahunan terlebih dahulu sebelum menambah sheet.', 'warning');
            return;
        }

        if (forcedName) {
            await this._executeAddSheet(forcedName, fileId);
        } else {
            this._showMonthPicker(fileId);
        }
    }

    _showMonthPicker(fileId) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        
        const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        
        let html = `
            <div class="modal-box" style="width: 400px; max-width: 90vw;">
                <div class="modal-header">
                    <h3><i class="fas fa-calendar-alt"></i> Pilih Bulan Sheet Baru</h3>
                    <button class="modal-close" id="closeMonthPicker"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                    ${months.map(m => `<button class="month-picker-btn" data-month="${m}">${m}</button>`).join('')}
                </div>
                <style>
                    .month-picker-btn {
                        background: var(--bg-tertiary);
                        border: 1px solid var(--border-color);
                        border-radius: 6px;
                        padding: 10px;
                        font-size: 0.85rem;
                        font-weight: 500;
                        color: var(--text-primary);
                        cursor: pointer;
                        transition: all 0.2s;
                    }
                    .month-picker-btn:hover {
                        background: var(--red-light);
                        border-color: var(--red);
                        color: var(--red);
                    }
                </style>
            </div>
        `;
        overlay.innerHTML = html;
        document.body.appendChild(overlay);

        const closeBtn = overlay.querySelector('#closeMonthPicker');
        closeBtn.onclick = () => document.body.removeChild(overlay);

        const btns = overlay.querySelectorAll('.month-picker-btn');
        btns.forEach(btn => {
            btn.onclick = () => {
                document.body.removeChild(overlay);
                this._executeAddSheet(btn.dataset.month, fileId);
            };
        });
    }

    async _executeAddSheet(name, fileId) {
        this._isAdding = true;
        try {
            tableManager.updateStatusBar('Membuat sheet baru...');
            const newSheet = await databaseManager.addSheet(name, fileId);
            if (newSheet) {
                this.sheets.push(newSheet);
                await this.switchSheet(newSheet.id);
                showToast(`Sheet "${name}" berhasil dibuat`, 'success');
            }
        } catch (error) {
            console.error('Gagal membuat sheet:', error);
            showToast('Gagal membuat sheet: ' + error.message, 'error');
            tableManager.updateStatusBar('');
        } finally {
            this._isAdding = false;
        }
    }

    async duplicateSheet(id) {
        if (!authManager.hasAnyEditPermission()) return;
        const sheet = this.sheets.find(s => s.id === id);
        if (!sheet) return;
        try {
            tableManager.updateStatusBar('Menduplikasi sheet...');
            const newName = sheet.name + ' (Copy)';
            const newSheet = await databaseManager.addSheet(newName);
            if (newSheet) {
                const sourceData = await databaseManager.fetchAllData(id);
                if (sourceData && sourceData.length > 0) {
                    const filtered = sourceData.filter(r => r.nama || r.awb || r.penjualan);
                    if (filtered.length > 0) {
                        const chunks = [];
                        for (let i = 0; i < filtered.length; i += 100) chunks.push(filtered.slice(i, i + 100));
                        for (const chunk of chunks) {
                            const rows = chunk.map(row => {
                                const copy = { ...row };
                                delete copy.id; delete copy.created_at; delete copy.updated_at;
                                copy.sheet_id = newSheet.id;
                                return copy;
                            });
                            await databaseManager.insertRowsBulk(rows);
                        }
                    }
                }
                this.sheets.push(newSheet);
                await this.switchSheet(newSheet.id);
                tableManager.updateStatusBar(`✓ Sheet "${newName}" dibuat`);
            }
        } catch (error) {
            console.error('Gagal menduplikasi sheet:', error);
            showToast('Gagal menduplikasi: ' + error.message, 'error');
            tableManager.updateStatusBar('');
        }
    }

    async moveSheet(id, direction) {
        if (!authManager.hasAnyEditPermission()) return;
        const idx = this.sheets.findIndex(s => s.id === id);
        if (idx === -1) return;
        const newIdx = direction === 'left' ? idx - 1 : idx + 1;
        if (newIdx < 0 || newIdx >= this.sheets.length) return;
        this._reorderSheets(idx, newIdx);
    }

    _reorderSheets(fromIdx, toIdx) {
        const moved = this.sheets.splice(fromIdx, 1)[0];
        this.sheets.splice(toIdx, 0, moved);
        this.renderTabs();
        this.sheets.forEach((sheet, i) => {
            databaseManager.updateSheetOrder(sheet.id, i).catch(() => { });
        });
    }

    async deleteSheet(id) {
        if (!authManager.hasAnyEditPermission()) return;
        if (this.sheets.length <= 1) {
            showToast('Tidak bisa menghapus sheet terakhir.', 'warning');
            return;
        }
        const sheet = this.sheets.find(s => s.id === id);
        if (!sheet) return;

        const confirmed = await showConfirm({
            title: 'Hapus Sheet',
            message: `Hapus sheet "${sheet.name}"?\n\nSemua data di sheet ini akan dihapus permanen!`,
            icon: 'danger',
            confirmText: 'Hapus',
            confirmClass: 'danger'
        });

        if (!confirmed) return;

        try {
            tableManager.updateStatusBar('Menghapus sheet...');
            await databaseManager.deleteSheet(id);
            this.sheets = this.sheets.filter(s => s.id !== id);
            await this.switchSheet(this.sheets[0].id);
            showToast(`Sheet "${sheet.name}" berhasil dihapus`, 'success');
        } catch (error) {
            console.error('Gagal menghapus sheet:', error);
            showToast('Gagal menghapus: ' + error.message, 'error');
            tableManager.updateStatusBar('');
        }
    }

    startRename(id) {
        if (!authManager.hasAnyEditPermission()) return;
        const tab = document.querySelector(`.sheet-tab[data-id="${id}"]`);
        if (!tab) return;
        const nameSpan = tab.querySelector('.sheet-name');
        const currentName = nameSpan.textContent;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentName;
        input.className = 'sheet-rename-input';
        input.style.cssText = 'width:90px;padding:1px 4px;border:1px solid #1d4ed8;border-radius:3px;outline:none;font-size:0.78rem;background:var(--bg-primary);color:var(--text-primary);';
        nameSpan.replaceWith(input);
        input.focus(); input.select();
        const finish = async () => {
            const newName = input.value.trim() || currentName;
            if (newName !== currentName) {
                try {
                    await databaseManager.renameSheet(id, newName);
                    const s = this.sheets.find(s => s.id === id);
                    if (s) s.name = newName;
                    showToast('Nama sheet berhasil diubah', 'success');
                } catch (error) {
                    showToast('Gagal mengganti nama: ' + error.message, 'error');
                }
            }
            this.renderTabs();
        };
        input.addEventListener('blur', finish);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') input.blur();
            if (e.key === 'Escape') { input.value = currentName; input.blur(); }
        });
    }

    showSheetMenu(event, id) {
        event.stopPropagation();
        this.showSheetDropdown(event, id);
    }

    setupEventListeners() {
        const btnAdd = document.getElementById('btnAddSheet');
        if (!btnAdd) return;

        btnAdd.addEventListener('click', (e) => {
            if (authManager.hasAnyEditPermission()) this.addSheet();
            else showToast('Anda tidak memiliki izin untuk menambah sheet.', 'warning');
        });
    }
}

// Global instance
window.sheetsManager = new SheetsManager();
const sheetsManager = window.sheetsManager;