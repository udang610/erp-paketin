/**
 * SELECTION MANAGER: Menangani logika seleksi rentang sel, active cell, dan auto-scroll
 */
class SelectionManager {
    constructor(tableManager) {
        this.tm = tableManager;
        this.autoScrollInterval = null;

        // Reposition overlay on browser zoom (Ctrl +/-) or window resize
        window.addEventListener('resize', () => {
            if (this.tm && this.tm.activeCell) {
                // Using requestAnimationFrame to ensure layout has updated after resize
                requestAnimationFrame(() => {
                    this._updateHighlightOverlay(this.tm.activeCell);
                });
            }
        });
    }

    selectCell(td) {
        this.tm.clearReferencedHighlights();
        const tr = td.closest('tr');
        const r = parseInt(tr.dataset.idx);
        const c = td.cellIndex;
        
        this.tm.selectedRange = { sr: r, er: r, sc: c, ec: c };
        this.tm.activeCellPos = { r, c };
        this.tm.activeCell = td;
        
        this._updateSelectionUI();
        if (td.dataset.id && !td.dataset.id.startsWith('preload_')) {
            this.tm.showLastEditInfo(td.dataset.id);
        }
        this.tm._updateFormulaBar(td);
        this.tm.broadcastPresence(); // Broadcast posisi ke user lain
    }

    selectRangeByPos(s, e) {
        this.tm.selectedRange = {
            sr: Math.min(s.r, e.r),
            er: Math.max(s.r, e.r),
            sc: Math.min(s.c, e.c),
            ec: Math.max(s.c, e.c)
        };
        this._updateSelectionUI();
        this.tm.broadcastPresence(); // Broadcast rentang ke user lain
    }

    selectRange(sTd, eTd) {
        const s = { r: parseInt(sTd.closest('tr').dataset.idx), c: sTd.cellIndex };
        const e = { r: parseInt(eTd.closest('tr').dataset.idx), c: eTd.cellIndex };
        this.selectRangeByPos(s, e);
    }

    handleAutoScroll(e) {
        const container = document.querySelector('.spreadsheet-container');
        if (!container) return;

        const rect = container.getBoundingClientRect();
        const threshold = 50; // Jarak dari pinggir untuk mulai scroll
        let scrollX = 0;
        let scrollY = 0;

        if (e.clientX < rect.left + threshold) scrollX = -25;
        else if (e.clientX > rect.right - threshold) scrollX = 25;

        if (e.clientY < rect.top + threshold) scrollY = -25;
        else if (e.clientY > rect.bottom - threshold) scrollY = 25;

        if (scrollX !== 0 || scrollY !== 0) {
            if (!this.autoScrollInterval) {
                this.autoScrollInterval = setInterval(() => {
                    container.scrollLeft += scrollX;
                    container.scrollTop += scrollY;
                    
                    // Update seleksi saat scroll otomatis berjalan
                    const targetEl = document.elementFromPoint(e.clientX, e.clientY);
                    const targetTd = targetEl?.closest('td');
                    const targetTh = targetEl?.closest('th');
                    
                    if (targetTd && !targetTd.classList.contains('col-index') && !targetTd.classList.contains('col-actions')) {
                        const tr = targetTd.closest('tr');
                        if (tr && tr.dataset.idx !== undefined) {
                            const r = parseInt(tr.dataset.idx);
                            const c = targetTd.cellIndex;
                            this.selectRangeByPos(this.tm.dragStartPos, { r, c });
                        }
                    } else if (targetTh && !targetTh.classList.contains('col-index') && !targetTh.classList.contains('col-actions')) {
                        const c = targetTh.cellIndex;
                        if (c !== undefined && c >= 0) {
                            this.selectRangeByPos(this.tm.dragStartPos, { r: 0, c });
                        }
                    }
                }, 30);
            }
        } else {
            this.stopAutoScroll();
        }
    }

    stopAutoScroll() {
        if (this.autoScrollInterval) {
            clearInterval(this.autoScrollInterval);
            this.autoScrollInterval = null;
        }
    }

    _updateSelectionUI() {
        // Forcefully clear all selection classes from the entire document
        document.querySelectorAll('.cell-selected, .cell-active, .row-active, .cell-editing').forEach(el => {
            el.classList.remove('cell-selected', 'cell-active', 'row-active', 'cell-editing');
        });
        
        this.tm.selectedCells = [];
        const { sr, er, sc, ec } = this.tm.selectedRange;
        const { r: ar, c: ac } = this.tm.activeCellPos;

        if (sr === -1) {
            this._updateHighlightOverlay(null);
            return;
        }

        document.querySelectorAll('#kpiTableBody tr.spreadsheet-row').forEach(tr => {
            const ridx = parseInt(tr.dataset.idx);
            if (ridx >= sr && ridx <= er) {
                Array.from(tr.children).forEach(td => {
                    const cidx = td.cellIndex;
                    if (cidx >= sc && cidx <= ec && !td.classList.contains('col-index') && !td.classList.contains('col-actions')) {
                        td.classList.add('cell-selected');
                        this.tm.selectedCells.push(td);
                        if (ridx === ar && cidx === ac) {
                            td.classList.add('cell-active');
                            tr.classList.add('row-active');
                            this.tm.activeCell = td;
                        }
                    }
                });
            }
        });

        // Also ensure VirtualScroller doesn't have stale state if it exists
        if (this.tm.virtualScroller && this.tm.virtualScroller.tbody) {
            this.tm.virtualScroller.tbody.querySelectorAll('.cell-selected:not(.cell-active)').forEach(el => {
                // If an element has cell-selected but is not in tm.selectedCells, it's stale
                if (!this.tm.selectedCells.includes(el)) {
                    el.classList.remove('cell-selected');
                }
            });
        }

        const rc = er - sr + 1, cc = ec - sc + 1;
        if (rc > 1 || cc > 1) this.tm.updateStatusBar(`${rc} x ${cc} dipilih`);

        // Position the overlay highlight over the active cell
        this._updateHighlightOverlay(this.tm.activeCell);
    }

    /**
     * Creates and positions an overlay div that draws the red active cell border
     * ABOVE the sticky header (z-index 400 > header's 300).
     * This guarantees the red border is visible at any zoom level (80%, 90%, 100%).
     */
    _updateHighlightOverlay(td) {
        let overlay = document.getElementById('cellHighlightOverlay');
        const container = document.querySelector('.spreadsheet-container');

        // Create overlay element if it doesn't exist yet
        if (!overlay && container) {
            overlay = document.createElement('div');
            overlay.id = 'cellHighlightOverlay';
            overlay.className = 'cell-highlight-overlay';
            container.appendChild(overlay);
        }

        if (!td || !overlay || !container) {
            if (overlay) overlay.style.display = 'none';
            return;
        }

        const tdRect = td.getBoundingClientRect();
        const contRect = container.getBoundingClientRect();

        overlay.style.display = 'block';
        overlay.style.left = (tdRect.left - contRect.left + container.scrollLeft - 1) + 'px';
        overlay.style.top = (tdRect.top - contRect.top + container.scrollTop - 1) + 'px';
        overlay.style.width = (tdRect.width + 2) + 'px';
        overlay.style.height = (tdRect.height + 2) + 'px';
    }
}
