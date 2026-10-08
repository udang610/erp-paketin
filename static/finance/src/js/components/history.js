/**
 * HISTORY MANAGER: Menangani logika Undo dan Redo untuk TableManager
 */
class HistoryManager {
    constructor(tableManager) {
        this.tm = tableManager;
        this.undoStack = [];
        this.redoStack = [];
    }

    push(action) {
        this.undoStack.push(action);
        this.redoStack = [];
    }

    async undo() {
        if (!this.undoStack.length) { 
            this.tm.updateStatusBar('Tidak ada undo'); 
            return; 
        }
        const a = this.undoStack.pop();
        this.redoStack.push(a);
        
        if (a.type === 'batch') {
            const ai = new Set();
            let firstTd = null;
            for (const i of a.actions) {
                this.tm.updateCellValue(i.id, i.field, i.oldValue);
                
                // Restore formula if tracked
                if (i.oldFormula !== undefined || i.newFormula !== undefined) {
                    const row = this.tm.currentData.find(r => r.id == i.id);
                    if (row) {
                        if (row.formulas && typeof row.formulas === 'string') {
                            try { row.formulas = JSON.parse(row.formulas); } catch (e) { row.formulas = {}; }
                        }
                        if (!row.formulas) row.formulas = {};
                        
                        if (i.oldFormula !== undefined) {
                            row.formulas[i.field] = i.oldFormula;
                        } else {
                            delete row.formulas[i.field];
                        }
                        this.tm.queueSave(i.id, 'formulas', JSON.stringify(row.formulas));
                    }
                }
                
                const td = document.querySelector('td[data-field="' + i.field + '"][data-id="' + i.id + '"]');
                if (td) { 
                    if (!firstTd) firstTd = td;
                    this.tm.renderCellDisplay(td, i.field, i.id); 
                    this.flashCell(td, 'undo');
                }
                ai.add(i.id); 
                this.tm.queueSave(i.id, i.field, i.oldValue);
            }
            if (firstTd) firstTd.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
            
            // Trigger auto-calc and formula dependents
            ai.forEach(id => this.tm.updateRelatedCells(id));
            if (window.formulaEngine) {
                for (const i of a.actions) {
                    const cellA1 = window.formulaEngine._mapCellIdToA1(`${i.id}:${i.field}`);
                    if (cellA1) window.formulaEngine.recalculateDependents(cellA1);
                }
            }
            
            this.tm.renderTable(this.tm.currentData);
            this.tm.updateStatusBar(`✓ Undo: ${a.actions.length} perubahan dikembalikan`);
        } else if (a.type === 'deleteRow') {
            try {
                const r = await window.databaseManager.insertRow(a.row);
                if (r) { 
                    this.tm.currentData.push(r); 
                    this.tm.originalData.push(r); 
                    this.tm.renderTable(this.tm.currentData); 
                    showToast('Baris berhasil dikembalikan', 'success');
                }
            } catch (e) { 
                console.error(e); 
                showToast('Gagal undo hapus baris', 'error');
            }
        }
        this.tm.flushSaveQueue();
    }

    async redo() {
        if (!this.redoStack.length) { 
            this.tm.updateStatusBar('Tidak ada redo'); 
            return; 
        }
        const a = this.redoStack.pop();
        this.undoStack.push(a);
        
        if (a.type === 'batch') {
            const ai = new Set();
            let firstTd = null;
            for (const i of a.actions) {
                const v = i.newValue !== undefined ? i.newValue : null;
                this.tm.updateCellValue(i.id, i.field, v);
                
                // Restore newFormula if tracked
                if (i.oldFormula !== undefined || i.newFormula !== undefined) {
                    const row = this.tm.currentData.find(r => r.id == i.id);
                    if (row) {
                        if (row.formulas && typeof row.formulas === 'string') {
                            try { row.formulas = JSON.parse(row.formulas); } catch (e) { row.formulas = {}; }
                        }
                        if (!row.formulas) row.formulas = {};
                        
                        if (i.newFormula !== undefined) {
                            row.formulas[i.field] = i.newFormula;
                        } else {
                            delete row.formulas[i.field];
                        }
                        this.tm.queueSave(i.id, 'formulas', JSON.stringify(row.formulas));
                    }
                }

                const td = document.querySelector('td[data-field="' + i.field + '"][data-id="' + i.id + '"]');
                if (td) { 
                    if (!firstTd) firstTd = td;
                    this.tm.renderCellDisplay(td, i.field, i.id); 
                    this.flashCell(td, 'redo');
                }
                ai.add(i.id); 
                this.tm.queueSave(i.id, i.field, v);
            }
            if (firstTd) firstTd.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
            
            // Trigger auto-calc and formula dependents
            ai.forEach(id => this.tm.updateRelatedCells(id));
            if (window.formulaEngine) {
                for (const i of a.actions) {
                    const cellA1 = window.formulaEngine._mapCellIdToA1(`${i.id}:${i.field}`);
                    if (cellA1) window.formulaEngine.recalculateDependents(cellA1);
                }
            }

            this.tm.renderTable(this.tm.currentData);
            this.tm.updateStatusBar(`↻ Redo: ${a.actions.length} perubahan diterapkan ulang`);
        } else if (a.type === 'deleteRow') {
            try {
                this.tm.currentData = this.tm.currentData.filter(r => r.id != a.row.id);
                this.tm.originalData = this.tm.originalData.filter(r => r.id != a.row.id);
                this.tm.renderTable(this.tm.currentData);
                await window.databaseManager.deleteRow(a.row.id);
                showToast('Penghapusan baris di-redo', 'success');
            } catch (e) {
                console.error(e);
                showToast('Gagal redo hapus baris', 'error');
            }
        }
        this.tm.flushSaveQueue();
    }

    flashCell(td, type = 'undo') {
        if (!td) return;
        const color = type === 'undo' ? 'rgba(255, 165, 0, 0.3)' : 'rgba(34, 197, 94, 0.3)';
        const originalBg = td.style.backgroundColor;
        td.style.transition = 'background-color 0.1s';
        td.style.backgroundColor = color;
        setTimeout(() => {
            td.style.transition = 'background-color 0.8s';
            td.style.backgroundColor = originalBg;
            setTimeout(() => { 
                td.style.transition = ''; 
                td.style.backgroundColor = ''; 
            }, 800);
        }, 150);
    }
}

