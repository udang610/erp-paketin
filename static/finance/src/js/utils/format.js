/**
 * FORMATTER UTILITIES v2.0
 */
const Formatter = {
    currency(value) {
        if (value === null || value === undefined || isNaN(value)) return 'Rp 0';
        return 'Rp ' + new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    },

    number(value) {
        if (value === null || value === undefined || isNaN(value)) return '0';
        return new Intl.NumberFormat('en-US').format(value);
    },

    percent(value) {
        if (value === null || value === undefined || isNaN(value)) return '0%';
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(value);
    },

    date(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('id-ID', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        }).format(date);
    },

    parseLocaleFloat(val) {
        if (val === null || val === undefined || val === '') return 0;
        if (typeof val === 'number') return val;

        let cleaned = String(val).replace(/Rp\s?/gi, '').replace(/\s/g, '').trim();
        if (!cleaned) return 0;

        // Treat comma (,) as thousands separator -> remove it!
        cleaned = cleaned.replace(/,/g, '');

        // Treat dot (.) as decimal separator -> keep it as is!
        const num = parseFloat(cleaned);
        return isNaN(num) ? 0 : num;
    },
    
    parseDateRobust(val) {
        if (!val) return '';
        val = String(val).trim();
        
        // 1. Check if it's an Excel serial date (numeric value)
        if (/^\d{4,5}$/.test(val)) {
            const serial = parseInt(val, 10);
            if (serial > 25000 && serial < 70000) { // Valid range for modern dates
                const jsDate = new Date((serial - 25569) * 86400 * 1000);
                return jsDate.toISOString().split('T')[0]; // returns YYYY-MM-DD
            }
        }
        
        // 2. Parse text formats
        let p = val.split(/[-/.\s,]+/); // Split by dash, slash, dot, space, comma
        if (p.length >= 3) {
            let d, m, y;
            // Handle YYYY-MM-DD or YYYY/MM/DD
            if (p[0].length === 4) {
                [y, m, d] = p;
            } else {
                let part1 = parseInt(p[0], 10);
                let part2 = parseInt(p[1], 10);
                let part3 = p[2];
                
                const monthNames = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'mei': 5,
                    'jun': 6, 'jul': 7, 'aug': 8, 'agu': 8, 'sep': 9,
                    'oct': 10, 'okt': 10, 'nov': 11, 'dec': 12, 'des': 12
                };
                
                let monthStr1 = p[0].toLowerCase().substring(0,3);
                let monthStr2 = p[1].toLowerCase().substring(0,3);
                
                if (monthNames[monthStr2]) {
                    d = part1;
                    m = monthNames[monthStr2];
                    y = part3;
                } else if (monthNames[monthStr1]) {
                    m = monthNames[monthStr1];
                    d = part2;
                    y = part3;
                } else {
                    if (part1 > 12) {
                        d = part1; m = part2; y = part3; // DD/MM/YYYY
                    } else if (part2 > 12) {
                        m = part1; d = part2; y = part3; // MM/DD/YYYY (US Format)
                    } else {
                        d = part1; m = part2; y = part3; // Ambiguous, assume Indonesian standard DD/MM/YYYY
                    }
                }
            }
            
            y = String(y).replace(/\D/g, '');
            if (y.length === 2) y = '20' + y;
            
            const numY = parseInt(y, 10);
            const numM = parseInt(m, 10);
            const numD = parseInt(d, 10);
            
            if (numY > 1900 && numM >= 1 && numM <= 12 && numD >= 1 && numD <= 31) {
                return `${numY}-${String(numM).padStart(2, '0')}-${String(numD).padStart(2, '0')}`;
            }
        }
        
        // 3. Native fallback
        const dateObj = new Date(val);
        if (!isNaN(dateObj.getTime())) {
            return dateObj.toISOString().split('T')[0];
        }
        
        return ''; 
    }
};

window.Formatter = Formatter;
