/**
 * YEARLY FILE MANAGER
 * Mengelola list file tahunan (KPI Finance 2025, 2026, dll)
 */
class YearlyFileManager {
    constructor() {
        this.files = [];
        this.activeFileId = localStorage.getItem('pcf-active-file-id');
    }

    async init() {
        await this.loadFiles();
        if (this.files.length === 0) {
            const currentYear = new Date().getFullYear().toString();
            console.log('No files found, creating default file for', currentYear);
            const newFile = await window.databaseManager.addFile('KPI Finance ' + currentYear);
            if (newFile) {
                this.files.push(newFile);
            }
        }

        if (this.files.length > 0) {
            if (!this.activeFileId || !this.files.find(f => f.id == this.activeFileId)) {
                const currentYear = new Date().getFullYear().toString();
                const currentYearFile = this.files.find(f => f.name.includes(currentYear));
                
                if (currentYearFile) {
                    this.activeFileId = currentYearFile.id;
                } else {
                    this.activeFileId = this.files[0].id;
                }
                localStorage.setItem('pcf-active-file-id', this.activeFileId);
            }
        }
        this._updateFileBadge();
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.fs-col-actions')) {
                document.querySelectorAll('.fs-dropdown-menu').forEach(m => m.style.display = 'none');
            }
        });
    }

    async loadFiles() {
        try {
            this.files = await databaseManager.fetchFiles();
            this.renderFileList();
            this._updateFileBadge();
        } catch (error) {
            console.error('Gagal memuat file tahunan:', error);
        }
    }

    renderFileList() {
        const container = document.getElementById('yearlyFileList');
        if (!container) return;

        if (this.files.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">Belum ada file.</div>';
            return;
        }

        container.innerHTML = this.files.map(file => `
            <div class="fs-file-row ${file.id == this.activeFileId ? 'active' : ''}" onclick="yearlyFileManager.switchFile(${file.id})">
                <div class="fs-col-name">
                    <i class="ph-duotone ph-file-xls fs-file-icon"></i>
                    <span class="fs-file-title">${file.name}</span>
                </div>
                <div class="fs-col-owner">me</div>
                <div class="fs-col-date">2:54 AM</div>
                <div class="fs-col-actions" onclick="event.stopPropagation()" style="position:relative;">
                    <button class="fs-btn-action" onclick="yearlyFileManager.toggleMenu(${file.id})" title="Opsi">
                        <i class="ph-duotone ph-dots-three-vertical"></i>
                    </button>
                    <div id="fs-menu-${file.id}" class="fs-dropdown-menu" style="display:none; position:absolute; right:0; top:100%; background:var(--bg-card); border:1px solid var(--border-light); box-shadow:var(--shadow-md); border-radius:8px; z-index:100; min-width:140px; padding:4px 0;">
                        <div onclick="yearlyFileManager.renameFile(${file.id}, '${file.name}'); yearlyFileManager.closeMenu(${file.id})" style="padding:10px 15px; cursor:pointer; font-size:0.85rem; color:var(--text-primary); transition:background 0.2s;" onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='transparent'"><i class="ph-duotone ph-pencil-simple" style="margin-right:8px; width:16px;"></i> Rename</div>
                        <div onclick="exportFullYearToExcel(${file.id}, '${file.name}'); yearlyFileManager.closeMenu(${file.id})" style="padding:10px 15px; cursor:pointer; font-size:0.85rem; color:#16a34a; transition:background 0.2s;" onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='transparent'"><i class="ph-duotone ph-file-xls" style="margin-right:8px; width:16px;"></i> Export Full</div>
                        <div onclick="yearlyFileManager.deleteFile(${file.id}, '${file.name}'); yearlyFileManager.closeMenu(${file.id})" style="padding:10px 15px; cursor:pointer; font-size:0.85rem; color:var(--red); border-top:1px solid var(--border-light); transition:background 0.2s;" onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='transparent'"><i class="ph-duotone ph-trash" style="margin-right:8px; width:16px;"></i> Hapus</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    toggleMenu(id) {
        document.querySelectorAll('.fs-dropdown-menu').forEach(menu => {
            if (menu.id !== `fs-menu-${id}`) menu.style.display = 'none';
        });
        const menu = document.getElementById(`fs-menu-${id}`);
        if (menu) menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }

    closeMenu(id) {
        const menu = document.getElementById(`fs-menu-${id}`);
        if (menu) menu.style.display = 'none';
    }

    async switchFile(id, suppressToggle = false) {
        if (window.tableManager && typeof window.tableManager.flushSaveQueue === 'function') {
            try {
                await window.tableManager.flushSaveQueue();
            } catch (err) {
                console.error('Failed to flush save queue before switching file:', err);
            }
        }
        sessionStorage.setItem('pcf-file-selected', 'true');
        if (id == this.activeFileId) {
            if (!suppressToggle) toggleFilePanel();
            return;
        }

        this.activeFileId = id;
        localStorage.setItem('pcf-active-file-id', id);
        
        if (typeof _dashboardDataLoadedForFile !== 'undefined') {
            _dashboardDataLoadedForFile = null;
        }

        this.renderFileList();
        if (!suppressToggle) toggleFilePanel();

        // Update badge label di sheets bar
        this._updateFileBadge();

        // Reload data
        showToast('Memuat data tahunan...', 'info');
        await sheetsManager.loadSheets(id);

        // Load first sheet of this file (prioritize 'Januari')
        if (sheetsManager.sheets.length > 0) {
            const janSheet = sheetsManager.sheets.find(s => s.name.toLowerCase() === 'januari');
            if (janSheet) {
                await sheetsManager.switchSheet(janSheet.id);
            } else {
                await sheetsManager.switchSheet(sheetsManager.sheets[0].id);
            }
        } else {
            // If no sheets, create default one
            await sheetsManager.addSheet('Januari');
        }

        if (currentPage === 'dashboard') {
            await loadAllData();
        }
    }

    _updateFileBadge() {
        // Update display text next to hamburger menu
        const display = document.getElementById('activeFileNameDisplay');
        if (display) {
            const activeFile = this.files.find(f => f.id == this.activeFileId);
            display.textContent = activeFile ? activeFile.name : 'KPI Finance';
        }
    }

    async addNewFile() {
        const canAdd = authManager.isAdmin() || (authManager.currentUser?.config?.role === 'pic');
        if (!canAdd) {
            showToast('Hanya admin atau PIC yang bisa menambah file tahunan.', 'warning');
            return;
        }

        // Suggest next year
        const currentYear = new Date().getFullYear();
        const existingYears = this.files.map(f => {
            const m = f.name.match(/(\d{4})/);
            return m ? parseInt(m[1]) : 0;
        }).filter(y => y > 0);
        const nextYear = existingYears.length > 0 ? Math.max(...existingYears) + 1 : currentYear;
        const suggestedName = `KPI Finance ${nextYear}`;

        // Create modal
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

        overlay.innerHTML = `
            <div class="modal-card" style="max-width:380px;">
                <div class="modal-header">
                    <h3><i class="fas fa-plus-circle"></i> File Baru</h3>
                    <button class="modal-close" id="closeNewFileModal"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Nama File Tahunan</label>
                        <input type="text" class="form-input" id="newFileNameInput" value="${suggestedName}" placeholder="Contoh: KPI Finance 2027" autocomplete="off">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-modal-cancel" id="cancelNewFile">Batal</button>
                    <button class="btn-modal-confirm" id="confirmNewFile"><i class="fas fa-check"></i> Buat File</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const nameInput = overlay.querySelector('#newFileNameInput');
        nameInput.focus();
        nameInput.select();

        overlay.querySelector('#closeNewFileModal').onclick = () => overlay.remove();
        overlay.querySelector('#cancelNewFile').onclick = () => overlay.remove();

        nameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') overlay.querySelector('#confirmNewFile').click();
            if (e.key === 'Escape') overlay.remove();
        });

        overlay.querySelector('#confirmNewFile').onclick = async () => {
            const name = nameInput.value.trim();
            if (!name) {
                nameInput.style.borderColor = '#dc2626';
                nameInput.focus();
                return;
            }

            const btn = overlay.querySelector('#confirmNewFile');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Membuat...';

            try {
                const newFile = await databaseManager.addFile(name);
                if (newFile) {
                    overlay.remove();
                    showToast(`File "${name}" berhasil dibuat`, 'success');
                    await this.loadFiles();
                    await this.switchFile(newFile.id);
                }
            } catch (error) {
                showToast('Gagal membuat file: ' + error.message, 'error');
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-check"></i> Buat File';
            }
        };
    }

    async renameFile(id, oldName) {
        if (!authManager.isAdmin()) return;

        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

        overlay.innerHTML = `
            <div class="modal-card" style="max-width:380px;">
                <div class="modal-header">
                    <h3><i class="fas fa-edit"></i> Ubah Nama</h3>
                    <button class="modal-close" id="closeRenameModal"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Nama File</label>
                        <input type="text" class="form-input" id="renameFileInput" value="${oldName}" autocomplete="off">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-modal-cancel" id="cancelRename">Batal</button>
                    <button class="btn-modal-confirm" id="confirmRename"><i class="fas fa-check"></i> Simpan</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        const input = overlay.querySelector('#renameFileInput');
        input.focus();
        input.select();

        overlay.querySelector('#closeRenameModal').onclick = () => overlay.remove();
        overlay.querySelector('#cancelRename').onclick = () => overlay.remove();
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') overlay.querySelector('#confirmRename').click();
            if (e.key === 'Escape') overlay.remove();
        });

        overlay.querySelector('#confirmRename').onclick = async () => {
            const newName = input.value.trim();
            if (!newName || newName === oldName) { overlay.remove(); return; }

            try {
                await databaseManager.renameFile(id, newName);
                overlay.remove();
                showToast('Nama file berhasil diubah', 'success');
                await this.loadFiles();
            } catch (error) {
                showToast('Gagal merename file: ' + error.message, 'error');
            }
        };
    }

    async deleteFile(id, name) {
        if (!authManager.isAdmin()) return;

        const confirmed = await showConfirm({
            title: 'Hapus File Tahunan',
            message: `Apakah Anda yakin ingin menghapus "${name}"?\n\nSemua sheet dan data di dalamnya akan terhapus PERMANEN!`,
            icon: 'danger',
            confirmText: 'Hapus Permanen',
            confirmClass: 'danger'
        });

        if (!confirmed) return;

        try {
            await databaseManager.deleteFile(id);
            showToast('File berhasil dihapus', 'success');
            await this.init(); // Re-init to pick another active file if needed
            if (this.activeFileId == id) {
                if (this.files.length > 0) await this.switchFile(this.files[0].id);
            } else {
                await this.loadFiles();
            }
        } catch (error) {
            showToast('Gagal menghapus file: ' + error.message, 'error');
        }
    }
}
