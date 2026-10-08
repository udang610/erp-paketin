/**
 * KEYBOARD MANAGER: Menangani navigasi keyboard dan shortcut untuk TableManager
 */
class KeyboardManager {
    constructor(tableManager) {
        this.tm = tableManager;
    }

    init() {
        const container = document.querySelector('.spreadsheet-container');
        if (container) container.setAttribute('tabindex', '0');

        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('paste', (e) => this.handlePaste(e));
        this.initFindReplaceEvents();
    }

    handleKeyDown(e) {
        if (typeof currentPage !== 'undefined' && currentPage !== 'table') return;
        
        // Don't intercept if focus is in an input/textarea (like find bar or cell editor)
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        const isDeleteKey = e.key === 'Delete' || e.key === 'Backspace';
        const hasSelection = this.tm.selectedRange && this.tm.selectedRange.sr !== -1;

        if (isDeleteKey && hasSelection) {
            if (this.tm.editingCell) return; // Let the editor handle it if editing
            e.preventDefault();
            this.tm.deleteSelection();
            return;
        }
        
        if (e.ctrlKey && e.key === 'h') { e.preventDefault(); this.tm.openFind(); this.tm.toggleReplace(); return; }
        if (e.key === 'Escape') {
            const fb = document.getElementById('findBar');
            if (fb && fb.style.display !== 'none') { this.tm.closeFind(); return; }
        }
        if (this.tm.editingCell) return;

        // Direct Typing to Edit (Excel Style)
        if (this.tm.activeCell && !e.ctrlKey && !e.altKey && e.key.length === 1) {
            if (this.tm.activeCell.classList.contains('cell-readonly')) return;
            this.tm.startEditCell(this.tm.activeCell, true, e.key); // Pass the character
            return;
        }

        if (e.ctrlKey && e.key === 'c') { e.preventDefault(); this.tm.copySelection(); return; }
        if (e.ctrlKey && e.key === 'x') { e.preventDefault(); this.tm.cutSelection(); return; }
        if (e.ctrlKey && e.key === 'd') { e.preventDefault(); const { sr, er, sc, ec } = this.tm.selectedRange; this.tm.autofillRange(sr, er, sc, ec); return; }
        if (e.ctrlKey && e.key === 'z') { e.preventDefault(); this.tm.history.undo(); return; }
        if (e.ctrlKey && e.key === 'y') { e.preventDefault(); this.tm.history.redo(); return; }
        if (e.ctrlKey && e.key === 'a') { e.preventDefault(); this.tm.selectAllColumns(); return; }
        
        // Toolbar formatting shortcuts
        if (e.ctrlKey && e.key === 'b') { e.preventDefault(); if (window.spreadsheetToolbar) window.spreadsheetToolbar._handleStyle('bold'); return; }
        if (e.ctrlKey && e.key === 'i') { e.preventDefault(); if (window.spreadsheetToolbar) window.spreadsheetToolbar._handleStyle('italic'); return; }
        if (e.ctrlKey && e.key === 'u') { e.preventDefault(); if (window.spreadsheetToolbar) window.spreadsheetToolbar._handleStyle('underline'); return; }
        
        // CTRL+S → status info
        if (e.ctrlKey && e.key === 's') { e.preventDefault(); this.tm.updateStatusBar('✓ Semua perubahan tersimpan'); return; }
        
        // CTRL+P → export to Excel
        if (e.ctrlKey && e.key === 'p') { e.preventDefault(); if (typeof window.exportToExcel === 'function') window.exportToExcel(); return; }
        
        if ((e.key === 'Enter' || e.key === 'F2') && this.tm.activeCell) {
            e.preventDefault();
            if (this.tm.activeCell.classList.contains('cell-readonly')) return;
            this.tm.startEditCell(this.tm.activeCell);
            return;
        }

        // ARROW KEYS Navigation
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
            if (e.shiftKey && e.key !== 'Tab') {
                const { r: anchorR, c: anchorC } = this.tm.activeCellPos;
                if (anchorR === -1) return;
                
                const { sr, er, sc, ec } = this.tm.selectedRange;
                let currentR = (anchorR === sr) ? er : sr;
                let currentC = (anchorC === sc) ? ec : sc;
                
                const maxCol = window.formulaEngine ? window.formulaEngine.colToField.length - 1 : 40;
                let nr = currentR, nc = currentC;
                if (e.key === 'ArrowUp') nr = Math.max(0, currentR - 1);
                else if (e.key === 'ArrowDown') nr = Math.min(this.tm.currentData.length - 1, currentR + 1);
                else if (e.key === 'ArrowLeft') nc = Math.max(1, currentC - 1);
                else if (e.key === 'ArrowRight') nc = Math.min(maxCol, currentC + 1);
                
                e.preventDefault();
                this.tm.selectRangeByPos(this.tm.activeCellPos, { r: nr, c: nc });
                
                // Auto-scroll logic if the new boundary goes out of view
                const tbody = document.querySelector('.spreadsheet-table tbody');
                if (tbody) {
                    const targetTr = tbody.querySelector(`tr[data-idx="${nr}"]`);
                    if (targetTr) {
                        const targetTd = targetTr.children[nc];
                        if (targetTd) {
                            const rect = targetTd.getBoundingClientRect();
                            const container = document.querySelector('.spreadsheet-container');
                            const cRect = container.getBoundingClientRect();
                            if (rect.bottom > cRect.bottom || rect.top < cRect.top || rect.right > cRect.right || rect.left < cRect.left) {
                                targetTd.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                            }
                        }
                    }
                }
            } else {
                e.preventDefault();
                let dir = e.key;
                if (e.shiftKey && e.key === 'Tab') dir = 'ShiftTab';
                this.tm.moveActiveCell(dir);
            }
        }
    }

    handlePaste(e) {
        if (typeof currentPage !== 'undefined' && currentPage !== 'table') return;
        const target = e.target;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
            if (target.id !== 'formulaBar') return;
        }
        
        if (!this.tm.editingCell) {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            this.tm.pasteFromClipboard(pastedText, e.clipboardData || window.clipboardData);
        }
    }

    initFindReplaceEvents() {
        const fi = document.getElementById('findInput');
        if (fi) {
            fi.addEventListener('input', () => this.tm.executeFind());
            fi.addEventListener('keydown', (e) => {
                e.stopPropagation();
                if (e.key === 'Enter') { e.preventDefault(); e.shiftKey ? this.tm.findPrev() : this.tm.findNext(); }
                if (e.key === 'Escape') { e.preventDefault(); this.tm.closeFind(); }
            });
        }
        const ri = document.getElementById('replaceInput');
        if (ri) {
            ri.addEventListener('keydown', (e) => {
                e.stopPropagation();
                if (e.key === 'Escape') { e.preventDefault(); this.tm.closeFind(); }
            });
        }
    }
}
