const getDbApiBaseUrl = () => {
    if (window.location.protocol === 'file:' || ['3000', '5173', '5500'].includes(window.location.port)) {
        return 'http://localhost:8000';
    }
    return '';
};

/**
 * DATABASE MANAGER (Django API Backend)
 * Mengelola CRUD kpi_finance + manajemen pic_permissions via Django REST API.
 */
class DatabaseManager {
    constructor() {
        this.baseUrl = getDbApiBaseUrl() + '/finance/api';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    async _fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const fetchOptions = {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            credentials: 'include' // use 'include' if relying on session cookies for auth
        };

        if (options.method && options.method.toUpperCase() !== 'GET' && typeof getCsrfToken === 'function') {
            fetchOptions.headers['X-CSRFToken'] = getCsrfToken();
        }

        const response = await fetch(url, fetchOptions);
        if (!response.ok) {
            let errorMsg = response.statusText;
            try {
                const errData = await response.json();
                errorMsg = JSON.stringify(errData);
            } catch (e) {}
            throw new Error(`API Error: ${response.status} - ${errorMsg}`);
        }
        
        // Handle 204 No Content
        if (response.status === 204) return null;
        return await response.json();
    }

    // ==================== YEARLY FILES ====================

    async fetchFiles() {
        try {
            return await this._fetch('/files/');
        } catch (error) {
            console.error('Fetch files error:', error.message);
            return [{ id: 1, name: 'KPI Finance 2026' }];
        }
    }

    async addFile(name) {
        return await this._fetch('/files/', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
    }

    async renameFile(id, newName) {
        return await this._fetch(`/files/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify({ name: newName })
        });
    }

    async deleteFile(id) {
        await this._fetch(`/files/${id}/`, { method: 'DELETE' });
    }

    // ==================== SHEETS ====================

    async fetchSheets(fileId = null) {
        try {
            let url = '/sheets/';
            if (fileId) url += `?file_id=${fileId}`;
            return await this._fetch(url);
        } catch (error) {
            console.error('Fetch sheets error:', error.message);
            return [];
        }
    }

    async addSheet(name, fileId, type = 'data') {
        if (!fileId) throw new Error('file_id diperlukan untuk membuat sheet baru.');
        const existing = await this.fetchSheets(fileId);
        const nextOrder = existing.length > 0 ? Math.max(...existing.map(s => s.sort_order || 0)) + 1 : 0;

        return await this._fetch('/sheets/', {
            method: 'POST',
            body: JSON.stringify({
                name,
                kpi_file: fileId,
                sheet_type: type,
                sort_order: nextOrder
            })
        });
    }

    async renameSheet(id, newName) {
        return await this._fetch(`/sheets/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify({ name: newName })
        });
    }

    async deleteSheet(id) {
        await this._fetch(`/sheets/${id}/`, { method: 'DELETE' });
    }

    async updateSheetOrder(id, sortOrder) {
        await this._fetch(`/sheets/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify({ sort_order: sortOrder })
        });
    }

    // ==================== USER MANAGEMENT (Admin) ====================

    async listUsers() {
        try {
            return await this._fetch('/profiles/');
        } catch (e) {
            console.warn('listUsers error:', e.message);
            return [];
        }
    }

    async inviteUser(email, role, fullName) {
        throw new Error('Gunakan Django Admin Panel untuk mengelola user.');
    }

    async upsertUserConfig(email, name, role) {
        // Implement via Django Admin
        return null;
    }

    async fetchUserConfigs() {
        try {
            return await this._fetch('/profiles/');
        } catch (error) {
            console.warn('fetchUserConfigs error:', error.message);
            return [];
        }
    }

    async deleteUserConfig(email) {
        throw new Error('Gunakan Django Admin Panel untuk menghapus user.');
    }

    async fetchUserConfig(email) {
        const users = await this.fetchUserConfigs();
        return users.find(u => u.email === email || u.user?.username === email);
    }

    async deleteUserFull(userId, email) {
        throw new Error('Gunakan Django Admin Panel untuk menghapus user.');
    }

    async updateUserRole(email, role) {
        throw new Error('Gunakan Django Admin Panel untuk mengubah role.');
    }

    // ==================== FINANCE DATA ====================

    async fetchAllDataForFile(fileId) {
        if (!fileId) return [];
        const sheets = await this.fetchSheets(fileId);
        if (sheets.length === 0) return [];
        
        let allData = [];
        for (const sheet of sheets) {
            const data = await this.fetchAllData(sheet.id);
            allData = allData.concat(data);
        }
        return allData;
    }

    async fetchAllData(sheetId = null) {
        try {
            let url = '/finance/';
            if (sheetId !== null) url += `?sheet_id=${sheetId}`;
            const data = await this._fetch(url);
            
            // Format dates back for the frontend (YYYY-MM-DD)
            return data.map(row => {
                if (row.tanggal_pickup) row.tanggal_pickup = row.tanggal_pickup.split('T')[0];
                if (row.sheet) row.sheet_id = row.sheet;
                return row;
            });
        } catch (error) {
            console.error('Fetch error:', error);
            return [];
        }
    }

    async fetchNewData(sheetId, minId) {
        try {
            // Hanya fetch row dari CRM untuk menghindari race condition ID dengan baris kosong (manual)
            let url = `/finance/?sheet_id=${sheetId}&id__gt=${minId}&source=crm`;
            const data = await this._fetch(url);
            
            return data.map(row => {
                if (row.tanggal_pickup) row.tanggal_pickup = row.tanggal_pickup.split('T')[0];
                if (row.sheet) row.sheet_id = row.sheet;
                return row;
            });
        } catch (error) {
            console.error('Fetch new data error:', error);
            return [];
        }
    }

    _formatDateForDjango(dateVal) {
        if (dateVal === undefined || dateVal === null || dateVal === '') return null;
        const dateStr = String(dateVal).trim();
        if (!dateStr || dateStr === 'null' || dateStr === 'undefined' || dateStr === '-') return null;
        
        // If it already matches YYYY-MM-DD exactly
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
        
        // Try parsing DD/MM/YYYY or DD-MM-YYYY or YYYY/MM/DD
        const parts = dateStr.split(/[\/\-]/);
        if (parts.length === 3) {
            let day, month, year;
            if (parts[0].length === 4) {
                // YYYY-MM-DD or YYYY/MM/DD
                year = parts[0];
                month = parts[1];
                day = parts[2];
            } else {
                // DD/MM/YYYY
                day = parts[0];
                month = parts[1];
                year = parts[2];
            }
            // Ensure year is 4 digits
            if (year.length === 2) {
                year = '20' + year;
            }
            month = String(month).padStart(2, '0');
            day = String(day).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
        
        // Fallback: try parsing with native Date
        try {
            const d = new Date(dateStr);
            if (!isNaN(d.getTime())) {
                const y = d.getFullYear();
                const m = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                return `${y}-${m}-${day}`;
            }
        } catch (e) {}
        
        return null;
    }

    async upsertDataBatch(rows) {
        if (!rows || rows.length === 0) return [];
        
        // All DecimalField columns in KpiFinance model (max decimal_places=4)
        const decimalFields = [
            'aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil',
            'harga', 'surcharge', 'packing', 'handling', 'penjualan',
            'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv',
            'ops', 'asuransi', 'asuransi_jasindo', 'nilai_barang',
            'total_biaya', 'profit', 'idx_profit'
        ];

        // Django DRF doesn't support bulk upsert by default, so we'll simulate it for now.
        // Or if you added a custom bulk endpoint, call that.
        // For now, loop through and POST/PATCH individually.
        const results = [];
        for (const row of rows) {
            const rowData = { ...row };
            delete rowData.id; // avoid ID conflicts on insert
            rowData.tanggal_pickup = this._formatDateForDjango(row.tanggal_pickup);
            
            // Map sheet_id -> sheet for Django
            let finalSheetId = rowData.sheet_id;
            if (finalSheetId === undefined || finalSheetId === null || finalSheetId === 'undefined' || finalSheetId === 'null' || finalSheetId === '') {
                finalSheetId = window.activeSheetId;
            }
            if (finalSheetId !== undefined && finalSheetId !== null && finalSheetId !== 'undefined' && finalSheetId !== 'null' && finalSheetId !== '') {
                rowData.sheet = parseInt(finalSheetId);
            }
            delete rowData.sheet_id;

            // Round decimal fields to max 4 decimal places (Django DecimalField constraint)
            decimalFields.forEach(field => {
                if (rowData[field] !== undefined && rowData[field] !== null) {
                    const num = parseFloat(rowData[field]);
                    rowData[field] = isNaN(num) ? "0.0000" : num.toFixed(4);
                }
            });

            // Ensure formulas is a proper object
            if (typeof rowData.formulas === 'string') {
                try { rowData.formulas = JSON.parse(rowData.formulas); } catch (e) { rowData.formulas = {}; }
            }

            try {
                if (row.id && typeof row.id === 'number' && row.id > 0) {
                    const res = await this._fetch(`/finance/${row.id}/`, {
                        method: 'PATCH',
                        body: JSON.stringify(rowData)
                    });
                    if (res && res.sheet) res.sheet_id = res.sheet;
                    results.push(res);
                } else {
                    const res = await this._fetch('/finance/', {
                        method: 'POST',
                        body: JSON.stringify(rowData)
                    });
                    if (res && res.sheet) res.sheet_id = res.sheet;
                    results.push(res);
                }
            } catch (e) {
                console.error('Batch save error for row:', row, e);
            }
        }
        return results;
    }

    async deleteDataBatch(ids) {
        for (const id of ids) {
            try {
                await this._fetch(`/finance/${id}/`, { method: 'DELETE' });
            } catch (e) {
                console.error('Delete error for id:', id, e);
            }
        }
    }

    // Aliases expected by app.js and table.js
    async insertRow(rowData) {
        const res = await this.upsertDataBatch([rowData]);
        return res[0];
    }
    
    async updateRow(id, updates, oldData = null) {
        // All DecimalField columns in KpiFinance model (max decimal_places=4)
        const decimalFields = [
            'aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil',
            'harga', 'surcharge', 'packing', 'handling', 'penjualan',
            'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv',
            'ops', 'asuransi', 'asuransi_jasindo', 'nilai_barang',
            'total_biaya', 'profit', 'idx_profit'
        ];

        const cleanedUpdates = { ...updates };
        
        // Convert sheet_id -> sheet for Django
        if (cleanedUpdates.sheet_id !== undefined) {
            cleanedUpdates.sheet = parseInt(cleanedUpdates.sheet_id);
            delete cleanedUpdates.sheet_id;
        }

        // Round decimal fields to max 4 decimal places (Django DecimalField constraint)
        decimalFields.forEach(field => {
            if (cleanedUpdates[field] !== undefined && cleanedUpdates[field] !== null) {
                const num = parseFloat(cleanedUpdates[field]);
                cleanedUpdates[field] = isNaN(num) ? "0.0000" : num.toFixed(4);
            }
        });

        // Ensure formulas is a proper object
        if (typeof cleanedUpdates.formulas === 'string') {
            try { cleanedUpdates.formulas = JSON.parse(cleanedUpdates.formulas); } catch (e) { cleanedUpdates.formulas = {}; }
        }

        const res = await this._fetch(`/finance/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(cleanedUpdates)
        });
        return res;
    }
    
    async deleteRow(id) {
        await this._fetch(`/finance/${id}/`, { method: 'DELETE' });
    }
    
    async insertRowsBulk(rows) {
        if (!rows || rows.length === 0) return [];
        console.log('insertRowsBulk called with activeSheetId:', window.activeSheetId);
        const decimalFields = [
            'aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil',
            'harga', 'surcharge', 'packing', 'handling', 'penjualan',
            'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv',
            'ops', 'asuransi', 'asuransi_jasindo', 'nilai_barang',
            'total_biaya', 'profit', 'idx_profit'
        ];
        const cleanedRows = rows.map(row => {
            const r = { ...row };
            delete r.id;
            r.tanggal_pickup = this._formatDateForDjango(row.tanggal_pickup);
            
            // Map sheet_id -> sheet for Django
            let finalSheetId = r.sheet_id;
            if (finalSheetId === undefined || finalSheetId === null || finalSheetId === 'undefined' || finalSheetId === 'null' || finalSheetId === '') {
                finalSheetId = window.activeSheetId;
            }
            if (finalSheetId !== undefined && finalSheetId !== null && finalSheetId !== 'undefined' && finalSheetId !== 'null' && finalSheetId !== '') {
                r.sheet = parseInt(finalSheetId);
            }
            delete r.sheet_id;

            // Round decimal fields to max 4 decimal places (Django DecimalField constraint)
            decimalFields.forEach(field => {
                if (r[field] !== undefined && r[field] !== null) {
                    const num = parseFloat(r[field]);
                    r[field] = isNaN(num) ? "0.0000" : num.toFixed(4);
                }
            });

            // Ensure formulas is a proper object
            if (typeof r.formulas === 'string') {
                try { r.formulas = JSON.parse(r.formulas); } catch (e) { r.formulas = {}; }
            }

            return r;
        });
        console.log('cleanedRows to send:', cleanedRows.slice(0, 2));
        const res = await this._fetch('/finance/bulk_create/', {
            method: 'POST',
            body: JSON.stringify(cleanedRows)
        });
        return res.map(row => {
            if (row.sheet) row.sheet_id = row.sheet;
            return row;
        });
    }
    
    async updateRowsBulk(bulkData) {
        // Fields that Django auto-manages or doesn't accept on PATCH
        const readOnlyFields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by'];

        // All DecimalField columns in KpiFinance model (max decimal_places=4)
        const decimalFields = [
            'aktual', 'vol', 'unit', 'kubik', 'p', 'l', 't', 'koil',
            'harga', 'surcharge', 'packing', 'handling', 'penjualan',
            'vendor_i', 'vendor_ii', 'vendor_iii', 'vendor_iv',
            'ops', 'asuransi', 'asuransi_jasindo', 'nilai_barang',
            'total_biaya', 'profit', 'idx_profit'
        ];

        const promises = bulkData.map(async (item) => {
            try {
                const raw = { ...item.updates };

                // Remove read-only fields
                readOnlyFields.forEach(f => delete raw[f]);

                // Convert sheet_id -> sheet (Django ForeignKey field name)
                if (raw.sheet_id !== undefined) {
                    raw.sheet = parseInt(raw.sheet_id);
                    delete raw.sheet_id;
                } else if (raw.sheet === undefined && window.activeSheetId) {
                    raw.sheet = parseInt(window.activeSheetId);
                }

                // Format date for Django (YYYY-MM-DD)
                if (raw.tanggal_pickup !== undefined) {
                    raw.tanggal_pickup = this._formatDateForDjango(raw.tanggal_pickup);
                }

                // Round decimal fields to max 4 decimal places (Django DecimalField constraint)
                decimalFields.forEach(field => {
                    if (raw[field] !== undefined && raw[field] !== null) {
                        const num = parseFloat(raw[field]);
                        raw[field] = isNaN(num) ? "0.0000" : num.toFixed(4);
                    }
                });

                // Ensure formulas is a proper object (not a stringified JSON)
                if (typeof raw.formulas === 'string') {
                    try {
                        raw.formulas = JSON.parse(raw.formulas);
                    } catch (e) {
                        raw.formulas = {};
                    }
                }

                // Remove internal/transient fields that Django doesn't know about
                delete raw._excelRowNum;
                delete raw._rawFormulas;
                delete raw._rawComments;

                const res = await this._fetch(`/finance/${item.id}/`, {
                    method: 'PATCH',
                    body: JSON.stringify(raw)
                });
                return { id: item.id, data: res, success: true };
            } catch (e) {
                console.error('Update bulk error for id:', item.id, e);
                return { id: item.id, error: e, success: false };
            }
        });
        return await Promise.all(promises);
    }

    async fetchYearlyData(fileId, selectStr = null) {
        return await this.fetchAllDataForFile(fileId);
    }
    
    async fetchAllPermissions() {
        return await this.fetchUserConfigs();
    }
    
    async resetPermissions(email) {
        console.log('Reset permissions handled by Admin Panel');
    }
    
    async addAuditLog(sheetId, action, cellType, changes, userEmail, userName) {
        try {
            await this._fetch('/audit/', {
                method: 'POST',
                body: JSON.stringify({
                    sheet_id: sheetId || null,
                    action: action,
                    details: typeof changes === 'string' ? changes : JSON.stringify(changes)
                })
            });
        } catch (e) {
            console.error('Audit log error', e);
        }
    }
    
    async getAuditLogs(limit=500) {
        try {
            return await this._fetch('/audit/');
        } catch(e) {
            return [];
        }
    }
    
    subscribeToChanges(callback) {
        console.log("Realtime subscription disabled for current backend");
    }

    // ==================== PIC PERMISSIONS ====================

    async fetchPermissions(email) {
        const user = await this.fetchUserConfig(email);
        return user ? { allowed_columns: user.allowed_columns, sheet_ids: user.sheet_ids } : null;
    }

    async upsertPermissions(email, allowedColumns = [], sheetIds = []) {
        throw new Error('Gunakan Django Admin Panel untuk mengelola permissions.');
    }

    async deletePermissions(email) {
        throw new Error('Gunakan Django Admin Panel.');
    }

    // ==================== STYLES ====================

    async fetchStylesForSheet(sheetId) {
        try {
            return await this._fetch(`/styles/?sheet_id=${sheetId}`);
        } catch (e) {
            return [];
        }
    }

    async saveStyle(sheetId, rowId, field, styles) {
        // DRF logic: find if exists, then PATCH, else POST
        const existingStyles = await this.fetchStylesForSheet(sheetId);
        const existing = existingStyles.find(s => s.row_id == rowId && s.field == field);

        if (existing) {
            await this._fetch(`/styles/${existing.id}/`, {
                method: 'PATCH',
                body: JSON.stringify({ styles })
            });
        } else {
            await this._fetch('/styles/', {
                method: 'POST',
                body: JSON.stringify({ sheet_id: sheetId, row_id: rowId, field, styles })
            });
        }
    }

    async deleteStyle(sheetId, rowId, field) {
        const existingStyles = await this.fetchStylesForSheet(sheetId);
        const existing = existingStyles.find(s => s.row_id == rowId && s.field == field);
        if (existing) {
            await this._fetch(`/styles/${existing.id}/`, { method: 'DELETE' });
        }
    }

    // ==================== AUDIT LOGS ====================

    async logChange(rowId, fieldName, oldValue, newValue, userEmail, userName) {
        try {
            await this._fetch('/audit/', {
                method: 'POST',
                body: JSON.stringify({
                    row_id: rowId,
                    field_name: fieldName,
                    old_value: String(oldValue),
                    new_value: String(newValue),
                    user_email: userEmail,
                    user_name: userName,
                    changed_by: userName
                })
            });
        } catch (error) {
            console.error('Failed to log change:', error.message);
        }
    }

    async fetchAuditLogs(limit = 100) {
        try {
            return await this._fetch('/audit/');
        } catch (error) {
            return [];
        }
    }

    // ==================== FORMULAS (Legacy) ====================

    async saveFormulas(rowId, formulas) {
        await this._fetch(`/finance/${rowId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ formulas })
        });
    }

    async fetchFormulas(sheetId) {
        const data = await this.fetchAllData(sheetId);
        return data.filter(r => r.formulas && Object.keys(r.formulas).length > 0)
                   .map(r => ({ row_id: r.id, formulas: r.formulas }));
    }
}

// Global instance
window.databaseManager = new DatabaseManager();
const databaseManager = window.databaseManager;
