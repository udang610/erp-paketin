/**
 * ERP Paketin - Global Input Masking & Data Sanitization
 * Auto-applies standard formatting for NPWP, Phone numbers, and Bank Accounts.
 */
(function() {
    function formatNPWP(val) {
        // Strip non-digits
        var clean = val.replace(/\D/g, '').substring(0, 16);
        if (clean.length === 0) return '';
        
        // 15 Digit format: 00.000.000.0-000.000 or 16 digit: 00.000.000.0-000.0000
        var parts = [];
        if (clean.length > 0) parts.push(clean.substring(0, 2));
        if (clean.length > 2) parts.push(clean.substring(2, 5));
        if (clean.length > 5) parts.push(clean.substring(5, 8));
        
        var formatted = parts.join('.');
        if (clean.length > 8) {
            formatted += '.' + clean.substring(8, 9);
        }
        if (clean.length > 9) {
            formatted += '-' + clean.substring(9, 12);
        }
        if (clean.length > 12) {
            formatted += '.' + clean.substring(12, 16);
        }
        return formatted;
    }

    function formatPhone(val) {
        // Allow leading +, digits, and hyphens
        var hasPlus = val.startsWith('+');
        var clean = val.replace(/[^\d]/g, '');
        if (clean.length === 0) return hasPlus ? '+' : '';
        return (hasPlus ? '+' : '') + clean;
    }

    function initInputMasks() {
        // 1. NPWP Inputs
        var npwpInputs = document.querySelectorAll('input[name*="npwp" i], input[data-mask="npwp"], input#id_npwp');
        npwpInputs.forEach(function(input) {
            input.setAttribute('placeholder', '00.000.000.0-000.000');
            input.setAttribute('maxlength', '20');
            input.addEventListener('input', function(e) {
                var pos = this.selectionStart;
                var prevLen = this.value.length;
                this.value = formatNPWP(this.value);
                var diff = this.value.length - prevLen;
                this.setSelectionRange(pos + diff, pos + diff);
            });
        });

        // 2. Phone / WhatsApp Inputs
        var phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="phone" i], input[name*="telepon" i], input[data-mask="phone"]');
        phoneInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                this.value = formatPhone(this.value);
            });
        });

        // 3. Bank Account / Pure Numeric Inputs
        var numericInputs = document.querySelectorAll('input[data-mask="numeric"], input[name*="rekening" i], input[name*="bank_account" i]');
        numericInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                this.value = this.value.replace(/\D/g, '');
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInputMasks);
    } else {
        initInputMasks();
    }
})();
