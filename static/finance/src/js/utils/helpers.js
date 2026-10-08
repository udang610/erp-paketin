/**
 * GENERAL HELPERS v2.0
 */
const Helpers = {
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    generateId() {
        return Math.random().toString(36).substr(2, 9);
    },

    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },

    showToast(message, type = 'info') {
        // Trigger event for Toast component or use global function if available
        const event = new CustomEvent('show-toast', {
            detail: { message, type }
        });
        window.dispatchEvent(event);
        console.log(`[Toast ${type.toUpperCase()}]: ${message}`);
    }
};

window.Helpers = Helpers;
