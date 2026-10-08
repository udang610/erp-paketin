document.addEventListener('DOMContentLoaded', () => {
    function initColumnResizing() {
        const thead = document.querySelector('#kpiTable thead');
        if (!thead) return;

        const ths = thead.querySelectorAll('th');
        ths.forEach(th => {
            // Ignore index or action columns if they shouldn't be resized
            if (th.classList.contains('col-index') || th.classList.contains('col-actions')) return;

            // Prevent adding multiple resizers if already added
            if (th.querySelector('.col-resizer')) return;

            const resizer = document.createElement('div');
            resizer.classList.add('col-resizer');
            th.appendChild(resizer);
            th.style.position = 'relative';

            let startX, startWidth;

            resizer.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                startX = e.pageX;
                startWidth = th.offsetWidth;
                document.documentElement.classList.add('resizing');
                
                const onMouseMove = (eMove) => {
                    const currentX = eMove.pageX;
                    const diffX = currentX - startX;
                    const newWidth = Math.max(30, startWidth + diffX);
                    th.style.width = `${newWidth}px`;
                    th.style.minWidth = `${newWidth}px`;
                    th.style.maxWidth = `${newWidth}px`;
                };

                const onMouseUp = () => {
                    document.documentElement.classList.remove('resizing');
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                    
                    if (window.tableManager && window.tableManager.colWidths) {
                        window.tableManager.colWidths[th.dataset.field] = th.style.width;
                    }
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });

            // Double click to auto-fit like Excel
            resizer.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                if (window.tableManager && typeof window.tableManager.autoFitColumns === 'function') {
                    window.tableManager.autoFitColumns(th.dataset.field);
                }
            });
        });
    }

    // Initialize resizers immediately
    initColumnResizing();

    // Re-initialize if table structure changes (e.g., sheets change)
    const observer = new MutationObserver((mutations) => {
        let shouldInit = false;
        mutations.forEach(m => {
            if (m.type === 'childList') shouldInit = true;
        });
        if (shouldInit) initColumnResizing();
    });

    const thead = document.querySelector('#kpiTable thead');
    if (thead) {
        observer.observe(thead, { childList: true, subtree: true });
    }
});
