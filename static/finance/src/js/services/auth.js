/**
 * AUTH MANAGER: Autentikasi & Otorisasi Pengguna
 * Menangani login, session, role checking, dan permission per-kolom.
 */
const getApiBaseUrl = () => {
    if (window.location.protocol === 'file:' || ['3000', '5173', '5500'].includes(window.location.port)) {
        return 'http://localhost:8000';
    }
    return '';
};

const getCsrfToken = () => {
    const match = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
    return match ? match[2] : '';
};

class AuthManager {
    constructor() {
        this.currentUser = null;
    }

    async init() {
        try {
            // Check session against Django Backend API
            const response = await fetch(getApiBaseUrl() + '/accounts/api/me/', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            if (response.ok) {
                const user = await response.json();
                return await this._setupUser({ 
                    email: user.email || user.username, 
                    id: user.id,
                    is_superuser: user.is_superuser 
                });
            }
            return null;
        } catch (err) {
            console.error('Auth init error:', err);
            return null;
        }
    }

    async logout() {
        try {
            await fetch(getApiBaseUrl() + '/accounts/api/logout/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
        } catch (e) {
            console.error('Logout request failed:', e);
        }
    }

    async login(email, password) {
        try {
            const response = await fetch(getApiBaseUrl() + '/accounts/api/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username: email, password: password })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Email atau password salah');
            }
            
            const data = await response.json();
            return await this._setupUser({ 
                email: data.user.email || data.user.username, 
                id: data.user.id,
                is_superuser: data.user.is_superuser 
            });
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('Gagal terhubung ke backend Django. Pastikan python manage.py runserver berjalan.');
            }
            throw error;
        }
    }

    async signUp(email, password, name) {
        throw new Error('Pendaftaran akun sekarang dilakukan melalui Admin Panel Django.');
    }

    async _setupUser(supabaseUser) {
        const email = supabaseUser.email;
        const metaName = supabaseUser.user_metadata?.display_name
            || supabaseUser.user_metadata?.name
            || supabaseUser.user_metadata?.full_name
            || '';

        let roleConfig = null;

        // ✅ Prioritas 1: Ambil dari database
        try {
            const dbConfig = await databaseManager.fetchUserConfig(email);
            if (dbConfig) {
                let allowedColumns = [];
                if (dbConfig.role === 'pic') {
                    try {
                        const perms = await databaseManager.fetchPermissions(email);
                        allowedColumns = perms?.allowed_columns || [];
                    } catch (e) { /* ignore */ }
                }

                roleConfig = {
                    name: dbConfig.display_name || metaName || email.split('@')[0],
                    role: dbConfig.role || 'viewer',
                    picId: dbConfig.pic_id ?? -1,
                    canEditAll: dbConfig.role === 'admin',
                    allowedColumns: dbConfig.role === 'admin' ? null : allowedColumns
                };
            }
        } catch (e) {
            console.warn('Gagal ambil config dari DB, fallback ke lokal:', e.message);
        }

        // ✅ Prioritas 2: Fallback ke USER_ROLES hardcoded
        if (!roleConfig) {
            roleConfig = {
                name: metaName || email.split('@')[0],
                role: supabaseUser.is_superuser ? 'admin' : (USER_ROLES[email]?.role || 'viewer'),
                picId: USER_ROLES[email]?.picId ?? -1,
                canEditAll: supabaseUser.is_superuser || USER_ROLES[email]?.canEditAll || false,
                allowedColumns: (supabaseUser.is_superuser || USER_ROLES[email]?.canEditAll) ? null : (USER_ROLES[email]?.allowedColumns || [])
            };
        } else if (supabaseUser.is_superuser) {
            roleConfig.role = 'admin';
            roleConfig.canEditAll = true;
            roleConfig.allowedColumns = null;
        }

        this.currentUser = {
            email: email,
            id: supabaseUser.id,
            created_at: supabaseUser.created_at,
            config: roleConfig
        };

        return this.currentUser;
    }

    isAdmin() {
        return this.currentUser?.config?.role === 'admin';
    }

    isPic() {
        return this.currentUser?.config?.role === 'pic';
    }

    isViewer() {
        if (!this.currentUser) return true;
        return !this.isAdmin() && !this.isPic();
    }

    isReadOnlyUser() {
        return !this.hasAnyEditPermission();
    }

    canEdit(row, field) {
        const config = this.currentUser?.config;
        if (!config) return false;
        if (config.canEditAll) return true;
        if (!config.allowedColumns || config.allowedColumns.length === 0) return false;
        if (field && !config.allowedColumns.includes(field)) return false;
        return true;
    }

    hasAnyEditPermission() {
        const config = this.currentUser?.config;
        if (!config) return false;
        if (config.canEditAll) return true;
        return Array.isArray(config.allowedColumns) && config.allowedColumns.length > 0;
    }

    getPicUsers() {
        return Object.entries(USER_ROLES)
            .filter(([, config]) => config.role === 'pic')
            .map(([email, config]) => ({
                email,
                name: config.name,
                picId: config.picId,
                role: config.role
            }));
    }

    async loadPicPermissions() {
        if (!this.isPic()) return;
        try {
            const perms = await databaseManager.fetchPermissions(this.currentUser.email);
            if (perms?.allowed_columns) {
                this.currentUser.config.allowedColumns = perms.allowed_columns;
                if (USER_ROLES[this.currentUser.email]) {
                    USER_ROLES[this.currentUser.email].allowedColumns = perms.allowed_columns;
                }
            } else {
                this.currentUser.config.allowedColumns = [];
                if (USER_ROLES[this.currentUser.email]) {
                    USER_ROLES[this.currentUser.email].allowedColumns = [];
                }
            }
        } catch (err) {
            console.error('Failed to load PIC permissions:', err);
            this.currentUser.config.allowedColumns = [];
        }
    }
}

// Global instance
window.authManager = new AuthManager();
const authManager = window.authManager;