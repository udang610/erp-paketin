/**
 * APP INITIALIZATION: Titik masuk utama aplikasi
 * Menggunakan tabStorage (sessionStorage + window.name) agar session terisolasi per tab.
 */
let supabaseClient;
let currentPage = 'dashboard';
let onlineUsersChannel = null;

// ==================== DOM INIT ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('=== Paketin Cargo Finance STARTED (Tab ID: ' + TAB_ID + ') ===');

    supabaseClient = supabase.createClient(
        SUPABASE_CONFIG.url,
        SUPABASE_CONFIG.anonKey,
        {
            auth: {
                storage: tabStorage,
                autoRefreshToken: true,
                persistSession: true,
                detectSessionInUrl: false
            }
        }
    );



    setupEventListeners();
    setupOnlineUsersDropdown();
    checkSession();
});

// ==================== TOAST NOTIFICATION ====================

function showToast(message, type = 'info', duration = 4000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast-item ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 200);
    }, duration);
}

// ==================== CUSTOM CONFIRM DIALOG ====================

function showConfirm({ title = 'Konfirmasi', message = '', icon = 'warning', confirmText = 'Ya', cancelText = 'Batal', confirmClass = 'primary' } = {}) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';

        const icons = {
            danger: 'fa-trash-alt',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const messageHtml = message.replace(/\n/g, '<br>');

        overlay.innerHTML = `
            <div class="confirm-card">
                <div class="confirm-header">
                    <div class="confirm-icon ${icon}"><i class="fas ${icons[icon] || icons.info}"></i></div>
                    <div class="confirm-title">${title}</div>
                </div>
                <div class="confirm-body">${messageHtml}</div>
                <div class="confirm-footer">
                    <button class="btn-confirm-cancel" id="confirmCancelBtn">${cancelText}</button>
                    <button class="btn-confirm-ok ${confirmClass}" id="confirmOkBtn">${confirmText}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const cleanup = (result) => {
            overlay.remove();
            resolve(result);
        };

        overlay.querySelector('#confirmCancelBtn').addEventListener('click', () => cleanup(false));
        overlay.querySelector('#confirmOkBtn').addEventListener('click', () => cleanup(true));
        overlay.addEventListener('click', (e) => { if (e.target === overlay) cleanup(false); });

        overlay.querySelector('#confirmOkBtn').focus();

        const escHandler = (e) => {
            if (e.key === 'Escape') { cleanup(false); document.removeEventListener('keydown', escHandler); }
        };
        document.addEventListener('keydown', escHandler);
    });
}

// ==================== INVITE LINK PROCESSING ====================

async function processAuthHash() {
    const hash = window.location.hash;
    if (!hash || !hash.startsWith('#')) return false;
    const params = new URLSearchParams(hash.substring(1));
    const type = params.get('type');
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    if (!accessToken || !refreshToken) return false;

    history.replaceState(null, null, window.location.pathname);

    if (type === 'invite' || type === 'signup') {
        window._inviteTokens = { access_token: accessToken, refresh_token: refreshToken };
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('setupSection').style.display = 'flex';
        return true;
    }

    if (type === 'recovery') {
        // Password reset flow - bisa ditambahkan nanti
        try {
            await supabaseClient.auth.setSession({ access_token: accessToken, refresh_token: refreshToken });
        } catch (e) { console.error('Recovery session error:', e); }
        return true;
    }

    try {
        await supabaseClient.auth.setSession({ access_token: accessToken, refresh_token: refreshToken });
    } catch (e) { console.error('Set session from hash error:', e); }
    return false;
}

// ==================== SETUP AKUN BARU (dari Invite Link) ====================

async function handleSetup() {
    const name = document.getElementById('setupName')?.value?.trim();
    const password = document.getElementById('setupPassword')?.value;
    const confirm = document.getElementById('setupConfirmPassword')?.value;
    const btn = document.getElementById('setupButton');
    const errEl = document.getElementById('setupError');

    const FIELD_MAP = {
        'shipper': 'Shipper',
        'consignee': 'Consignee',
        'origin': 'Asal',
        'destination': 'Tujuan',
        'status': 'Status',
        'price': 'Harga'
    };

    if (!name || name.length < 2) { errEl.textContent = 'Nama minimal 2 karakter'; errEl.classList.add('show'); return; }
    if (!password || password.length < 6) { errEl.textContent = 'Password minimal 6 karakter'; errEl.classList.add('show'); return; }
    if (password !== confirm) { errEl.textContent = 'Konfirmasi password tidak cocok'; errEl.classList.add('show'); return; }
    errEl.classList.remove('show');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="btn-text"><i class="fas fa-spinner fa-spin"></i> Mengaktivasi...</span><span class="btn-icon"></span>'; }

    try {
        // Set session dari token invite
        await supabaseClient.auth.setSession(window._inviteTokens);

        // Update password dan nama
        await supabaseClient.auth.updateUser({ password: password, data: { display_name: name } });

        // Sync ke user_config dan reset permissions
        const { data: { user } } = await supabaseClient.auth.getUser();
        if (user?.email) {
            try {
                // Upsert ke user_config
                await databaseManager.upsertUserConfig(user.email, name, 'pic');
                await databaseManager.resetPermissions(user.email);
            } catch (e) { console.warn('User config sync skipped:', e.message); }
        }

        window._inviteTokens = null;
        document.getElementById('setupSuccess').style.display = 'flex';

        setTimeout(async () => {
            try { await supabaseClient.auth.signOut(); } catch (e) { /* ignore */ }
            authManager.currentUser = null;
            document.getElementById('setupSection').style.display = 'none';
            document.getElementById('loginSection').style.display = 'flex';
            document.getElementById('setupName').value = '';
            document.getElementById('setupPassword').value = '';
            document.getElementById('setupConfirmPassword').value = '';
            errEl.classList.remove('show');
            document.getElementById('setupSuccess').style.display = 'none';
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-text">Aktivasi Akun</span><span class="btn-icon"><i class="fas fa-check"></i></span>';
        }, 2500);
    } catch (err) {
        let msg = err.message || 'Gagal mengaktifkan akun';
        if (msg.includes('expired')) msg = 'Link invite sudah kedaluwarsa. Minta link baru dari admin.';
        if (msg.includes('same password')) msg = 'Password baru tidak boleh sama dengan password sementara.';
        errEl.textContent = msg; errEl.classList.add('show');
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-text">Aktivasi Akun</span><span class="btn-icon"><i class="fas fa-check"></i></span>';
    }
}

async function handleSignup() {
    const name = document.getElementById('signupName')?.value?.trim();
    const email = document.getElementById('signupEmail')?.value?.trim();
    const password = document.getElementById('signupPassword')?.value;
    const confirm = document.getElementById('signupConfirm')?.value;
    const btn = document.getElementById('signupButton');
    const errEl = document.getElementById('signupError');

    if (!name || name.length < 2) { errEl.textContent = 'Nama minimal 2 karakter'; errEl.classList.add('show'); return; }
    if (!email || !email.includes('@')) { errEl.textContent = 'Email tidak valid'; errEl.classList.add('show'); return; }
    if (!password || password.length < 6) { errEl.textContent = 'Password minimal 6 karakter'; errEl.classList.add('show'); return; }
    if (password !== confirm) { errEl.textContent = 'Konfirmasi password tidak cocok'; errEl.classList.add('show'); return; }

    errEl.classList.remove('show');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mendaftar...'; }

    try {
        await authManager.signUp(email, password, name);
        try { await databaseManager.upsertUserConfig(email, name, 'viewer'); } catch (e) { }

        document.getElementById('signupSuccess').style.display = 'flex';
        setTimeout(() => {
            document.getElementById('signupSection').style.display = 'none';
            document.getElementById('loginSection').style.display = 'flex';
            document.getElementById('signupSuccess').style.display = 'none';
            if (btn) { btn.disabled = false; btn.innerHTML = 'Daftar Sekarang'; }
        }, 3000);
    } catch (err) {
        errEl.textContent = err.message || 'Gagal mendaftar';
        errEl.classList.add('show');
        if (btn) { btn.disabled = false; btn.innerHTML = 'Daftar Sekarang'; }
    }
}

// ==================== EVENT LISTENERS ====================

function setupEventListeners() {
    const loginBtn = document.getElementById('loginButton');
    if (loginBtn) loginBtn.addEventListener('click', handleLogin);

    const toggleBtn = document.getElementById('passwordToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const passInput = document.getElementById('password');
            const icon = toggleBtn.querySelector('i');
            if (passInput.type === 'password') {
                passInput.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                passInput.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    }

    const setupPassToggle = document.getElementById('setupPasswordToggle');
    if (setupPassToggle) {
        setupPassToggle.addEventListener('click', () => {
            const input = document.getElementById('setupPassword');
            const icon = setupPassToggle.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    }

    const setupConfirmToggle = document.getElementById('setupConfirmToggle');
    if (setupConfirmToggle) {
        setupConfirmToggle.addEventListener('click', () => {
            const input = document.getElementById('setupConfirmPassword');
            const icon = setupConfirmToggle.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    }

    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const setupSec = document.getElementById('setupSection');
            if (setupSec && setupSec.style.display !== 'none') { handleSetup(); return; }
            const loginSec = document.getElementById('loginSection');
            if (loginSec && loginSec.style.display !== 'none') handleLogin();
        }
    });

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'f' || e.key === 'F')) {
            e.preventDefault();
            if (currentPage === 'recap') {
                const recapSearch = document.getElementById('recapSearch');
                if (recapSearch) {
                    recapSearch.focus();
                    recapSearch.select();
                }
            } else if (currentPage === 'table') {
                const findBar = document.getElementById('findBar');
                const findInput = document.getElementById('findInput');
                if (findBar && findInput) {
                    findBar.style.display = 'flex';
                    findInput.focus();
                    findInput.select();
                }
            }
        }
    });
}

// ==================== YEARLY FILE PANEL ====================

function toggleFilePanel() {
    console.log('[toggleFilePanel] called');
    const overlay = document.getElementById('filePanelOverlay');
    if (!overlay) { console.log('[toggleFilePanel] overlay not found'); return; }
    const isVisible = overlay.style.display === 'flex';
    overlay.style.display = isVisible ? 'none' : 'flex';
    console.log('[toggleFilePanel] toggled to:', overlay.style.display);

    if (!isVisible && window.yearlyFileManager) {
        window.yearlyFileManager.loadFiles();
    }
}
window.toggleFilePanel = toggleFilePanel;


// ==================== ONLINE USERS ====================

function setupOnlineUsersDropdown() {
    const navOnline = document.getElementById('navOnlineUsers');
    if (!navOnline) return;

    navOnline.addEventListener('click', (e) => {
        e.stopPropagation();
        const dropdown = document.getElementById('onlineDropdown');
        if (dropdown) {
            const isVisible = dropdown.style.display === 'block';
            dropdown.style.display = isVisible ? 'none' : 'block';
        }
    });

    document.addEventListener('click', () => {
        const dropdown = document.getElementById('onlineDropdown');
        if (dropdown) dropdown.style.display = 'none';
    });
}

async function setupOnlineUsersPresence() {
    if (!authManager.currentUser) return;

    const user = authManager.currentUser;
    const email = user.email;
    const config = user.config;
    const name = config?.name || email.split('@')[0];
    const initials = name.split(' ').map(n => n[0]).filter(c => c).join('').substring(0, 2).toUpperCase() || '??';
    const tabLabel = TAB_ID.replace('pcf_tab_', '').substring(0, 4).toUpperCase();

    const userData = {
        email: email,
        name: name + ' [' + tabLabel + ']',
        role: config?.role?.toUpperCase() || 'USER',
        initials: initials,
        online_at: new Date().toISOString(),
        status: 'active' // 'active' or 'away'
    };

    // Store reference for lifecycle handlers
    window._presenceUserData = userData;

    if (onlineUsersChannel) {
        try { onlineUsersChannel.untrack(); } catch (e) { }
        try { await supabaseClient.removeChannel(onlineUsersChannel); } catch (e) { }
        onlineUsersChannel = null;
    }

    const listEl = document.getElementById('onlineUsersList');
    if (listEl) listEl.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">Menghubungkan...</span>';

    onlineUsersChannel = supabaseClient.channel('online-users', {
        config: { presence: { key: TAB_ID } }
    });

    onlineUsersChannel
        .on('presence', { event: 'sync' }, () => {
            const state = onlineUsersChannel.presenceState();
            const allEntries = Object.values(state).map(u => u[0]);

            // Deduplikasi per email: ambil entry terbaru (paling recent online_at) per email
            const emailMap = new Map();
            allEntries.forEach(entry => {
                const existing = emailMap.get(entry.email);
                if (!existing || new Date(entry.online_at) > new Date(existing.online_at)) {
                    emailMap.set(entry.email, entry);
                }
            });
            const uniqueUsers = Array.from(emailMap.values());

            updateOnlineUsersUI(uniqueUsers.length > 0 ? uniqueUsers : [userData]);
        })
        .subscribe(async (status) => {
            const dots = document.querySelectorAll('.online-status-dot');
            if (status === 'SUBSCRIBED') {
                dots.forEach(dot => dot.style.backgroundColor = '#22c55e');
                await onlineUsersChannel.track(userData);
                updateOnlineUsersUI([userData]);
            } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
                dots.forEach(dot => dot.style.backgroundColor = '#ef4444');
            } else {
                dots.forEach(dot => dot.style.backgroundColor = '#f59e0b');
            }
        });

    // === LIFECYCLE: Away detection saat tab tidak terlihat atau IDLE ===
    if (!window._presenceVisibilityBound) {
        window._presenceVisibilityBound = true;
        let idleTimer = null;

        const setPresenceStatus = async (newStatus) => {
            if (!onlineUsersChannel || !window._presenceUserData) return;
            if (window._presenceUserData.status === newStatus) return; // Prevent spam

            window._presenceUserData.status = newStatus;
            if (newStatus === 'active') {
                window._presenceUserData.online_at = new Date().toISOString();
            }
            try {
                await onlineUsersChannel.track(window._presenceUserData);
            } catch (e) {
                console.warn('[Presence] track error:', e.message);
            }
        };

        const resetIdleTimer = () => {
            if (document.hidden) return; // Kalau tab ditutup, biarkan away

            setPresenceStatus('active');

            clearTimeout(idleTimer);
            // Jika tidak ada interaksi selama 60 detik, otomatis Away
            idleTimer = setTimeout(() => {
                setPresenceStatus('away');
            }, 60000);
        };

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                clearTimeout(idleTimer);
                setPresenceStatus('away');
            } else {
                resetIdleTimer();
            }
        });

        // Deteksi aktivitas user secara instan
        const interactionEvents = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
        interactionEvents.forEach(evt => {
            document.addEventListener(evt, resetIdleTimer, { passive: true });
        });

        // Inisialisasi timer pertama kali
        resetIdleTimer();

        // === LIFECYCLE: Cleanup saat tab ditutup paksa (tanpa logout) === ===
        window.addEventListener('beforeunload', () => {
            if (onlineUsersChannel) {
                try { onlineUsersChannel.untrack(); } catch (e) { }
            }
        });

        // pagehide lebih reliable di mobile browser
        window.addEventListener('pagehide', () => {
            if (onlineUsersChannel) {
                try { onlineUsersChannel.untrack(); } catch (e) { }
            }
        });
    }
}

function updateOnlineUsersUI(users) {
    const countEl = document.getElementById('onlineCount');
    const listEl = document.getElementById('onlineUsersList');

    // Hitung hanya user yang status-nya 'active' untuk badge count
    const activeUsers = users.filter(u => u.status !== 'away');
    if (countEl) countEl.textContent = activeUsers.length || users.length;

    if (listEl) {
        if (users.length === 0) {
            listEl.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">Tidak ada pengguna lain</span>';
        } else {
            listEl.innerHTML = users.map(u => {
                const isAway = u.status === 'away';
                const statusDot = isAway
                    ? '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-left:6px;" title="Away"></span>'
                    : '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;margin-left:6px;" title="Active"></span>';
                const nameStyle = isAway ? 'opacity:0.6;' : '';
                return `
                <div class="online-user-item">
                    <div class="user-avatar">${u.initials || '?'}</div>
                    <div>
                        <div class="user-name" style="${nameStyle}">${u.name || u.email} ${statusDot} <span class="user-role-badge">${u.role || 'USER'}</span></div>
                        <div class="user-email">${u.email}</div>
                    </div>
                </div>
            `}).join('');
        }
    }
}

function cleanupOnlineUsers() {
    if (onlineUsersChannel) {
        try { onlineUsersChannel.untrack(); } catch (e) { }
        supabaseClient.removeChannel(onlineUsersChannel);
        onlineUsersChannel = null;
    }
    window._presenceUserData = null;
    const countEl = document.getElementById('onlineCount');
    if (countEl) countEl.textContent = '0';
    const listEl = document.getElementById('onlineUsersList');
    if (listEl) listEl.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">Offline</span>';
}

// ==================== SESSION ====================

async function checkSession() {
    try {
        const isInvite = await processAuthHash();
        if (!isInvite) {
            const user = await authManager.init();
            if (user) await handleSuccessfulLogin(user);
        }
    } catch (err) {
        console.error('Session check error:', err);
    }
}

async function handleLogin() {
    const email = document.getElementById('email')?.value?.trim();
    const password = document.getElementById('password')?.value?.trim();
    const errorEl = document.getElementById('loginError');
    const loginBtn = document.getElementById('loginButton');

    if (!email || !password) {
        if (errorEl) { errorEl.textContent = 'Mohon isi email dan password'; errorEl.style.display = 'block'; }
        return;
    }

    if (errorEl) errorEl.style.display = 'none';
    if (loginBtn) { loginBtn.classList.add('loading'); loginBtn.disabled = true; }

    try {
        await authManager.login(email, password);
        localStorage.setItem('pcf-last-page', 'dashboard');
        await handleSuccessfulLogin(authManager.currentUser);
    } catch (error) {
        console.error('Login error:', error);
        if (errorEl) {
            errorEl.textContent = error.message || 'Login gagal, periksa email dan password';
            errorEl.style.display = 'block';
        }
    } finally {
        if (loginBtn) { loginBtn.classList.remove('loading'); loginBtn.disabled = false; }
    }
}

/**
 * Sinkronisasi USER_ROLES dari database.
 * - Memastikan user hardcoded ada di DB (insert saja, tidak overwrite)
 * - Rebuild USER_ROLES dari data DB (jadi DB = source of truth)
 * - User yang dihapus dari DB otomatis hilang dari USER_ROLES
 */
async function syncUserRolesFromDatabase() {
    try {
        const dbUsers = await databaseManager.fetchUserConfigs();
        const dbEmails = new Set(dbUsers.map(u => u.email));

        // Step 1: Pastikan semua user hardcoded ada di DB (insert only, JANGAN overwrite)
        for (const [email, config] of Object.entries(USER_ROLES)) {
            if (!dbEmails.has(email)) {
                try {
                    await databaseManager.upsertUserConfig(email, config.name, config.role);
                    console.log('✅ Hardcoded user synced to DB:', email);
                } catch (e) {
                    console.warn('Gagal sync user ke DB (mungkin RLS):', email, e.message);
                }
            }
        }

        // Force sync current user if missing in DB
        const current = authManager.currentUser;
        if (current && !dbEmails.has(current.email) && current.config?.role === 'admin') {
            try {
                await databaseManager.upsertUserConfig(current.email, current.config.name, 'admin');
                console.log('🚀 Force synced current admin to profiles');
            } catch (e) { /* ignore */ }
        }
    } catch (err) {
        console.error('syncUserRolesFromDatabase error:', err);
    }

    // Step 2: Re-fetch setelah insert user baru
    const freshDbUsers = await databaseManager.fetchUserConfigs();

    // Step 3: Load permissions untuk PIC
    let permsMap = {};
    try {
        const allPerms = await databaseManager.fetchAllPermissions();
        allPerms.forEach(p => { permsMap[p.pic_email] = p.allowed_columns || []; });
    } catch (e) {
        console.warn('Gagal load permissions:', e.message);
    }

    // Step 4: Rebuild USER_ROLES dari database
    const newRoles = {};
    freshDbUsers.forEach((u, idx) => {
        const isSuper = u.is_superuser === true || u.username === 'admin';
        newRoles[u.email] = {
            name: u.name || u.email.split('@')[0],
            picId: idx,
            role: isSuper ? 'admin' : (u.role || 'viewer'),
            canEditAll: isSuper || u.role === 'admin',
            allowedColumns: (isSuper || u.role === 'admin') ? null : (permsMap[u.email] || [])
        };
    });

    // Step 5: Replace isi USER_ROLES (hapus yang lama, masukkan yang baru dari DB)
    Object.keys(USER_ROLES).forEach(key => delete USER_ROLES[key]);
    Object.assign(USER_ROLES, newRoles);

    console.log('✅ USER_ROLES disinkronkan dari DB:', Object.keys(USER_ROLES).length, 'user');
}

async function handleSuccessfulLogin(user) {
    console.log('✅ Login successful:', user.email, '| Tab:', TAB_ID);

    // ✅ Sync USER_ROLES dari database DULU sebelum apa pun
    await syncUserRolesFromDatabase();

    // Re-apply config dari USER_ROLES yang sudah di-update dari DB
    if (USER_ROLES[user.email]) {
        authManager.currentUser.config = USER_ROLES[user.email];
    }

    if (authManager.isPic()) {
        await authManager.loadPicPermissions();
        console.log('📋 PIC permissions loaded:', authManager.currentUser.config.allowedColumns.length, 'kolom');
    }

    // Write login audit log
    try {
        let os = "Unknown OS";
        if (navigator.userAgent.indexOf("Win") != -1) os = "Windows";
        else if (navigator.userAgent.indexOf("Mac") != -1) os = "MacOS";
        else if (navigator.userAgent.indexOf("X11") != -1) os = "UNIX";
        else if (navigator.userAgent.indexOf("Linux") != -1) os = "Linux";

        let browser = "Browser";
        if (navigator.userAgent.indexOf("Chrome") != -1) browser = "Chrome";
        else if (navigator.userAgent.indexOf("Safari") != -1) browser = "Safari";
        else if (navigator.userAgent.indexOf("Firefox") != -1) browser = "Firefox";
        else if (navigator.userAgent.indexOf("MSIE") != -1 || !!document.documentMode == true) browser = "IE";

        const loginDetail = `Login via ${browser} (${os})`;
        const displayName = authManager.currentUser?.config?.name || user.email.split('@')[0];

        await databaseManager.addAuditLog(null, 'login', 'offline', loginDetail, user.email, displayName);
        console.log('📝 Login audit log written successfully');
    } catch (e) {
        console.warn('Failed to write login audit log:', e);
    }

    const loginSec = document.getElementById('loginSection');
    if (loginSec) loginSec.style.display = 'none';
    const nav = document.getElementById('navbar');
    if (nav) nav.style.display = 'flex';
    const dashContainer = document.getElementById('dashboardContainer');
    if (dashContainer) dashContainer.style.display = 'block';

    const config = authManager.currentUser?.config;
    const name = config?.name || user.email;
    const role = config?.role ? config.role.charAt(0).toUpperCase() + config.role.slice(1) : '';

    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
        // Prefer metadata full name over DB name if DB name is just the email prefix
        let displayName = config?.name || user.email.split('@')[0];
        const emailPrefix = user.email.split('@')[0];

        if (displayName === emailPrefix && user.user_metadata) {
            displayName = user.user_metadata.full_name || user.user_metadata.name || user.user_metadata.display_name || emailPrefix;
        }

        userInfo.innerHTML = `${displayName} <span class="nav-role-label">${role}</span>`;
    }

    const navAdmin = document.getElementById('navAdmin');
    if (navAdmin) {
        navAdmin.style.display = 'none';
    }

    const navMonitoring = document.getElementById('navMonitoring');
    if (navMonitoring) {
        navMonitoring.style.display = authManager.isAdmin() ? 'inline-flex' : 'none';
    }

    let targetPage = localStorage.getItem('pcf-last-page') || 'table';
    // Dashboard page was removed, so if it's dashboard, fallback to table
    if (targetPage === 'dashboard' || (targetPage === 'admin' && !authManager.isAdmin())) {
        targetPage = 'table';
    }
    switchPage(targetPage);
    
    // Auto-show file panel on first load
    const overlay = document.getElementById('filePanelOverlay');
    if (overlay && overlay.style.display !== 'flex') {
        overlay.style.display = 'flex';
        if (window.yearlyFileManager) window.yearlyFileManager.loadFiles();
    }

    // Initialize New Managers v2.0
    if (typeof SpreadsheetToolbar !== 'undefined') {
        window.toolbarManager = new SpreadsheetToolbar(tableManager);
        window.spreadsheetToolbar = window.toolbarManager; // alias for keyboard shortcuts
        window.toolbarManager.init();
    }
    if (typeof RecapManager !== 'undefined') {
        window.recapManager = new RecapManager(tableManager);
        window.recapManager.init();
    }

    if (typeof YearlyFileManager !== 'undefined') {
        window.yearlyFileManager = new YearlyFileManager();
        await window.yearlyFileManager.init();
    }

    await sheetsManager.init();
    await loadAllData();

    if (window.location.hash) {
        history.replaceState(null, null, window.location.pathname);
    }

    setupRealtimeSubscription();

    // Initialize Presence (Remote Cursor) after auth is ready
    if (window.tableManager) {
        window.tableManager.initPresence();
    }

    setTimeout(() => {
        setupOnlineUsersPresence();
    }, 800);
}

function setupRealtimeSubscription() {
    databaseManager.subscribeToChanges((payload) => {
        const eventType = payload.eventType;
        if (eventType === 'UPDATE') {
            const newRecord = payload.new;
            if (newRecord?.id) {
                tableManager._syncLocalRow(newRecord);
                Object.keys(newRecord).forEach(field => {
                    if (field === 'id') return;
                    if (['created_at', 'created_by', 'updated_by', 'updated_at'].includes(field)) return;
                    tableManager.updateRemoteCell(newRecord.id, field, newRecord[field], newRecord.updated_by);
                });
                if (currentPage === 'dashboard') {
                    _dashboardDataLoadedForFile = null;
                    loadAllData();
                }
                updateLastUpdatedStatus();
            }
        } else if (eventType === 'INSERT') {
            const newRecord = payload.new;
            if (newRecord) {
                tableManager.addRemoteRow(newRecord);
                updateLastUpdatedStatus();
                if (currentPage === 'dashboard' || typeof chartsManager !== 'undefined') {
                    _dashboardDataLoadedForFile = null;
                    loadAllData();
                }
            }
        } else if (eventType === 'DELETE') {
            const oldRecord = payload.old;
            if (oldRecord?.id) {
                tableManager.currentData = tableManager.currentData.filter(r => r.id != oldRecord.id);
                tableManager.originalData = tableManager.originalData.filter(r => r.id != oldRecord.id);
                tableManager.renderTable(tableManager.currentData);
            }
        }
    });
}

function switchPage(pageName) {
    if (!pageName) return;
    currentPage = pageName;
    localStorage.setItem('pcf-last-page', pageName);

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.page === pageName);
    });

    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById('page-' + pageName);
    if (targetPage) targetPage.classList.add('active');

    if (pageName !== 'table' && typeof tableManager !== 'undefined') {
        tableManager.closeFind();
        tableManager.clearSelection();
        tableManager.cancelCellEdit();

        // Hide file panel if navigating to dashboard/admin
        const overlay = document.getElementById('filePanelOverlay');
        if (overlay && overlay.style.display === 'flex') {
            overlay.style.display = 'none';
        }
    }



    if (pageName === 'admin') {
        renderAdminPanel();
    }

    if (pageName === 'audit') {
        renderAuditLogsPage();
    }

    if (pageName === 'monitoring') {
        if (typeof monitoringManager !== 'undefined') {
            monitoringManager.init();
        }
    }

    if (pageName === 'recap') {
        if (typeof recapPageManager !== 'undefined') {
            recapPageManager.init();
        }
    }

    const banner = document.getElementById('readonlyBanner');
    if (banner) {
        banner.style.display = (pageName === 'table' && !authManager.hasAnyEditPermission()) ? 'flex' : 'none';
    }

    if (pageName === 'table' && !sessionStorage.getItem('pcf-file-selected')) {
        const overlay = document.getElementById('filePanelOverlay');
        if (overlay && overlay.style.display !== 'flex') {
            toggleFilePanel();
        }
    }

    // Auto focus TANGGAL, 1 every time user enters the table worksheet
    if (pageName === 'table' && typeof tableManager !== 'undefined' && typeof tableManager.resetSheetView === 'function') {
        setTimeout(() => {
            if (tableManager.currentData && tableManager.currentData.length > 0) {
                tableManager.resetSheetView();
            }
        }, 300);
    }
    if (pageName === 'dashboard') {
        // Always fetch fresh yearly data when switching to dashboard
        const fileId = window.yearlyFileManager ? window.yearlyFileManager.activeFileId : null;
        if (fileId && typeof chartsManager !== 'undefined') {
            databaseManager.fetchYearlyData(fileId, 'id, nama, tanggal_pickup, awb, awb_sistem, pengirim, service, penjualan, profit, total_biaya, sheet_id, formulas').then(yearlyData => {
                console.log('[switchPage→dashboard] yearlyData rows:', yearlyData.length);
                chartsManager.renderDashboardStats(yearlyData);
            }).catch(err => console.error('Dashboard load error:', err));
        }
    }
}

function updateLastUpdatedStatus() {
    const lastUpdated = document.getElementById('lastUpdated');
    if (lastUpdated) {
        lastUpdated.innerHTML = `<span class="realtime-indicator"></span> Last updated: ${new Date().toLocaleTimeString('id-ID')}`;
    }
}

async function handleLogout() {
    console.log('🔒 Logging out... Tab:', TAB_ID);

    sessionStorage.removeItem('pcf-file-selected'); // Clear file selection on logout

    try {
        if (typeof tableManager !== 'undefined' && tableManager) {
            if (tableManager.editingCell) tableManager.saveCellEdit();
            if (typeof tableManager.flushSaveQueue === 'function') {
                await tableManager.flushSaveQueue();
            }
        }
    } catch (e) {
        console.warn('Warning during table flush on logout:', e);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    try {
        if (typeof cleanupOnlineUsers === 'function') cleanupOnlineUsers();
    } catch (e) {}
    
    _dataLoaded = false;

    try {
        // Use authManager if available, otherwise fetch directly to the correct dynamic API url
        if (typeof authManager !== 'undefined' && authManager && typeof authManager.logout === 'function') {
            await authManager.logout();
            authManager.currentUser = null;
        } else {
            const baseUrl = (typeof getApiBaseUrl === 'function') ? getApiBaseUrl() : 'http://localhost:8001';
            await fetch(baseUrl + '/accounts/api/logout/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'omit'
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    }

    document.getElementById('navbar').style.display = 'none';
    document.getElementById('dashboardContainer').style.display = 'none';
    document.getElementById('loginSection').style.display = 'flex';
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
    const errorEl = document.getElementById('loginError');
    if (errorEl) errorEl.classList.remove('show');

    if (typeof chartsManager !== 'undefined') chartsManager.destroyCharts();
}

// ==================== EXPORT ====================

function applyEnhancementsToWorksheet(worksheet, dataForExcel, dataRows) {
    if (!dataForExcel || dataForExcel.length === 0) return;

    const headers = Object.keys(dataForExcel[0]);

    function getColName(index) {
        let name = '';
        while (index >= 0) {
            name = String.fromCharCode(65 + (index % 26)) + name;
            index = Math.floor(index / 26) - 1;
        }
        return name;
    }

    const fieldToHeader = {
        'tanggal_pickup': 'TANGGAL', 'nama': 'IP PERUSAHAAN', 'awb': 'AWB', 'awb_sistem': 'AWB SISTEM',
        'pengirim': 'CUSTOMER', 'sales': 'SALES', 'penerima': 'PENERIMA', 'service': 'SERVICE',
        'via': 'VIA', 'aktual': 'AKTUAL', 'vol': 'VOL', 'unit': 'UNIT', 'kubik': 'KUBIK',
        'p': 'P', 'l': 'L', 't': 'T', 'koil': 'KOLI', 'harga': 'HARGA PERKILO',
        'surcharge': 'SURCHARGE', 'packing': 'PACKING', 'handling': 'HANDLING',
        'penjualan': 'PENJUALAN', 'asal_pickup': 'ASAL PICK UP', 'jenis_barang': 'JENIS BARANG',
        'tujuan': 'TUJUAN', 'nama_vendor': 'NAMA VENDOR I', 'nama_vendor_ii': 'NAMA VENDOR II',
        'nama_vendor_iii': 'NAMA VENDOR III', 'nama_vendor_iv': 'NAMA VENDOR IV',
        'vendor_i': 'HARGA VENDOR I', 'vendor_ii': 'HARGA VENDOR II', 'vendor_iii': 'HARGA VENDOR III', 'vendor_iv': 'HARGA VENDOR IV',
        'ops': 'OPS', 'total_biaya': 'TOTAL BIAYA', 'profit': 'PROFIT', 'idx_profit': 'IDX PROFIT',
        'asuransi': 'PENJUALAN ASURANSI', 'nilai_barang': 'NILAI BARANG', 'asuransi_jasindo': 'MODAL ASURANSI'
    };

    const currencyHeaders = new Set([
        'PENJUALAN', 'TOTAL BIAYA', 'PROFIT', 'PENJUALAN ASURANSI', 'MODAL ASURANSI',
        'NILAI BARANG', 'HARGA VENDOR I', 'HARGA VENDOR II', 'HARGA VENDOR III', 'HARGA VENDOR IV',
        'OPS', 'HARGA PERKILO', 'SURCHARGE', 'PACKING', 'HANDLING'
    ]);

    const currencyCols = new Set();
    const colMap = {};
    headers.forEach((h, i) => {
        const colName = getColName(i);
        colMap[h] = colName;
        if (currencyHeaders.has(h)) {
            currencyCols.add(colName);
        }
    });

    // 1. Inject Formulas and Comments
    dataRows.forEach((row, rIdx) => {
        const excelRowIndex = rIdx + 4; // origin A3 implies header is 3, data starts at 4

        // A. Inject Auto-Calc Formulas first (can be overridden by manual formulas)
        const setFormula = (header, formulaStr) => {
            const col = colMap[header];
            if (!col) return;
            const cellAddress = col + excelRowIndex;
            if (!worksheet[cellAddress]) worksheet[cellAddress] = { v: 0 };
            worksheet[cellAddress].t = 'n';
            worksheet[cellAddress].f = formulaStr;
            if (typeof worksheet[cellAddress].v !== 'number') {
                worksheet[cellAddress].v = parseFloat(worksheet[cellAddress].v) || 0;
            }
            delete worksheet[cellAddress].w;
        };

        const fieldToHeaderLocal = {
            'kubik': 'KUBIK', 'penjualan': 'PENJUALAN', 'total_biaya': 'TOTAL BIAYA',
            'profit': 'PROFIT', 'idx_profit': 'IDX PROFIT', 'asuransi': 'ASURANSI', 'asuransi_jasindo': 'ASURANSI JASINDO'
        };

        const hasManualFormula = (field) => {
            if (!row || !row.formulas) return false;
            let fObj = row.formulas;
            if (typeof fObj === 'string') {
                try { fObj = JSON.parse(fObj); } catch (e) { return false; }
            }
            return fObj && fObj[field] !== undefined;
        };

        // KUBIK: (P * L * T) / 1000000
        if (!hasManualFormula('kubik') && colMap['P'] && colMap['L'] && colMap['T']) {
            setFormula('KUBIK', `(${colMap['P']}${excelRowIndex}*${colMap['L']}${excelRowIndex}*${colMap['T']}${excelRowIndex})/1000000`);
        }

        // PENJUALAN
        if (!hasManualFormula('penjualan') && colMap['AKTUAL'] && colMap['VOL'] && colMap['HARGA PERKILO']) {
            const extras = [colMap['SURCHARGE'], colMap['PACKING'], colMap['HANDLING']].filter(Boolean).map(c => `${c}${excelRowIndex}`).join('+');
            setFormula('PENJUALAN', `(MAX(${colMap['AKTUAL']}${excelRowIndex},${colMap['VOL']}${excelRowIndex})*${colMap['HARGA PERKILO']}${excelRowIndex})${extras ? '+' + extras : ''}`);
        }

        // TOTAL BIAYA
        if (!hasManualFormula('total_biaya') && colMap['HARGA VENDOR I']) {
            const vendors = ['HARGA VENDOR I', 'HARGA VENDOR II', 'HARGA VENDOR III', 'HARGA VENDOR IV', 'OPS'].map(h => colMap[h]).filter(Boolean).map(c => `${c}${excelRowIndex}`).join('+');
            setFormula('TOTAL BIAYA', vendors);
        }

        // ASURANSI
        if (!hasManualFormula('asuransi') && colMap['NILAI BARANG']) {
            setFormula('PENJUALAN ASURANSI', `${colMap['NILAI BARANG']}${excelRowIndex}*0.002`);
        }

        if (!hasManualFormula('asuransi_jasindo') && colMap['NILAI BARANG']) {
            setFormula('MODAL ASURANSI', `${colMap['NILAI BARANG']}${excelRowIndex}*0.001`);
        }

        // PROFIT
        if (!hasManualFormula('profit') && colMap['PENJUALAN'] && colMap['TOTAL BIAYA']) {
            // Profit formula: PENJUALAN - TOTAL BIAYA
            setFormula('PROFIT', `${colMap['PENJUALAN']}${excelRowIndex}-${colMap['TOTAL BIAYA']}${excelRowIndex}`);
        }

        // IDX PROFIT
        if (!hasManualFormula('idx_profit') && colMap['PROFIT'] && colMap['PENJUALAN']) {
            setFormula('IDX PROFIT', `IFERROR(${colMap['PROFIT']}${excelRowIndex}/${colMap['PENJUALAN']}${excelRowIndex}, 0)`);
            const idxCell = colMap['IDX PROFIT'] + excelRowIndex;
            if (worksheet[idxCell]) worksheet[idxCell].z = '0.0%';
        }

        // B. Inject Manual Formulas and Comments
        if (!row || !row.formulas) return;
        let fObj = row.formulas;
        if (typeof fObj === 'string') {
            try { fObj = JSON.parse(fObj); } catch (e) { return; }
        }
        if (typeof fObj !== 'object') return;

        Object.entries(fObj).forEach(([field, formulaStr]) => {
            if (typeof formulaStr === 'string' && formulaStr.startsWith('=')) {
                const headerName = fieldToHeader[field];
                if (!headerName) return;

                const cIdx = headers.indexOf(headerName);
                if (cIdx === -1) return;

                const colName = getColName(cIdx);
                const excelRowIndex = rIdx + 4; // origin A3 implies header is 3, data starts at 4
                const cellAddress = colName + excelRowIndex;

                // Shift row references by +3 for Excel AND shift column by +1 (because Excel has 'NO' at col A)
                let shiftedFormula = formulaStr.replace(/([A-Z]+)(\d+)/g, (match, col, rowNum) => {
                    let cIdx = 0;
                    for (let i = 0; i < col.length; i++) {
                        cIdx = cIdx * 26 + (col.charCodeAt(i) - 64);
                    }
                    cIdx += 1;
                    let newCol = '';
                    let tempIdx = cIdx;
                    while (tempIdx > 0) {
                        let mod = (tempIdx - 1) % 26;
                        newCol = String.fromCharCode(65 + mod) + newCol;
                        tempIdx = Math.floor((tempIdx - mod) / 26);
                    }
                    return newCol + (parseInt(rowNum) + 3);
                });

                // Prevent circular references in Excel by capping the range to end BEFORE the subtotal row
                shiftedFormula = shiftedFormula.replace(/([A-Z]+)(\d+):([A-Z]+)(\d+)/g, (match, c1, r1, c2, r2) => {
                    let startRow = parseInt(r1);
                    let endRow = parseInt(r2);
                    if (startRow <= excelRowIndex && endRow >= excelRowIndex) {
                        endRow = Math.max(startRow, excelRowIndex - 1);
                    }
                    return `${c1}${startRow}:${c2}${endRow}`;
                });

                if (!worksheet[cellAddress]) worksheet[cellAddress] = { v: 0 };
                worksheet[cellAddress].t = 'n';
                worksheet[cellAddress].f = shiftedFormula.substring(1);
                if (typeof worksheet[cellAddress].v !== 'number') {
                    worksheet[cellAddress].v = parseFloat(worksheet[cellAddress].v) || 0;
                }
                delete worksheet[cellAddress].w;
            }
        });

        // Inject comments
        if (fObj.__comments) {
            Object.entries(fObj.__comments).forEach(([field, commentStr]) => {
                const headerName = fieldToHeader[field];
                if (!headerName) return;

                const col = colMap[headerName];
                if (!col) return;

                const cellAddress = col + excelRowIndex;
                if (!worksheet[cellAddress]) worksheet[cellAddress] = { v: '' };
                if (!worksheet[cellAddress].c) worksheet[cellAddress].c = [];
                worksheet[cellAddress].c.push({ a: 'User', t: commentStr, hidden: true });
            });
        }
    });

    // 2. Format Currency and Dates
    for (const cell in worksheet) {
        if (cell[0] === '!') continue;
        const col = cell.replace(/\d+$/, '');
        const rowMatch = cell.match(/\d+$/);
        const rowNum = rowMatch ? parseInt(rowMatch[0]) : 0;

        // Only format data rows (starting from row 4)
        if (rowNum >= 4) {
            const cellObj = worksheet[cell];
            if (!cellObj) continue;

            if (currencyCols.has(col) && cellObj.t === 'n') {
                cellObj.z = '"Rp" #,##0';
            } else if (col === colMap['TANGGAL']) {
                if (cellObj.t === 'n' || cellObj.t === 'd' || cellObj.v instanceof Date) {
                    cellObj.z = 'dd/mm/yyyy';
                }
            }
        }
    }
}

function exportToExcel() {
    if (!tableManager.currentData?.length) {
        showToast('Tidak ada data untuk diexport', 'warning');
        return;
    }

    try {
        const formatDateExcel = (dateStr) => {
            if (!dateStr) return '';
            const d = window.formulaEngine ? window.formulaEngine._parseDate(dateStr) : new Date(dateStr);
            if (!d || isNaN(d.getTime())) return dateStr;
            const dd = String(d.getDate()).padStart(2, '0');
            const mm = String(d.getMonth() + 1).padStart(2, '0');
            const yyyy = d.getFullYear();
            return `${dd}/${mm}/${yyyy}`;
        };

        const dataForExcel = tableManager.currentData.map((row, index) => {
            const penjualan = !isNaN(parseFloat(row.penjualan)) ? parseFloat(row.penjualan) : (window.formulaEngine.compute('penjualan', row) || 0);
            const totalBiaya = !isNaN(parseFloat(row.total_biaya)) ? parseFloat(row.total_biaya) : (window.formulaEngine.compute('total_biaya', row) || 0);
            const profit = !isNaN(parseFloat(row.profit)) ? parseFloat(row.profit) : (window.formulaEngine.compute('profit', row) || 0);
            const margin = !isNaN(parseFloat(row.idx_profit)) ? parseFloat(row.idx_profit) : (window.formulaEngine.compute('margin_percent', row) || 0);
            const kubik = !isNaN(parseFloat(row.kubik)) ? parseFloat(row.kubik) : ((((parseFloat(row.p) || 0) * (parseFloat(row.l) || 0) * (parseFloat(row.t) || 0)) / 1000000) || 0);

            return {
                'NO': index + 1,
                'TANGGAL': formatDateExcel(row.tanggal_pickup),
                'IP PERUSAHAAN': row.nama || '',
                'AWB': row.awb || '',
                'AWB SISTEM': row.awb_sistem || '',
                'CUSTOMER': row.pengirim || '',
                'SALES': row.sales || '',
                'PENERIMA': row.penerima || '',
                'SERVICE': row.service || '',
                'VIA': row.via || '',
                'AKTUAL': parseFloat(row.aktual) || 0,
                'VOL': parseFloat(row.vol) || 0,
                'UNIT': parseInt(row.unit) || 0,
                'KUBIK': kubik,
                'P': parseFloat(row.p) || 0,
                'L': parseFloat(row.l) || 0,
                'T': parseFloat(row.t) || 0,
                'KOLI': parseInt(row.koil) || 0,
                'HARGA PERKILO': parseFloat(row.harga) || 0,
                'SURCHARGE': parseFloat(row.surcharge) || 0,
                'PACKING': parseFloat(row.packing) || 0,
                'HANDLING': parseFloat(row.handling) || 0,
                'PENJUALAN': penjualan,
                'ASAL PICK UP': row.asal_pickup || '',
                'JENIS BARANG': row.jenis_barang || '',
                'TUJUAN': row.tujuan || '',
                'NAMA VENDOR I': row.nama_vendor || '',
                'NAMA VENDOR II': row.nama_vendor_ii || '',
                'NAMA VENDOR III': row.nama_vendor_iii || '',
                'NAMA VENDOR IV': row.nama_vendor_iv || '',
                'HARGA VENDOR I': parseFloat(row.vendor_i) || 0,
                'HARGA VENDOR II': parseFloat(row.vendor_ii) || 0,
                'HARGA VENDOR III': parseFloat(row.vendor_iii) || 0,
                'HARGA VENDOR IV': parseFloat(row.vendor_iv) || 0,
                'OPS': parseFloat(row.ops) || 0,
                'TOTAL BIAYA': totalBiaya,
                'PROFIT': profit,
                'IDX PROFIT': margin,
                'PENJUALAN ASURANSI': parseFloat(row.asuransi) || 0,
                'NILAI BARANG': parseFloat(row.nilai_barang) || 0,
                'MODAL ASURANSI': parseFloat(row.asuransi_jasindo) || 0
            };
        });

        // Title logic
        const activeSheet = typeof sheetsManager !== 'undefined' ? sheetsManager.sheets.find(s => s.id == sheetsManager.activeSheetId) : null;
        const activeFile = typeof yearlyFileManager !== 'undefined' ? yearlyFileManager.files.find(f => f.id == yearlyFileManager.activeFileId) : null;
        const monthNameFromSheet = activeSheet ? activeSheet.name : 'Data';
        const yearMatch = activeFile ? activeFile.name.match(/\d{4}/) : null;
        const yearName = yearMatch ? yearMatch[0] : '';

        // Ekstrak bulan dari data pertama yang valid
        let dynamicMonthName = monthNameFromSheet;
        if (tableManager && tableManager.currentData && tableManager.currentData.length > 0) {
            const firstRow = tableManager.currentData.find(r => r && r.tanggal_pickup && r.tanggal_pickup.trim() !== '' && !String(r.id).startsWith('preload_'));
            if (firstRow) {
                const d = window.formulaEngine ? window.formulaEngine._parseDate(firstRow.tanggal_pickup) : new Date(firstRow.tanggal_pickup);
                if (d && !isNaN(d.getTime())) {
                    const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                    dynamicMonthName = months[d.getMonth()];
                }
            }
        }

        const titleString = `Data KPI Finance - Bulan ${dynamicMonthName} ${yearName}`.trim();

        const worksheet = XLSX.utils.json_to_sheet(dataForExcel, { origin: 'A3', cellDates: true });
        XLSX.utils.sheet_add_aoa(worksheet, [[titleString]], { origin: 'A1' });

        applyEnhancementsToWorksheet(worksheet, dataForExcel, tableManager.currentData);

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Data KPI Finance");

        const wscols = [
            { wch: 5 }, { wch: 15 }, { wch: 25 }, { wch: 15 }, { wch: 18 },
            { wch: 18 }, { wch: 15 }, { wch: 18 }, { wch: 10 }, { wch: 8 },
            { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 8 },
            { wch: 8 }, { wch: 8 }, { wch: 8 }, { wch: 15 }, { wch: 15 },
            { wch: 15 }, { wch: 15 }, { wch: 18 }, { wch: 18 }, { wch: 18 },
            { wch: 18 }, { wch: 18 }, { wch: 18 }, { wch: 18 }, { wch: 18 },
            { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 },
            { wch: 18 }, { wch: 18 }, { wch: 12 }, { wch: 18 }, { wch: 18 },
            { wch: 18 }
        ];
        worksheet['!cols'] = wscols;

        const safeMonth = dynamicMonthName.replace(/\s+/g, '_');
        const fileName = `PaketinCargo_Finance_Export_${safeMonth}_${yearName}.xlsx`.replace(/_$/, '');
        XLSX.writeFile(workbook, fileName);

        showToast('Data berhasil diexport ke Excel', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Gagal melakukan export: ' + error.message, 'error');
    }
}

window.exportFullYearToExcel = async function (fileId, fileName) {
    if (typeof databaseManager === 'undefined') return;

    try {
        showToast('Menyiapkan export full tahun, mohon tunggu...', 'info');
        const sheets = await databaseManager.fetchSheets(fileId);

        if (!sheets || sheets.length === 0) {
            showToast('Tidak ada data sheet untuk file ini', 'warning');
            return;
        }

        const workbook = XLSX.utils.book_new();
        let sheetFound = false;
        let usedSheetNames = new Set();

        for (const sheet of sheets) {
            const rows = await databaseManager.fetchAllData(sheet.id);
            if (!rows || rows.length === 0) continue;

            sheetFound = true;
            const formatDateExcel = (dateStr) => {
                if (!dateStr) return '';
                const d = window.formulaEngine ? window.formulaEngine._parseDate(dateStr) : new Date(dateStr);
                if (!d || isNaN(d.getTime())) return dateStr;
                return new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
            };

            const dataForExcel = rows.map((row, index) => {
                const penjualan = !isNaN(parseFloat(row.penjualan)) ? parseFloat(row.penjualan) : (window.formulaEngine.compute('penjualan', row) || 0);
                const totalBiaya = !isNaN(parseFloat(row.total_biaya)) ? parseFloat(row.total_biaya) : (window.formulaEngine.compute('total_biaya', row) || 0);
                const profit = !isNaN(parseFloat(row.profit)) ? parseFloat(row.profit) : (window.formulaEngine.compute('profit', row) || 0);
                const margin = !isNaN(parseFloat(row.idx_profit)) ? parseFloat(row.idx_profit) : (window.formulaEngine.compute('margin_percent', row) || 0);
                const kubik = !isNaN(parseFloat(row.kubik)) ? parseFloat(row.kubik) : ((((parseFloat(row.p) || 0) * (parseFloat(row.l) || 0) * (parseFloat(row.t) || 0)) / 1000000) || 0);

                return {
                    'NO': index + 1,
                    'TANGGAL': formatDateExcel(row.tanggal_pickup),
                    'IP PERUSAHAAN': row.nama || '',
                    'AWB': row.awb || '',
                    'AWB SISTEM': row.awb_sistem || '',
                    'CUSTOMER': row.pengirim || '',
                    'SALES': row.sales || '',
                    'PENERIMA': row.penerima || '',
                    'SERVICE': row.service || '',
                    'VIA': row.via || '',
                    'AKTUAL': parseFloat(row.aktual) || 0,
                    'VOL': parseFloat(row.vol) || 0,
                    'UNIT': parseInt(row.unit) || 0,
                    'KUBIK': kubik,
                    'P': parseFloat(row.p) || 0,
                    'L': parseFloat(row.l) || 0,
                    'T': parseFloat(row.t) || 0,
                    'KOLI': parseInt(row.koil) || 0,
                    'HARGA PERKILO': parseFloat(row.harga) || 0,
                    'SURCHARGE': parseFloat(row.surcharge) || 0,
                    'PACKING': parseFloat(row.packing) || 0,
                    'HANDLING': parseFloat(row.handling) || 0,
                    'PENJUALAN': penjualan,
                    'ASAL PICK UP': row.asal_pickup || '',
                    'JENIS BARANG': row.jenis_barang || '',
                    'TUJUAN': row.tujuan || '',
                    'NAMA VENDOR I': row.nama_vendor || '',
                    'NAMA VENDOR II': row.nama_vendor_ii || '',
                    'NAMA VENDOR III': row.nama_vendor_iii || '',
                    'NAMA VENDOR IV': row.nama_vendor_iv || '',
                    'HARGA VENDOR I': parseFloat(row.vendor_i) || 0,
                    'HARGA VENDOR II': parseFloat(row.vendor_ii) || 0,
                    'HARGA VENDOR III': parseFloat(row.vendor_iii) || 0,
                    'HARGA VENDOR IV': parseFloat(row.vendor_iv) || 0,
                    'OPS': parseFloat(row.ops) || 0,
                    'TOTAL BIAYA': totalBiaya,
                    'PROFIT': profit,
                    'IDX PROFIT': margin,
                    'PENJUALAN ASURANSI': parseFloat(row.asuransi) || 0,
                    'NILAI BARANG': parseFloat(row.nilai_barang) || 0,
                    'MODAL ASURANSI': parseFloat(row.asuransi_jasindo) || 0
                };
            });

            const yearMatch = fileName.match(/\d{4}/);
            const yearName = yearMatch ? yearMatch[0] : '';

            let dynamicMonthName = sheet.name;
            if (rows && rows.length > 0) {
                const firstRow = rows.find(r => r && r.tanggal_pickup && r.tanggal_pickup.trim() !== '');
                if (firstRow) {
                    const d = window.formulaEngine ? window.formulaEngine._parseDate(firstRow.tanggal_pickup) : new Date(firstRow.tanggal_pickup);
                    if (d && !isNaN(d.getTime())) {
                        const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                        dynamicMonthName = months[d.getMonth()];
                    }
                }
            }

            const titleString = `Data KPI Finance - Bulan ${dynamicMonthName} ${yearName}`.trim();

            const worksheet = XLSX.utils.json_to_sheet(dataForExcel, { origin: 'A3', cellDates: true });
            XLSX.utils.sheet_add_aoa(worksheet, [[titleString]], { origin: 'A1' });

            applyEnhancementsToWorksheet(worksheet, dataForExcel, rows);

            const wscols = [
                { wch: 5 }, { wch: 15 }, { wch: 25 }, { wch: 15 }, { wch: 18 },
                { wch: 18 }, { wch: 15 }, { wch: 18 }, { wch: 10 }, { wch: 8 },
                { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 10 }, { wch: 8 },
                { wch: 8 }, { wch: 8 }, { wch: 8 }, { wch: 15 }, { wch: 15 },
                { wch: 15 }, { wch: 15 }, { wch: 18 }, { wch: 18 }, { wch: 18 },
                { wch: 18 }, { wch: 18 }, { wch: 18 }, { wch: 18 }, { wch: 18 },
                { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 },
                { wch: 18 }, { wch: 18 }, { wch: 12 }, { wch: 18 }, { wch: 18 },
                { wch: 18 }
            ];
            worksheet['!cols'] = wscols;

            let baseSheetName = sheet.name.substring(0, 25);
            let validSheetName = baseSheetName;
            let counter = 1;
            while (usedSheetNames.has(validSheetName)) {
                validSheetName = `${baseSheetName} (${counter})`;
                counter++;
            }
            usedSheetNames.add(validSheetName);

            XLSX.utils.book_append_sheet(workbook, worksheet, validSheetName);
        }

        if (!sheetFound) {
            showToast('Semua sheet kosong', 'warning');
            return;
        }

        const fileYearMatch = fileName.match(/\d{4}/);
        const fileYear = fileYearMatch ? fileYearMatch[0] : '';
        const exportName = `PaketinCargo_Finance_Full_1_Tahun_${fileYear}.xlsx`.replace(/_$/, '');
        XLSX.writeFile(workbook, exportName);
        showToast('Data full tahun berhasil diexport ke Excel', 'success');
    } catch (err) {
        console.error('Full export error:', err);
        showToast('Gagal melakukan export full: ' + err.message, 'error');
    }
}


let _adminTab = 'users';

function switchAdminTab(tab) {
    _adminTab = tab;
    document.querySelectorAll('.admin-tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.admin-tab-pane').forEach(p => p.classList.toggle('active', p.dataset.pane === tab));

    if (tab === 'audit') {
        renderAuditLogsPane();
    }
}

async function renderAdminPanel() {
    const container = document.getElementById('adminPanelContent');
    if (!container) return;

    if (!authManager.isAdmin()) {
        container.innerHTML = '<div class="admin-denied"><i class="fas fa-lock"></i><h3>Akses Ditolak</h3><p>Hanya admin yang bisa mengakses halaman ini.</p></div>';
        return;
    }

    container.innerHTML = '<div class="admin-loading"><i class="fas fa-spinner fa-spin"></i> Memuat data...</div>';

    try {
        const [allPerms, userConfigs] = await Promise.all([
            databaseManager.fetchAllPermissions(),
            databaseManager.fetchUserConfigs()
        ]);

        const permsMap = {};
        allPerms.forEach(p => { permsMap[p.user_email] = p.allowed_columns || []; });

        const allUsers = _mergeUsers(userConfigs);
        const picUsers = allUsers.filter(u => u.role === 'pic');
        const adminUsers = allUsers.filter(u => u.role === 'admin');
        const viewerUsers = allUsers.filter(u => u.role === 'viewer');

        let html = `
        <div class="admin-tabs">
            <button class="admin-tab-btn ${_adminTab === 'users' ? 'active' : ''}" data-tab="users" onclick="switchAdminTab('users')">
                <i class="fas fa-users"></i> Manajemen User
            </button>
            <button class="admin-tab-btn ${_adminTab === 'permissions' ? 'active' : ''}" data-tab="permissions" onclick="switchAdminTab('permissions')">
                <i class="fas fa-shield-alt"></i> Hak Akses PIC
            </button>
            <button class="admin-tab-btn ${_adminTab === 'audit' ? 'active' : ''}" data-tab="audit" onclick="switchAdminTab('audit')">
                <i class="fas fa-history"></i> Audit Logs
            </button>
            <button class="admin-tab-btn ${_adminTab === 'settings' ? 'active' : ''}" data-tab="settings" onclick="switchAdminTab('settings')">
                <i class="fas fa-cog"></i> Pengaturan
            </button>
        </div>

        <div class="admin-tab-pane ${_adminTab === 'users' ? 'active' : ''}" data-pane="users">
            <div class="admin-section-header">
                <div>
                    <strong>Daftar User Terdaftar</strong>
                    <p style="font-size:0.78rem;color:var(--text-muted);margin:2px 0 0;">Kelola akses user, ubah role, atau hapus akses.</p>
                </div>
                <button class="btn-invite-user" onclick="showInviteModal()">
                    <i class="fas fa-user-plus"></i> Tambah User
                </button>
            </div>

            <div class="admin-online-card">
                <i class="fas fa-circle" style="color:#22c55e;font-size:0.6rem;"></i>
                <span id="adminOnlineList" style="font-size:0.8rem;color:var(--text-secondary);">Memeriksa status online...</span>
            </div>

            <div class="admin-user-list" id="adminUserList">
        `;

        adminUsers.forEach(u => {
            const initials = u.name.split(' ').map(n => n[0]).filter(c => c).join('').substring(0, 2).toUpperCase() || '??';
            const isSelf = u.email === authManager.currentUser?.email;
            html += `
                <div class="admin-user-row" data-email="${u.email}">
                    <div class="user-row-avatar" style="background:linear-gradient(135deg,#CC0000,#8B0000);">${initials}</div>
                    <div class="user-row-info">
                        <div class="user-row-name">
                            ${u.name} ${isSelf ? '<span class="user-self-badge">Anda</span>' : ''}
                            <i class="fas fa-edit btn-edit-name" onclick="editUserName('${u.email}', '${u.name}', '${u.role}')" title="Ubah Nama"></i>
                        </div>
                        <div class="user-row-email">${u.email}</div>
                    </div>
                    <div class="user-row-role">
                        <select class="role-select" onchange="changeUserRole('${u.email}', this.value)" ${isSelf ? 'disabled' : ''}>
                            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
                            <option value="pic" ${u.role === 'pic' ? 'selected' : ''}>PIC</option>
                            <option value="viewer" ${u.role === 'viewer' ? 'selected' : ''}>Viewer</option>
                        </select>
                    </div>
                    <div class="user-row-actions">
                        ${isSelf ? '<span style="color:var(--text-muted);font-size:0.75rem;">—</span>' : `<button class="btn-delete-user" onclick="deleteUserFull('${u.id}','${u.email}','${u.name}')" title="Hapus User Permanen"><i class="fas fa-trash-alt" style="color:var(--red);"></i></button>`}
                    </div>
                </div>
            `;
        });

        picUsers.forEach(u => {
            const initials = u.name.split(' ').map(n => n[0]).filter(c => c).join('').substring(0, 2).toUpperCase() || '??';
            html += `
                <div class="admin-user-row" data-email="${u.email}">
                    <div class="user-row-avatar" style="background:linear-gradient(135deg,#1d4ed8,#1e40af);">${initials}</div>
                    <div class="user-row-info">
                        <div class="user-row-name">
                            ${u.name}
                            <i class="fas fa-edit btn-edit-name" onclick="editUserName('${u.email}', '${u.name}', '${u.role}')" title="Ubah Nama"></i>
                        </div>
                        <div class="user-row-email">${u.email}</div>
                    </div>
                    <div class="user-row-role">
                        <select class="role-select" onchange="changeUserRole('${u.email}', this.value)">
                            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
                            <option value="pic" ${u.role === 'pic' ? 'selected' : ''}>PIC</option>
                            <option value="viewer" ${u.role === 'viewer' ? 'selected' : ''}>Viewer</option>
                        </select>
                    </div>
                    <div class="user-row-actions">
                        <button class="btn-delete-user" onclick="deleteUserFull('${u.id}','${u.email}','${u.name}')" title="Hapus User Permanen"><i class="fas fa-trash-alt" style="color:var(--red);"></i></button>
                    </div>
                </div>
            `;
        });

        viewerUsers.forEach(u => {
            const initials = u.name.split(' ').map(n => n[0]).filter(c => c).join('').substring(0, 2).toUpperCase() || '??';
            html += `
                <div class="admin-user-row" data-email="${u.email}">
                    <div class="user-row-avatar" style="background:linear-gradient(135deg,#6b7280,#4b5563);">${initials}</div>
                    <div class="user-row-info">
                        <div class="user-row-name">
                            ${u.name}
                            <i class="fas fa-edit btn-edit-name" onclick="editUserName('${u.email}', '${u.name}', '${u.role}')" title="Ubah Nama"></i>
                        </div>
                        <div class="user-row-email">${u.email}</div>
                    </div>
                    <div class="user-row-role">
                        <select class="role-select" onchange="changeUserRole('${u.email}', this.value)">
                            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
                            <option value="pic" ${u.role === 'pic' ? 'selected' : ''}>PIC</option>
                            <option value="viewer" ${u.role === 'viewer' ? 'selected' : ''}>Viewer</option>
                        </select>
                    </div>
                    <div class="user-row-actions">
                        <button class="btn-delete-user" onclick="deleteUserFull('${u.id}','${u.email}','${u.name}')" title="Hapus User Permanen"><i class="fas fa-trash-alt" style="color:var(--red);"></i></button>
                    </div>
                </div>
            `;
        });

        if (allUsers.length === 0) {
            html += `<div style="text-align:center;padding:40px;color:var(--text-muted);">
                <i class="fas fa-users" style="font-size:2rem;opacity:0.3;"></i>
                <p style="margin-top:12px;">Belum ada user terdaftar.</p>
            </div>`;
        }

        html += `</div></div>`;

        html += `
        <div class="admin-tab-pane ${_adminTab === 'permissions' ? 'active' : ''}" data-pane="permissions">
            <div class="admin-info-card" style="margin-bottom:16px;">
                <i class="fas fa-info-circle"></i>
                <div>
                    <strong>Cara Kerja Hak Akses</strong>
                    <p>PIC hanya bisa mengedit kolom yang dicentang. Perubahan berlaku setelah PIC refresh/login ulang.</p>
                </div>
            </div>
        `;

        if (picUsers.length === 0) {
            html += `<div class="admin-empty"><i class="fas fa-user-slash"></i><h3>Tidak Ada PIC</h3><p>Belum ada user dengan role PIC terdaftar.</p></div>`;
        } else {
            picUsers.forEach(pic => {
                const currentPerms = permsMap[pic.email] || [];
                const permCount = currentPerms.length;
                html += `
                <div class="pic-permission-card" data-email="${pic.email}">
                    <div class="pic-card-header">
                        <div class="pic-user-info">
                            <div class="pic-avatar">${pic.name.split(' ').map(n => n[0]).filter(c => c).join('').substring(0, 2).toUpperCase()}</div>
                            <div>
                                <div class="pic-name">${pic.name}</div>
                                <div class="pic-email">${pic.email}</div>
                            </div>
                        </div>
                        <div class="pic-perm-summary">
                            <span class="perm-count ${permCount > 0 ? 'has-perms' : 'no-perms'}">${permCount}</span>
                            <span class="perm-label">kolom</span>
                        </div>
                    </div>
                    <div class="pic-perm-body">
                `;

                COLUMN_CATEGORIES.forEach(cat => {
                    const catCols = EDITABLE_COLUMNS.filter(c => c.category === cat.key);
                    if (catCols.length === 0) return;
                    html += `
                        <div class="perm-category">
                            <div class="perm-category-header">
                                <i class="fas ${cat.icon}"></i>
                                <span>${cat.label}</span>
                                <button class="btn-toggle-category" onclick="toggleCategory('${pic.email}','${cat.key}',this)">Pilih Semua</button>
                            </div>
                            <div class="perm-checkboxes">
                    `;
                    catCols.forEach(col => {
                        const checked = currentPerms.includes(col.field) ? 'checked' : '';
                        html += `
                            <label class="perm-checkbox ${checked ? 'checked' : ''}">
                                <input type="checkbox" value="${col.field}" data-pic="${pic.email}" ${checked} onchange="onPermToggle(this)">
                                <span class="perm-checkmark"><i class="fas fa-check"></i></span>
                                <span class="perm-label-text">${col.label}</span>
                            </label>
                        `;
                    });
                    html += `</div></div>`;
                });

                html += `
                    </div>
                    <div class="pic-card-footer">
                        <button class="btn-save-perms" onclick="savePicPermissions('${pic.email}')">
                            <i class="fas fa-save"></i> Simpan Pengaturan
                        </button>
                        <span class="save-status" id="saveStatus-${pic.email.replace(/[@.]/g, '_')}"></span>
                    </div>
                </div>
                `;
            });
        }

        html += `</div>`;

        // Audit Logs Pane
        html += `
        <div class="admin-tab-pane ${_adminTab === 'audit' ? 'active' : ''}" data-pane="audit">
            <div style="width: fit-content; margin: 0 auto;">
                <div class="dashboard-section-title" style="margin-bottom: 20px; width: 100%; display: flex; justify-content: space-between; align-items: center; padding: 0;">
                    <div style="text-align: left;">
                        <strong style="display: block; font-size: 1.1rem; color: var(--text-primary);">Audit Log History</strong>
                        <p style="font-size:0.75rem; color:var(--text-muted); margin: 2px 0 0;">Monitoring data oleh semua user (100 log terakhir).</p>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <button class="btn-pill" onclick="renderAuditLogsPane()" title="Refresh Log">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>
                </div>
                
                <div class="card-glass" style="background: var(--bg-card); border-radius: 16px; border: 1px solid var(--border-light); box-shadow: var(--shadow-md); overflow: hidden; width: fit-content;">
                    <div id="auditLogsList" class="audit-table-container" style="min-height: 200px;">
                        <div style="padding:40px;text-align:center;color:var(--text-muted);">
                            <i class="fas fa-spinner fa-spin"></i> Memuat data log...
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        // Settings Pane
        const aiEnabled = localStorage.getItem('ai_assistant_enabled') !== 'false';
        html += `
        <div class="admin-tab-pane ${_adminTab === 'settings' ? 'active' : ''}" data-pane="settings">
            <div class="admin-info-card" style="margin-bottom:16px;">
                <i class="fas fa-cog"></i>
                <div>
                    <strong>Pengaturan Sistem</strong>
                    <p>Konfigurasi fitur-fitur tambahan pada sistem.</p>
                </div>
            </div>

            <div style="background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #ef4444, #b91c1c); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem;">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div>
                            <div style="font-weight: 700; color: var(--text-primary); font-size: 0.95rem;">AI Assistant</div>
                            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">Aktifkan/nonaktifkan fitur AI Assistant untuk analisis data otomatis. AI dapat menjawab pertanyaan tentang revenue, profit, pengiriman, customer, dan lainnya.</div>
                        </div>
                    </div>
                    <label class="toggle-switch" style="position: relative; display: inline-block; width: 52px; height: 28px; flex-shrink: 0; margin-left: 16px;">
                        <input type="checkbox" id="aiToggleSwitch" ${aiEnabled ? 'checked' : ''} onchange="toggleAIAssistant(this.checked)" style="opacity: 0; width: 0; height: 0;">
                        <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: ${aiEnabled ? '#22c55e' : '#ccc'}; transition: 0.3s; border-radius: 28px;">
                            <span style="position: absolute; content: ''; height: 22px; width: 22px; left: ${aiEnabled ? '27px' : '3px'}; bottom: 3px; background-color: white; transition: 0.3s; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.2);"></span>
                        </span>
                    </label>
                </div>
                <div id="aiToggleStatus" style="margin-top: 12px; padding: 8px 12px; border-radius: 8px; font-size: 0.78rem; font-weight: 600; background: ${aiEnabled ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)'}; color: ${aiEnabled ? '#16a34a' : '#dc2626'}; border: 1px solid ${aiEnabled ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'};">
                    <i class="fas ${aiEnabled ? 'fa-check-circle' : 'fa-times-circle'}"></i> AI Assistant saat ini ${aiEnabled ? 'AKTIF' : 'NONAKTIF'}
                </div>
            </div>

            <div style="background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #10b981, #047857); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem;">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <div>
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.95rem;">API Key Gemini (Server-Side)</div>
                        <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">
                            Status: <span style="color: #16a34a; font-weight: 700;">
                                ✓ Terkonfigurasi Aman
                            </span>
                            — Diatur melalui <code style="background:var(--bg-secondary); padding:2px 6px; border-radius:4px; font-size:0.72rem;">Vercel Environment Variables</code>
                        </div>
                        <div style="font-size: 0.72rem; color: #16a34a; margin-top: 4px;">
                            <i class="fas fa-lock"></i> Catatan Keamanan: API key saat ini tersimpan dan berjalan secara aman di server proxy (Vercel Edge Function). Kunci rahasia tidak terekspos ke sisi klien.
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        // Invite Modal
        html += `
        <div id="inviteModal" class="modal-overlay" style="display:none;" onclick="if(event.target===this)closeInviteModal()">
            <div class="modal-card">
                <div class="modal-header">
                    <h3><i class="fas fa-user-plus"></i> Tambah User Baru</h3>
                    <button class="modal-close" onclick="closeInviteModal()"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <div class="register-info" style="margin-bottom:14px; background:var(--bg-secondary); padding:10px; border-radius:6px; border-left:3px solid var(--primary);">
                        <i class="fas fa-info-circle"></i>
                        <span style="font-size:0.75rem;">Menambahkan user ke database agar bisa mendapatkan akses login ke sistem.</span>
                    </div>
                    <div class="form-group">
                        <label>Email User</label>
                        <input type="email" id="inviteEmail" placeholder="email@example.com" class="form-input">
                    </div>
                    <div class="form-group">
                        <label>Role</label>
                        <select id="inviteRole" class="form-input">
                            <option value="pic">PIC (bisa edit kolom tertentu)</option>
                            <option value="admin">Admin (akses penuh)</option>
                            <option value="viewer">Viewer (hanya baca)</option>
                        </select>
                    </div>
                    <div id="inviteError" class="invite-error" style="display:none;"></div>
                    <div id="inviteSuccess" class="invite-success" style="display:none;"></div>
                </div>
                <div class="modal-footer">
                    <button class="btn-modal-cancel" onclick="closeInviteModal()">Batal</button>
                    <button class="btn-modal-confirm" id="inviteSubmitBtn" onclick="submitInviteUser()">
                        <i class="fas fa-check"></i> Tambahkan
                    </button>
                </div>
            </div>
        </div>
        `;

        container.innerHTML = html;
        _updateAdminOnlineList();

    } catch (error) {
        console.error('Render admin panel error:', error);
        container.innerHTML = '<div class="admin-denied"><i class="fas fa-exclamation-triangle"></i><h3>Error</h3><p>' + error.message + '</p></div>';
    }

    if (_adminTab === 'audit') renderAuditLogsPane();
}

async function renderAuditLogsPane() {
    await _internalRenderAudit('auditLogsList');
}

function toggleAIAssistant(enabled) {
    AIChatManager.toggleAIFeature(enabled);

    // Update toggle visual
    const statusEl = document.getElementById('aiToggleStatus');
    if (statusEl) {
        statusEl.style.background = enabled ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)';
        statusEl.style.color = enabled ? '#16a34a' : '#dc2626';
        statusEl.style.borderColor = enabled ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)';
        statusEl.innerHTML = `<i class="fas ${enabled ? 'fa-check-circle' : 'fa-times-circle'}"></i> AI Assistant saat ini ${enabled ? 'AKTIF' : 'NONAKTIF'}`;
    }

    // Update toggle slider visual
    const toggleSwitch = document.getElementById('aiToggleSwitch');
    if (toggleSwitch) {
        const slider = toggleSwitch.nextElementSibling;
        if (slider) {
            slider.style.backgroundColor = enabled ? '#22c55e' : '#ccc';
            const dot = slider.querySelector('span');
            if (dot) dot.style.left = enabled ? '27px' : '3px';
        }
    }

    showToast(`AI Assistant ${enabled ? 'diaktifkan' : 'dinonaktifkan'}`, enabled ? 'success' : 'info');
}

let _historySubTab = 'audit'; // Deprecated

async function switchHistorySubTab(tab) {
    // Deprecated. Kept for compatibility if called elsewhere.
}

async function renderAuditLogsPage() {
    const listData = document.getElementById('auditLogsPageList_data');
    const listLogin = document.getElementById('auditLogsPageList_login');
    if (!listData || !listLogin) return;

    // Render both simultaneously
    _internalRenderAudit('auditLogsPageList_data');
    renderLoginLogsList('auditLogsPageList_login');
}

async function renderLoginLogsList(elementId) {
    const listEl = document.getElementById(elementId);
    if (!listEl) return;

    listEl.innerHTML = `
        <div style="padding:80px;text-align:center;color:var(--text-muted);">
            <i class="fas fa-spinner fa-spin" style="font-size:2.5rem;margin-bottom:15px;color:var(--red);display:block;opacity:0.8;"></i>
            <p style="font-weight:600;">Memuat riwayat login...</p>
        </div>
    `;

    try {
        const logs = await databaseManager.getAuditLogs(500);
        let loginLogs = logs ? logs.filter(log => log.field_name === 'login') : [];
        loginLogs = loginLogs.slice(0, 50); // Batasi 50 data terbaru

        // Update counter
        const countDisplay = document.getElementById('loginCountDisplay');
        if (countDisplay) {
            countDisplay.textContent = loginLogs.length + ' Login';
        }

        if (loginLogs.length === 0) {
            listEl.innerHTML = `
                <div style="padding:80px;text-align:center;color:var(--text-muted);">
                    <i class="fas fa-sign-in-alt" style="font-size:3rem;opacity:0.2;margin-bottom:15px;display:block;"></i>
                    <p style="font-weight:600;">Belum ada riwayat login yang tercatat.</p>
                </div>
            `;
            return;
        }

        let html = `
            <table class="audit-table" style="width: 100%; table-layout: fixed;">
                <thead>
                    <tr>
                        <th style="width: 25%;">Waktu Login</th>
                        <th style="width: 35%;">User</th>
                        <th style="width: 40%;">Detail Perangkat & Sesi</th>
                    </tr>
                </thead>
                <tbody>
        `;

        loginLogs.forEach(log => {
            const timestamp = log.created_at || log.changed_at;
            const time = timestamp ? new Date(timestamp).toLocaleString('id-ID', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            }) : '-';

            const changer = log.changed_by || log.user_name || log.user_email || 'System';
            const detail = log.new_value || 'Login Berhasil';
            const email = log.user_email || '-';
            const initial = changer.charAt(0).toUpperCase();

            html += `
                <tr style="border-bottom: 1px solid var(--border-light); transition: background-color 0.2s;">
                    <td class="audit-time" style="color: var(--text-muted); font-size: 0.85rem;">${time}</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--red), #8b0000); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem; flex-shrink: 0;">
                                ${initial}
                            </div>
                            <div style="display: flex; flex-direction: column;">
                                <strong style="color: var(--text-primary); font-size: 0.9rem;">${changer}</strong>
                                <span style="font-size: 0.75rem; color: var(--text-muted);">${email}</span>
                            </div>
                        </div>
                    </td>
                    <td>
                        <div style="font-weight: 500; color: var(--text-primary); display: flex; align-items: center; gap: 10px;">
                            <span style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #10b981; padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; gap: 4px;">
                                <i class="fas fa-check-circle"></i> SUCCESS
                            </span>
                            <span style="font-size: 0.85rem;">${detail}</span>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        listEl.innerHTML = html;
    } catch (err) {
        listEl.innerHTML = `<div style="padding:20px;color:var(--red);text-align:center;">Gagal memuat log login: ${err.message}</div>`;
    }
}

async function _internalRenderAudit(elementId) {
    const listEl = document.getElementById(elementId);
    if (!listEl) return;

    try {
        const logsRaw = await databaseManager.getAuditLogs(500);
        // Saring agar event login dan formulas tidak bercampur dengan log data
        let logs = logsRaw ? logsRaw.filter(log => log.field_name !== 'login' && log.field_name !== 'formulas') : [];
        logs = logs.slice(0, 50); // Batasi 50 data terbaru

        // Update counter if display exists
        const countDisplay = document.getElementById('dataCountDisplay');
        if (countDisplay) countDisplay.textContent = (logs ? logs.length : 0) + ' Data';

        if (!logs || logs.length === 0) {
            listEl.innerHTML = `
                        <div style="padding:80px;text-align:center;color:var(--text-muted);">
                    <i class="fas fa-history" style="font-size:3rem;opacity:0.2;margin-bottom:15px;display:block;"></i>
                    <p style="font-weight:600;">Belum ada history perubahan yang tercatat.</p>
                </div>
            `;
            return;
        }

        // Pre-fetch missing row context
        const visualRowMap = new Map();
        const rowContextMap = new Map();
        const missingRowIds = new Set();

        logs.forEach(log => {
            const idStr = String(log.row_id);
            if (window.tableManager && window.tableManager.rowMap && window.tableManager.currentData) {
                const rowData = window.tableManager.rowMap.get(idStr);
                if (rowData) {
                    const idx = window.tableManager.currentData.indexOf(rowData);
                    if (idx >= 0) visualRowMap.set(idStr, idx + 1);
                    if (rowData.awb) rowContextMap.set(idStr, `<br><span style="font-size:0.7rem;color:var(--text-muted);font-weight:normal;">AWB: ${rowData.awb}</span>`);
                    else if (rowData.nama) rowContextMap.set(idStr, `<br><span style="font-size:0.7rem;color:var(--text-muted);font-weight:normal;">${rowData.nama}</span>`);
                    return;
                }
            }
            if (log.row_id && !idStr.startsWith('preload_')) missingRowIds.add(log.row_id);
        });

        if (missingRowIds.size > 0 && supabaseClient) {
            try {
                const { data: rows } = await supabaseClient.from('kpi_finance')
                    .select('id, sheet_id, nama, awb, kpi_sheets(name)')
                    .in('id', Array.from(missingRowIds));

                if (rows) {
                    await Promise.all(rows.map(async (r) => {
                        const idStr = String(r.id);
                        let ctx = '';
                        if (r.kpi_sheets && r.kpi_sheets.name) ctx += `<span style="font-size:0.7rem;color:var(--primary);font-weight:600;">[${r.kpi_sheets.name}]</span> `;
                        if (r.awb) ctx += `<span style="font-size:0.7rem;color:var(--text-muted);font-weight:normal;">AWB: ${r.awb}</span>`;
                        else if (r.nama) ctx += `<span style="font-size:0.7rem;color:var(--text-muted);font-weight:normal;">${r.nama}</span>`;
                        rowContextMap.set(idStr, '<br>' + ctx);

                        const { count } = await supabaseClient.from('kpi_finance')
                            .select('id', { count: 'exact', head: true })
                            .eq('sheet_id', r.sheet_id)
                            .lte('id', r.id);

                        if (count !== null) visualRowMap.set(idStr, count);
                    }));
                }
            } catch (e) {
                console.warn('Failed to fetch audit log context:', e);
            }
        }

        let html = `
            <table class="audit-table" style="width: 100%; table-layout: fixed;">
                <thead>
                    <tr>
                        <th style="width: 15%;">Waktu</th>
                        <th style="width: 25%;">User</th>
                        <th style="width: 20%;">Baris / Referensi</th>
                        <th style="width: 15%;">Kolom</th>
                        <th style="width: 25%;">Perubahan</th>
                    </tr>
                </thead>
                <tbody>
        `;

        logs.forEach(log => {
            const time = log.created_at ? new Date(log.created_at).toLocaleString('id-ID', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            }) : '-';

            // Helper to format values cleanly & simply
            const formatValue = (val, isNew = false) => {
                if (val === null || val === undefined || val === '') return '<span style="color:var(--text-muted);font-style:italic;">Kosong</span>';
                if (String(val) === '[object Object]') return '<span style="color:var(--text-muted);font-style:italic;">Format Lama</span>';

                const pillColor = isNew ? 'color:#059669;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2)' : 'color:var(--text-muted);background:var(--bg-secondary);border:1px solid var(--border-light)';
                const pillStyle = `padding:3px 8px;border-radius:6px;font-size:0.75rem;display:inline-flex;align-items:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:110px;${pillColor}`;

                const processObj = (obj) => {
                    const entries = Object.entries(obj);
                    if (entries.length === 0) return '-';
                    const [k, v] = entries[0];
                    let vStr = String(v);
                    if (vStr.length > 12) vStr = vStr.substring(0, 12) + '...';
                    let res = `<span style="${pillStyle}"><strong style="margin-right:4px;opacity:0.8;">${k}:</strong> <span>${vStr}</span></span>`;
                    if (entries.length > 1) res += `<span style="font-size:0.7rem;color:var(--primary);margin-left:4px;font-weight:600;">+${entries.length - 1}</span>`;
                    return res;
                };

                if (typeof val === 'object') return processObj(val);

                let parsed = val;
                if (typeof val === 'string' && val.trim().startsWith('{')) {
                    try { parsed = JSON.parse(val); } catch (e) { }
                }
                if (typeof parsed === 'object' && parsed !== null) return processObj(parsed);

                if (!isNaN(val) && val.toString().includes('.') && val.toString().split('.')[1].length > 2) {
                    return `<span style="${pillStyle};font-weight:600;max-width:80px;">${parseFloat(val).toFixed(2)}</span>`;
                }

                let str = String(val);
                if (str.length > 18) str = str.substring(0, 18) + '...';
                return `<span style="${pillStyle};font-weight:600;max-width:90px;">${str}</span>`;
            };

            const idStr = String(log.row_id);
            const visualRow = visualRowMap.get(idStr) || null;
            const rowContext = rowContextMap.get(idStr) || '';
            const rowLabel = (visualRow ? visualRow : log.row_id) + rowContext;

            const FIELD_MAP = {
                'tanggal_pickup': 'TANGGAL', 'nama': 'NAMA', 'awb': 'AWB', 'awb_sistem': 'AWB SISTEM',
                'pengirim': 'PENGIRIM', 'sales': 'SALES', 'penerima': 'PENERIMA', 'service': 'SERVICE',
                'via': 'VIA', 'aktual': 'AKTUAL', 'vol': 'VOL', 'unit': 'UNIT', 'kubik': 'KUBIK',
                'p': 'P', 'l': 'L', 't': 'T', 'koil': 'KOLI', 'harga': 'HARGA PERKILO',
                'surcharge': 'SURCHARGE', 'packing': 'PACKING', 'handling': 'HANDLING',
                'penjualan': 'PENJUALAN', 'asal_pickup': 'ASAL PICK UP', 'jenis_barang': 'JENIS BARANG',
                'tujuan': 'TUJUAN', 'nama_vendor': 'NAMA VENDOR', 'vendor_i': 'VENDOR I',
                'vendor_ii': 'VENDOR II', 'vendor_iii': 'VENDOR III', 'vendor_iv': 'VENDOR IV',
                'ops': 'OPS', 'total_biaya': 'TOTAL BIAYA', 'profit': 'PROFIT', 'idx_profit': 'IDX PROFIT',
                'asuransi': 'ASURANSI', 'nilai_barang': 'NILAI BARANG', 'asuransi_jasindo': 'ASURANSI JASINDO'
            };

            let fieldLabel = FIELD_MAP[log.field_name] || String(log.field_name).toUpperCase();

            let extOld = log.old_value;
            let extNew = log.new_value;

            if (log.field_name === 'formulas') {
                try {
                    let pNew = typeof extNew === 'string' && extNew.startsWith('{') ? JSON.parse(extNew) : extNew;
                    let pOld = typeof extOld === 'string' && extOld.startsWith('{') ? JSON.parse(extOld) : extOld;

                    if (pNew && typeof pNew === 'object') {
                        const keys = Object.keys(pNew);
                        if (keys.length > 0) {
                            const k = keys[0];
                            fieldLabel = FIELD_MAP[k] || String(k).toUpperCase();
                            extNew = pNew[k];

                            if (pOld && typeof pOld === 'object' && pOld[k] !== undefined) {
                                extOld = pOld[k];
                            } else {
                                extOld = (String(log.old_value) === '[object Object]') ? 'Format Lama' : 'Kosong';
                            }

                            if (keys.length > 1) fieldLabel += ` (+${keys.length - 1})`;
                        }
                    }
                } catch (e) { }
            }

            if (fieldLabel.length > 15) fieldLabel = fieldLabel.substring(0, 15) + '...';

            const oldValStr = formatValue(extOld, false);
            const newValStr = formatValue(extNew, true);

            const changer = log.changed_by || log.user_name || log.user_email || 'System';
            const initial = changer.charAt(0).toUpperCase();

            html += `
                <tr style="border-bottom: 1px solid var(--border-light); transition: background-color 0.2s;">
                    <td style="padding: 12px 8px; color: var(--text-muted); font-size: 0.75rem;">${time}</td>
                    <td style="padding: 12px 8px;">
                        <div style="display: flex; align-items: center; gap: 8px; overflow: hidden;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.7rem; flex-shrink: 0; box-shadow: 0 2px 4px rgba(239,68,68,0.2);">
                                ${initial}
                            </div>
                            <strong style="color: var(--text-primary); font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600;" title="${changer}">${changer}</strong>
                        </div>
                    </td>
                    <td style="padding: 12px 8px;">
                        <span style="background: var(--bg-secondary); border: 1px solid var(--border-light); padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; color: var(--text-primary); display: inline-flex; align-items: center; gap: 4px; white-space:nowrap;">
                            <i class="fas fa-hashtag" style="font-size: 0.65rem; color: var(--text-muted);"></i> ${rowLabel}
                        </span>
                    </td>
                    <td style="padding: 12px 8px;">
                        <span style="background: rgba(59,130,246,0.1); color: #2563eb; border: 1px solid rgba(59,130,246,0.2); padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.7rem; display: inline-flex; align-items: center; gap: 4px; white-space:nowrap;" title="${FIELD_MAP[log.field_name] || String(log.field_name).toUpperCase()}">
                            <i class="fas fa-columns" style="font-size: 0.65rem; opacity: 0.7;"></i> ${fieldLabel}
                        </span>
                    </td>
                    <td style="padding: 12px 8px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            ${oldValStr}
                            <i class="fas fa-arrow-right" style="color: var(--primary); font-size: 0.7rem; flex-shrink: 0; opacity: 0.6;"></i>
                            ${newValStr}
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        listEl.innerHTML = html;
    } catch (err) {
        listEl.innerHTML = `<div style="padding:20px;color:var(--red);text-align:center;">Gagal memuat log: ${err.message}</div>`;
    }
}

function switchHistoryTab(tabId) {
    const btnData = document.getElementById('tabBtnData');
    const btnLogin = document.getElementById('tabBtnLogin');
    const panelData = document.getElementById('panelHistoryData');
    const panelLogin = document.getElementById('panelHistoryLogin');

    if (!btnData || !btnLogin || !panelData || !panelLogin) return;

    if (tabId === 'data') {
        btnData.classList.add('active');
        btnData.style.background = '';
        btnData.style.color = '';
        btnData.style.border = '';

        btnLogin.classList.remove('active');
        btnLogin.style.background = 'transparent';
        btnLogin.style.color = 'var(--text-muted)';
        btnLogin.style.border = '1px solid transparent';

        panelData.style.display = 'flex';
        panelLogin.style.display = 'none';
    } else {
        btnLogin.classList.add('active');
        btnLogin.style.background = '';
        btnLogin.style.color = '';
        btnLogin.style.border = '';

        btnData.classList.remove('active');
        btnData.style.background = 'transparent';
        btnData.style.color = 'var(--text-muted)';
        btnData.style.border = '1px solid transparent';

        panelLogin.style.display = 'flex';
        panelData.style.display = 'none';
    }
}

window.switchHistoryTab = switchHistoryTab;
window.switchHistorySubTab = switchHistorySubTab;
window.renderAuditLogsPage = renderAuditLogsPage;
window.renderLoginLogsList = renderLoginLogsList;

function _mergeUsers(dbUsers) {
    const merged = {};

    // ✅ Prioritas utama: Data dari database
    dbUsers.forEach(u => {
        merged[u.email] = {
            email: u.email,
            id: u.id, // UUID from auth.users (needed for deleteUserFull)
            name: u.name || u.display_name || u.email.split('@')[0],
            role: u.role || 'viewer',
            source: 'db'
        };
    });

    // ✅ Fallback: User hardcoded yang belum ada di DB (baru ditambah, belum disinkronkan)
    Object.entries(USER_ROLES).forEach(([email, cfg]) => {
        if (!merged[email]) {
            merged[email] = {
                email,
                name: cfg.name,
                role: cfg.role,
                source: 'local'
            };
        }
    });

    return Object.values(merged);
}

function _updateAdminOnlineList() {
    const listEl = document.getElementById('adminOnlineList');
    if (!listEl || !onlineUsersChannel) {
        if (listEl) listEl.textContent = 'Presence tidak tersedia';
        return;
    }
    const state = onlineUsersChannel.presenceState();
    const users = Object.values(state).map(u => u[0]).filter(Boolean);
    const admins = users.filter(u => u.role === 'ADMIN');
    if (admins.length === 0) {
        listEl.textContent = 'Tidak ada admin lain yang online';
    } else {
        listEl.innerHTML = '<strong>Admin online:</strong> ' + admins.map(u => `<span style="font-weight:600;">${u.name}</span>`).join(', ');
    }
    if (currentPage === 'admin') {
        setTimeout(_updateAdminOnlineList, 10000);
    }
}

function showInviteModal() {
    const m = document.getElementById('inviteModal');
    if (m) {
        m.style.display = 'flex';
        document.getElementById('inviteEmail').value = '';
        document.getElementById('inviteRole').value = 'pic';
        document.getElementById('inviteError').style.display = 'none';
        document.getElementById('inviteSuccess').style.display = 'none';
        const btn = document.getElementById('inviteSubmitBtn');
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-check"></i> Tambahkan'; }
        setTimeout(() => document.getElementById('inviteEmail').focus(), 100);
    }
}

function closeInviteModal() {
    const modal = document.getElementById('inviteModal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('inviteEmail').value = '';
        document.getElementById('inviteError').style.display = 'none';
        document.getElementById('inviteSuccess').style.display = 'none';
        const btn = document.getElementById('inviteSubmitBtn');
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-check"></i> Tambahkan'; }
    }
}

async function submitInviteUser() {
    const email = document.getElementById('inviteEmail')?.value?.trim();
    const role = document.getElementById('inviteRole')?.value;
    const errorEl = document.getElementById('inviteError');
    const successEl = document.getElementById('inviteSuccess');
    const btn = document.getElementById('inviteSubmitBtn');

    if (!email || !email.includes('@')) {
        errorEl.textContent = 'Mohon masukkan email yang valid';
        errorEl.style.display = 'block';
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mengirim...';
    }
    errorEl.style.display = 'none';
    successEl.style.display = 'none';

    try {
        await databaseManager.inviteUser(email, role);

        if (btn) {
            btn.innerHTML = '<i class="fas fa-check"></i> Berhasil';
        }

        successEl.innerHTML = `<i class="fas fa-check-circle"></i> User <b>${email}</b> berhasil ditambahkan! <br><small>Beritahu user untuk mendaftar menggunakan email tersebut di halaman Login.</small>`;
        successEl.style.display = 'block';

        // Refresh admin panel
        await syncUserRolesFromDatabase();
        renderAdminPanel();

        setTimeout(() => closeInviteModal(), 3000);
    } catch (err) {
        console.error('Submit invite error:', err);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check"></i> Tambahkan';
        }
        errorEl.textContent = err.message;
        errorEl.style.display = 'block';
    }
}

function showInviteError(msg) {
    const el = document.getElementById('inviteError');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}

async function deleteUserAccess(email, name) {
    // Legacy fallback — routes to deleteUserFull if UUID is unavailable
    // Find UUID from USER_ROLES or warn
    const cfg = USER_ROLES[email];
    await deleteUserFull(cfg?.id || null, email, name);
}

async function deleteUserFull(userId, email, name) {
    const confirmed = await showConfirm({
        title: 'Hapus User Permanen',
        message: `Hapus user "${name}" (${email}) secara permanen?\n\n✗ Akun login akan dihapus total\n✗ Data profil & hak akses dihapus\n✗ User tidak bisa login kembali`,
        icon: 'danger',
        confirmText: 'Hapus Permanen',
        confirmClass: 'danger'
    });

    if (!confirmed) return;

    // Find userId from admin panel user list if not passed
    if (!userId) {
        try {
            const users = await databaseManager.fetchUserConfigs();
            const found = users.find(u => u.email === email);
            userId = found?.id || null;
        } catch (e) { /* ignore */ }
    }

    if (!userId) {
        showToast('Gagal mendapatkan ID user. Pastikan user terdaftar di database.', 'error');
        return;
    }

    // Show loading state on button
    const btn = document.querySelector(`.btn-delete-user[onclick*="${email}"]`);
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; }

    try {
        // Call Supabase RPC that deletes: auth.users + profiles + user_permissions
        await databaseManager.deleteUserFull(userId, email);
        delete USER_ROLES[email];
        renderAdminPanel();
        showToast(`User "${name}" berhasil dihapus permanen`, 'success');
    } catch (err) {
        console.error('deleteUserFull error:', err);
        showToast('Gagal menghapus user: ' + err.message, 'error');
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-trash-alt" style="color:var(--red);"></i>'; }
    }
}


async function changeUserRole(email, newRole) {
    const confirmed = await showConfirm({
        title: 'Ubah Role User',
        message: `Ubah role ${email} menjadi ${newRole.toUpperCase()}?`,
        icon: 'warning',
        confirmText: 'Ubah',
        confirmClass: 'primary'
    });

    if (!confirmed) {
        renderAdminPanel();
        return;
    }

    try {
        await databaseManager.updateUserRole(email, newRole);

        // ✅ Update USER_ROLES (yang sudah disinkronkan dari DB)
        if (USER_ROLES[email]) {
            USER_ROLES[email].role = newRole;
            USER_ROLES[email].canEditAll = newRole === 'admin';
            USER_ROLES[email].allowedColumns = newRole === 'admin' ? null : [];
        }

        // ✅ Jika diturunkan dari admin ke pic, reset permissions
        if (newRole === 'pic') {
            try {
                await databaseManager.resetPermissions(email);
            } catch (e) { /* ignore */ }
        }

        showToast(`Role ${email} diubah ke ${newRole}`, 'success');
        renderAdminPanel();
    } catch (err) {
        showToast('Gagal mengubah role: ' + err.message, 'error');
        renderAdminPanel();
    }
}

function onPermToggle(checkbox) {
    const label = checkbox.closest('.perm-checkbox');
    if (checkbox.checked) {
        label.classList.add('checked');
    } else {
        label.classList.remove('checked');
    }

    const card = checkbox.closest('.pic-permission-card');
    if (card) {
        const checkedCount = card.querySelectorAll('input[type="checkbox"]:checked').length;
        const countEl = card.querySelector('.perm-count');
        if (countEl) {
            countEl.textContent = checkedCount;
            countEl.className = 'perm-count ' + (checkedCount > 0 ? 'has-perms' : 'no-perms');
        }
    }
}

let _dataLoaded = false;
let _dashboardDataLoadedForFile = null;

async function loadAllData() {
    if (_dataLoaded && tableManager.currentData.length > 0) {
        tableManager.renderTable(tableManager.currentData);
        // Dashboard stats will be rendered below if needed
    } else {
        try {
            const data = await databaseManager.fetchAllData(window.activeSheetId);
            if (data) {
                tableManager.renderTable(data);

                if (!authManager.isReadOnlyUser()) {
                    const currentCount = data.length;
                    if (currentCount < 1000) {
                        await tableManager.preloadEmptyRows(1000, 'fill');
                    }
                }
                _dataLoaded = true;

                // UX: Reset scroll and cell focus on initial load
                if (typeof currentPage !== 'undefined' && currentPage === 'table' && typeof tableManager !== 'undefined') {
                    if (!tableManager.activeCell) {
                        setTimeout(() => tableManager.resetSheetView(), 150);
                    } else {
                        const activeId = tableManager.activeCell.dataset.id;
                        const activeField = tableManager.activeCell.dataset.field;
                        setTimeout(() => {
                            const td = document.querySelector(`td[data-id="${activeId}"][data-field="${activeField}"]`);
                            if (td) {
                                tableManager.selectCell(td);
                            }
                            // Avoid scrolling if they just imported data, let them stay where they are
                        }, 150);
                    }
                }
            }
        } catch (e) {
            console.error('loadAllData table error:', e);
        }
    }

    // Dashboard Data (Yearly Data)
    try {
        if (typeof chartsManager !== 'undefined') {
            chartsManager.invalidateCache();
        }
        const activeFileId = window.yearlyFileManager ? window.yearlyFileManager.activeFileId : null;
        if (activeFileId) {
            console.log('[loadAllData] Fetching yearly data for fileId:', activeFileId);
            const yearlyData = await databaseManager.fetchYearlyData(activeFileId, 'id, nama, tanggal_pickup, awb, awb_sistem, pengirim, service, penjualan, profit, total_biaya, sheet_id, formulas');
            console.log('[loadAllData] Yearly data rows:', yearlyData.length);
            if (typeof chartsManager !== 'undefined') {
                chartsManager.renderDashboardStats(yearlyData);
            }
            _dashboardDataLoadedForFile = activeFileId;
        }

        const lastUpdated = document.getElementById('lastUpdated');
        if (lastUpdated) {
            lastUpdated.innerHTML = `<span class="realtime-indicator"></span> Last updated: ${new Date().toLocaleTimeString('id-ID')}`;
        }
    } catch (error) {
        console.error('Error loading data:', error);
    }

    // Automatically trigger recapPageManager refresh if the user hard-refreshed onto the Recap tab
    if (typeof currentPage !== 'undefined' && currentPage === 'recap' && window.recapPageManager) {
        window.recapPageManager.refreshData().catch(err => console.error('Recap auto-refresh error:', err));
    }
}

function toggleCategory(picEmail, categoryKey, btn) {
    const card = btn.closest('.pic-permission-card');
    const catCols = EDITABLE_COLUMNS.filter(c => c.category === categoryKey);
    const catFields = catCols.map(c => c.field);

    const allChecked = catFields.every(f => {
        const cb = card.querySelector(`input[data-pic="${picEmail}"][value="${f}"]`);
        return cb && cb.checked;
    });

    catFields.forEach(f => {
        const cb = card.querySelector(`input[data-pic="${picEmail}"][value="${f}"]`);
        if (cb) {
            cb.checked = !allChecked;
            onPermToggle(cb);
        }
    });

    btn.textContent = allChecked ? 'Pilih Semua' : 'Hapus Semua';
}

async function savePicPermissions(picEmail) {
    const card = document.querySelector(`.pic-permission-card[data-email="${picEmail}"]`);
    if (!card) return;

    const statusEl = document.getElementById('saveStatus-' + picEmail.replace(/[@.]/g, '_'));
    const saveBtn = card.querySelector('.btn-save-perms');

    const checked = card.querySelectorAll('input[type="checkbox"]:checked');
    const allowedColumns = Array.from(checked).map(cb => cb.value);

    if (statusEl) statusEl.textContent = 'Menyimpan...';
    if (saveBtn) { saveBtn.disabled = true; saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...'; }

    try {
        await databaseManager.upsertPermissions(picEmail, allowedColumns);

        if (USER_ROLES[picEmail]) {
            USER_ROLES[picEmail].allowedColumns = allowedColumns;
        }

        if (statusEl) {
            statusEl.innerHTML = '<i class="fas fa-check-circle" style="color:#16a34a;"></i> Tersimpan!';
            setTimeout(() => { statusEl.textContent = ''; }, 3000);
        }
        showToast('Hak akses berhasil disimpan', 'success');
    } catch (error) {
        console.error('Save permissions error:', error);
        if (statusEl) {
            statusEl.innerHTML = '<i class="fas fa-times-circle" style="color:#dc2626;"></i> Gagal: ' + error.message;
        }
        showToast('Gagal menyimpan hak akses', 'error');
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Simpan Pengaturan';
        }
    }
}

// Global function to edit user name — inline editable
window.editUserName = function (email, currentName, currentRole) {
    const row = document.querySelector(`.admin-user-row[data-email="${email}"]`);
    if (!row) return;

    const nameEl = row.querySelector('.user-row-name');
    if (!nameEl || nameEl.dataset.editing === 'true') return;

    nameEl.dataset.editing = 'true';
    const selfBadge = nameEl.querySelector('.user-self-badge');
    const selfHtml = selfBadge ? selfBadge.outerHTML : '';

    nameEl.innerHTML = `
        <input type="text" class="inline-name-input" value="${currentName}" autocomplete="off">
        <button class="inline-name-save" title="Simpan"><i class="fas fa-check"></i></button>
        <button class="inline-name-cancel" title="Batal"><i class="fas fa-times"></i></button>
    `;

    const input = nameEl.querySelector('.inline-name-input');
    const saveBtn = nameEl.querySelector('.inline-name-save');
    const cancelBtn = nameEl.querySelector('.inline-name-cancel');

    input.focus();
    input.select();

    const restore = () => {
        nameEl.dataset.editing = '';
        nameEl.innerHTML = `${currentName} ${selfHtml} <i class="fas fa-edit btn-edit-name" onclick="editUserName('${email}', '${currentName}', '${currentRole}')" title="Ubah Nama"></i>`;
    };

    cancelBtn.onclick = (e) => { e.stopPropagation(); restore(); };

    const doSave = async () => {
        const newName = input.value.trim();
        if (!newName || newName === currentName) { restore(); return; }

        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        saveBtn.disabled = true;

        try {
            await databaseManager.upsertUserConfig(email, newName, currentRole);
            showToast('Nama user berhasil diperbarui', 'success');
            renderAdminPanel();
        } catch (err) {
            console.error(err);
            showToast('Gagal mengubah nama', 'error');
            restore();
        }
    };

    saveBtn.onclick = (e) => { e.stopPropagation(); doSave(); };
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doSave();
        if (e.key === 'Escape') restore();
    });
};

// ==================== IMPORT EXCEL ====================

window.importExcel = async function (event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!window.databaseManager || !tableManager) {
        showToast('Sistem belum siap untuk import.', 'error');
        return;
    }

    try {
        showToast('Membaca file Excel...', 'info');
        const buffer = await file.arrayBuffer();
        const workbook = XLSX.read(buffer, { type: 'array' });

        const selectedSheetName = await new Promise((resolve) => {
            if (workbook.SheetNames.length === 1) {
                resolve(workbook.SheetNames[0]);
                return;
            }

            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.style.zIndex = '9999';

            let sheetOptions = '';
            workbook.SheetNames.forEach((name, i) => {
                sheetOptions += `<option value="${i}">${i + 1}. ${name}</option>`;
            });

            overlay.innerHTML = `
                <div class="modal-card" style="max-width:400px; text-align: left;">
                    <div class="modal-header">
                        <h3 style="margin:0; font-size:1.1rem; color:var(--text-primary);"><i class="fas fa-file-excel" style="color:#d32f2f; margin-right:8px;"></i>Pilih Sheet Excel</h3>
                        <button class="modal-close" id="closeSheetModal"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="modal-body" style="padding: 20px;">
                        <p style="margin-top:0; margin-bottom: 15px; font-size: 0.9rem; color:var(--text-secondary);">File Excel ini memiliki <strong>${workbook.SheetNames.length} sheet</strong>. Silakan pilih sheet mana yang ingin di-import ke worksheet saat ini:</p>
                        <select id="sheetSelect" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--bg-primary); color: var(--text-primary); outline: none; font-size:0.9rem;">
                            ${sheetOptions}
                        </select>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-modal-cancel" id="cancelSheetModal">Batal</button>
                        <button class="btn-modal-confirm" id="confirmSheetModal" style="background:#d32f2f;"><i class="fas fa-file-import"></i> Import Sheet</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);

            const cleanup = () => {
                if (document.body.contains(overlay)) document.body.removeChild(overlay);
                event.target.value = '';
                resolve(null);
            };

            overlay.querySelector('#closeSheetModal').onclick = cleanup;
            overlay.querySelector('#cancelSheetModal').onclick = cleanup;
            overlay.querySelector('#confirmSheetModal').onclick = () => {
                const idx = parseInt(overlay.querySelector('#sheetSelect').value);
                const name = workbook.SheetNames[idx];
                if (document.body.contains(overlay)) document.body.removeChild(overlay);
                resolve(name);
            };
        });

        if (!selectedSheetName) {
            showToast('Import dibatalkan.', 'info');
            return;
        }
        showToast(`Memproses sheet: ${selectedSheetName}`, 'info');
        const worksheet = workbook.Sheets[selectedSheetName];

        // Membaca data sebagai Array of Arrays (agar bisa cari header di baris acak)
        const rawDataArray = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        if (!rawDataArray || rawDataArray.length === 0) {
            showToast('File Excel kosong atau format tidak sesuai.', 'warning');
            return;
        }

        // 1. Definisikan kolom yang diharapkan dan aliasnya (huruf besar semua untuk pencocokan)
        const expectedColumns = [
            'TANGGAL', 'NAMA', 'AWB', 'AWB SISTEM', 'PENGIRIM', 'SALES',
            'PENERIMA', 'SERVICE', 'VIA', 'AKTUAL', 'VOL', 'UNIT',
            'P', 'L', 'T', 'KOIL', 'KOLI', 'HARGA', 'HARGA PERKILO', 'SURCHARGE', 'PACKING',
            'HANDLING', 'NILAI BARANG', 'ASAL PICK UP', 'JENIS BARANG',
            'TUJUAN', 'NAMA VENDOR', 'NAMA VENDOR I', 'NAMA VENDOR II', 'NAMA VENDOR III',
            'NAMA VENDOR IV', 'VENDOR I', 'VENDOR II', 'VENDOR III', 'VENDOR IV',
            'HARGA VENDOR I', 'HARGA VENDOR II', 'HARGA VENDOR III', 'HARGA VENDOR IV',
            'OPS', 'PENJUALAN', 'TOTAL BIAYA', 'PROFIT', 'IDX PROFIT',
            'PENJUALAN ASURANSI', 'MODAL ASURANSI', 'ASURANSI', 'ASURANSI JASINDO'
        ];

        let mappingKolom = {};
        let barisMulaiData = -1;

        // 2. Cari Baris Header secara Dinamis
        for (let i = 0; i < rawDataArray.length; i++) {
            const baris = rawDataArray[i];
            if (!baris || !Array.isArray(baris)) continue;

            // Konversi seluruh nilai di baris menjadi uppercase string untuk dicocokkan
            const barisString = baris.map(cell => cell ? String(cell).toString().trim().toUpperCase() : '');

            // Jika menemukan minimal salah satu dari kolom utama ini, kita asumsikan ini adalah header
            if (barisString.includes('TANGGAL') || barisString.includes('PICKUP') || barisString.includes('PICK UP') || barisString.includes('NAMA') || barisString.includes('SYSTEM') || barisString.includes('IP PERUSAHAAN') || barisString.includes('AWB')) {
                // Petakan index masing-masing kolom yang diharapkan
                expectedColumns.forEach(kolomSistem => {
                    let indexDiExcel = barisString.indexOf(kolomSistem);
                    if (kolomSistem === 'TANGGAL' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('PICKUP');
                        if (indexDiExcel === -1) {
                            indexDiExcel = barisString.indexOf('PICK UP');
                        }
                    }
                    if (kolomSistem === 'NAMA' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('SYSTEM');
                        if (indexDiExcel === -1) {
                            indexDiExcel = barisString.indexOf('IP PERUSAHAAN');
                        }
                    }
                    if (kolomSistem === 'PENGIRIM' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('CUSTOMER');
                        if (indexDiExcel === -1) {
                            indexDiExcel = barisString.indexOf('NAMA PENGIRIM');
                        }
                    }
                    if (kolomSistem === 'NAMA VENDOR I' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('NAMA VENDOR');
                    }
                    if (kolomSistem === 'HARGA VENDOR I' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('VENDOR I');
                    }
                    if (kolomSistem === 'HARGA VENDOR II' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('VENDOR II');
                    }
                    if (kolomSistem === 'HARGA VENDOR III' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('VENDOR III');
                    }
                    if (kolomSistem === 'HARGA VENDOR IV' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('VENDOR IV');
                    }
                    if (kolomSistem === 'HARGA PERKILO' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('HARGA');
                        if (indexDiExcel === -1) indexDiExcel = barisString.indexOf('TARIF');
                        if (indexDiExcel === -1) indexDiExcel = barisString.indexOf('HARGA/KG');
                        if (indexDiExcel === -1) indexDiExcel = barisString.indexOf('HARGA /KG');
                    }
                    if (kolomSistem === 'KOLI' && indexDiExcel === -1) {
                        indexDiExcel = barisString.indexOf('KOIL');
                    }
                    if (indexDiExcel !== -1) {
                        mappingKolom[kolomSistem] = indexDiExcel;
                    }
                });

                barisMulaiData = i + 1; // Data dimulai persis di bawah baris header
                break;
            }
        }

        if (barisMulaiData === -1) {
            showToast('Format Excel tidak dikenali. Pastikan ada kolom TANGGAL, PICKUP, NAMA, atau AWB.', 'error');
            return;
        }

        // Cek kolom kritikal
        let missingCritical = [];
        if (mappingKolom['HARGA PERKILO'] === undefined) missingCritical.push('HARGA / TARIF');
        if (mappingKolom['AKTUAL'] === undefined) missingCritical.push('AKTUAL');
        
        if (missingCritical.length > 0) {
            showToast(`Peringatan: Kolom ${missingCritical.join(', ')} tidak ditemukan di Baris Header Excel! Perhitungan mungkin menjadi 0.`, 'warning');
        }

        showToast(`Header ditemukan. Memproses data...`, 'info');

        const newRows = [];
        const sheetId = window.activeSheetId || 1;

        // Build reverse mapping from Excel column index to Web App column letter dynamically
        const excelColToWebCol = {};
        const headerToField = {};
        const fieldsToExtract = [
            { field: 'tanggal_pickup', kol: 'TANGGAL' },
            { field: 'nama', kol: 'NAMA' }, { field: 'nama', kol: 'IP PERUSAHAAN' }, { field: 'nama', kol: 'SYSTEM' }, { field: 'nama', kol: 'CUSTOMER' },
            { field: 'awb', kol: 'AWB' }, { field: 'awb_sistem', kol: 'AWB SISTEM' },
            { field: 'pengirim', kol: 'PENGIRIM' }, { field: 'sales', kol: 'SALES' },
            { field: 'penerima', kol: 'PENERIMA' }, { field: 'service', kol: 'SERVICE' }, { field: 'via', kol: 'VIA' },
            { field: 'aktual', kol: 'AKTUAL' }, { field: 'vol', kol: 'VOL' }, { field: 'unit', kol: 'UNIT' },
            { field: 'kubik', kol: 'KUBIK' },
            { field: 'p', kol: 'P' }, { field: 'l', kol: 'L' }, { field: 't', kol: 'T' },
            { field: 'koil', kol: 'KOLI' }, { field: 'koil', kol: 'KOIL' },
            { field: 'harga', kol: 'HARGA PERKILO' }, { field: 'harga', kol: 'HARGA' },
            { field: 'surcharge', kol: 'SURCHARGE' }, { field: 'packing', kol: 'PACKING' },
            { field: 'handling', kol: 'HANDLING' }, { field: 'nilai_barang', kol: 'NILAI BARANG' },
            { field: 'asal_pickup', kol: 'ASAL PICK UP' }, { field: 'jenis_barang', kol: 'JENIS BARANG' },
            { field: 'tujuan', kol: 'TUJUAN' },
            { field: 'nama_vendor', kol: 'NAMA VENDOR I' }, { field: 'nama_vendor', kol: 'NAMA VENDOR' },
            { field: 'nama_vendor_ii', kol: 'NAMA VENDOR II' },
            { field: 'nama_vendor_iii', kol: 'NAMA VENDOR III' },
            { field: 'nama_vendor_iv', kol: 'NAMA VENDOR IV' },
            { field: 'vendor_i', kol: 'HARGA VENDOR I' }, { field: 'vendor_i', kol: 'VENDOR I' },
            { field: 'vendor_ii', kol: 'HARGA VENDOR II' }, { field: 'vendor_ii', kol: 'VENDOR II' },
            { field: 'vendor_iii', kol: 'HARGA VENDOR III' }, { field: 'vendor_iii', kol: 'VENDOR III' },
            { field: 'vendor_iv', kol: 'HARGA VENDOR IV' }, { field: 'vendor_iv', kol: 'VENDOR IV' },
            { field: 'ops', kol: 'OPS' },
            { field: 'penjualan', kol: 'PENJUALAN' }, { field: 'total_biaya', kol: 'TOTAL BIAYA' },
            { field: 'profit', kol: 'PROFIT' }, { field: 'idx_profit', kol: 'IDX PROFIT' },
            { field: 'asuransi', kol: 'PENJUALAN ASURANSI' }, { field: 'asuransi', kol: 'ASURANSI' },
            { field: 'asuransi_jasindo', kol: 'MODAL ASURANSI' }, { field: 'asuransi_jasindo', kol: 'ASURANSI JASINDO' }
        ];

        fieldsToExtract.forEach(item => headerToField[item.kol] = item.field);

        Object.entries(mappingKolom).forEach(([header, excelIdx]) => {
            const field = headerToField[header];
            if (field && window.formulaEngine) {
                const webColIdx = window.formulaEngine.colToField.indexOf(field); // 1-based index
                if (webColIdx !== -1) {
                    let c = webColIdx;
                    let letter = '';
                    while (c > 0) {
                        let mod = (c - 1) % 26;
                        letter = String.fromCharCode(65 + mod) + letter;
                        c = Math.floor((c - mod) / 26);
                    }
                    excelColToWebCol[excelIdx] = letter;
                }
            }
        });

        // 3. Ekstrak Data mulai dari baris setelah header
        for (let i = barisMulaiData; i < rawDataArray.length; i++) {
            const row = rawDataArray[i];
            if (!row || row.length === 0) continue; // Skip baris kosong sepenuhnya

            // Cek apakah ini baris header tabel rekap di bawah (contoh: mengandung OMZET / POD)
            // Jika iya, maka hentikan proses import agar data rekap tidak ikut masuk
            const rowStrForCheck = row.map(cell => cell ? String(cell).toString().trim().toUpperCase() : '');
            if (rowStrForCheck.includes('OMZET') || (rowStrForCheck.includes('NO') && rowStrForCheck.includes('NAMA CUSTOMER') && rowStrForCheck.includes('POD'))) {
                showToast('Tabel rekap ditemukan, mengabaikan baris sisanya...', 'info');
                break;
            }

            // Helper function untuk mengambil data dengan aman berdasarkan mapping
            const getVal = (namaKolom) => {
                const idx = mappingKolom[namaKolom];
                if (idx !== undefined && row[idx] !== undefined) {
                    return row[idx];
                }
                return '';
            };

            const tglRaw = getVal('TANGGAL');
            let tgl = null;
            if (typeof tglRaw === 'number') {
                const d = new Date(Math.round((tglRaw - 25569) * 86400 * 1000));
                const yyyy = d.getUTCFullYear();
                const mm = String(d.getUTCMonth() + 1).padStart(2, '0');
                const dd = String(d.getUTCDate()).padStart(2, '0');
                tgl = `${yyyy}-${mm}-${dd}`;
            } else {
                const rawStr = String(tglRaw || '').trim();
                if (rawStr && window.formulaEngine) {
                    const parsed = window.formulaEngine._parseDate(rawStr);
                    if (parsed && !isNaN(parsed.getTime())) {
                        const yyyy = parsed.getFullYear();
                        const mm = String(parsed.getMonth() + 1).padStart(2, '0');
                        const dd = String(parsed.getDate()).padStart(2, '0');
                        tgl = `${yyyy}-${mm}-${dd}`;
                    }
                }
            }

            const nm = String(getVal('NAMA') || '').trim();
            const awb = String(getVal('AWB') || '').trim();

            // Minimal data required: Lewati jika ketiga kolom penting ini kosong
            if (!tgl && !nm && !awb) continue;

            // Helper function to robustly parse numbers that might have commas/formatting
            const parseNum = (val) => {
                if (val === null || val === undefined || val === '') return '';
                if (typeof val === 'number') return val;
                let str = String(val).replace(/[^0-9.,-]/g, '');
                if (str === '') return '';

                const numCommas = (str.match(/,/g) || []).length;
                const numDots = (str.match(/\./g) || []).length;
                const lastComma = str.lastIndexOf(',');
                const lastDot = str.lastIndexOf('.');

                if (numDots > 0 && numCommas > 0) {
                    if (lastComma > lastDot) {
                        str = str.replace(/\./g, '').replace(',', '.');
                    } else {
                        str = str.replace(/,/g, '');
                    }
                } else if (numCommas > 0 && numDots === 0) {
                    if (/^-?(\d+)(,\d{3})+$/.test(str)) {
                        str = str.replace(/,/g, ''); 
                    } else {
                        str = str.replace(',', '.'); 
                    }
                } else if (numDots > 0 && numCommas === 0) {
                    if (/^-?(\d+)(\.\d{3})+$/.test(str)) {
                        str = str.replace(/\./g, ''); 
                    }
                }
                
                const parsed = parseFloat(str);
                return isNaN(parsed) ? '' : parsed;
            };

            const parseIntEmpty = (val) => {
                if (val === null || val === undefined || val === '') return '';
                const parsed = parseInt(val);
                return isNaN(parsed) ? '' : parsed;
            };

            const newRow = {
                sheet_id: sheetId,
                tanggal_pickup: tgl,
                nama: nm,
                awb: awb,
                awb_sistem: String(getVal('AWB SISTEM') || ''),
                pengirim: String(getVal('PENGIRIM') || ''),
                sales: String(getVal('SALES') || ''),
                penerima: String(getVal('PENERIMA') || ''),
                service: String(getVal('SERVICE') || ''),
                via: String(getVal('VIA') || ''),
                aktual: parseNum(getVal('AKTUAL')),
                vol: parseNum(getVal('VOL')),
                unit: parseIntEmpty(getVal('UNIT')),
                p: parseNum(getVal('P')),
                l: parseNum(getVal('L')),
                t: parseNum(getVal('T')),
                koil: parseIntEmpty(getVal('KOLI')),
                harga: parseNum(getVal('HARGA PERKILO')),
                surcharge: parseNum(getVal('SURCHARGE')),
                packing: parseNum(getVal('PACKING')),
                handling: parseNum(getVal('HANDLING')),
                nilai_barang: parseNum(getVal('NILAI BARANG')),
                asal_pickup: String(getVal('ASAL PICK UP') || ''),
                jenis_barang: String(getVal('JENIS BARANG') || ''),
                tujuan: String(getVal('TUJUAN') || ''),
                nama_vendor: String(getVal('NAMA VENDOR I') || ''),
                nama_vendor_ii: String(getVal('NAMA VENDOR II') || ''),
                nama_vendor_iii: String(getVal('NAMA VENDOR III') || ''),
                nama_vendor_iv: String(getVal('NAMA VENDOR IV') || ''),
                vendor_i: parseNum(getVal('HARGA VENDOR I')),
                vendor_ii: parseNum(getVal('HARGA VENDOR II')),
                vendor_iii: parseNum(getVal('HARGA VENDOR III')),
                vendor_iv: parseNum(getVal('HARGA VENDOR IV')),
                ops: parseNum(getVal('OPS')),
                penjualan: parseNum(getVal('PENJUALAN')),
                total_biaya: parseNum(getVal('TOTAL BIAYA')),
                profit: parseNum(getVal('PROFIT')),
                idx_profit: parseNum(getVal('IDX PROFIT')),
                asuransi: parseNum(getVal('PENJUALAN ASURANSI')) || parseNum(getVal('ASURANSI')),
                asuransi_jasindo: parseNum(getVal('MODAL ASURANSI')) || parseNum(getVal('ASURANSI JASINDO'))
            };

            // Extract formulas and comments directly from worksheet cell objects
            let rawFormulas = {};
            let rawComments = {};

            fieldsToExtract.forEach(item => {
                const idx = mappingKolom[item.kol];
                if (idx !== undefined) {
                    const cellAddress = XLSX.utils.encode_cell({ c: idx, r: i });
                    const cell = worksheet[cellAddress];
                    if (cell) {
                        if (cell.f) rawFormulas[item.field] = cell.f;
                        if (cell.c && cell.c.length > 0) rawComments[item.field] = cell.c.map(c => c.t).join('\\n');
                    }
                }
            });

            const isMissing = (colName) => mappingKolom[colName] === undefined;

            // Jika kolom pendukung tidak ada di file, jangan simpan nilai mentahnya agar dihitung ulang otomatis
            if (isMissing('HARGA PERKILO') && isMissing('SURCHARGE') && isMissing('PACKING') && isMissing('HANDLING')) {
                newRow.penjualan = 0;
                delete rawFormulas['penjualan'];
            }

            if (isMissing('HARGA VENDOR I') && isMissing('OPS')) {
                newRow.total_biaya = 0;
                delete rawFormulas['total_biaya'];
            }

            if (isMissing('HARGA PERKILO') && isMissing('HARGA VENDOR I')) {
                newRow.profit = 0;
                delete rawFormulas['profit'];
                newRow.idx_profit = 0;
                delete rawFormulas['idx_profit'];
            }

            newRow._excelRowNum = i + 1; // Store original excel row number
            newRow._rawFormulas = rawFormulas;
            newRow._rawComments = rawComments;

            newRows.push(newRow);
        }

        if (newRows.length === 0) {
            showToast('Tidak ada baris data valid untuk di-import.', 'warning');
            return;
        }

        // Cari baris kosong di tabel saat ini untuk ditimpa
        const bulkUpdateData = [];
        const rowsToInsert = [];

        const currentTableData = window.tableManager ? window.tableManager.currentData : [];

        // Kumpulkan baris kosong yang tersedia (memiliki ID tapi datanya kosong)
        const availableEmptyRows = currentTableData.filter(row => {
            return row.id && !String(row.awb || '').trim() && !String(row.nama || '').trim() && !String(row.tanggal_pickup || '').trim() && row.nama !== '__SHEET_CONFIG__';
        });

        const processFormulasForTargetRow = (newRow, targetRowNumber) => {
            let finalFormulas = {};
            const rowShift = targetRowNumber - newRow._excelRowNum;

            Object.entries(newRow._rawFormulas || {}).forEach(([field, excelFormula]) => {
                let hasUnmappedColumn = false;
                let shiftedFormula = excelFormula.replace(/([A-Z]+)(\d+)/g, (match, col, rowNum) => {
                    let cIdx = 0;
                    for (let ci = 0; ci < col.length; ci++) {
                        cIdx = cIdx * 26 + (col.charCodeAt(ci) - 64);
                    }
                    const excelIdx = cIdx - 1;
                    let newCol = excelColToWebCol[excelIdx];

                    if (!newCol) {
                        hasUnmappedColumn = true;
                        return match; // return original, but we'll discard it anyway
                    }
                    return newCol + Math.max(1, parseInt(rowNum) + rowShift);
                });

                if (hasUnmappedColumn) {
                    // Jika formula mengandung kolom yang tidak ter-map (misal kolom 'Catatan' di Excel), buang rumusnya agar tidak error
                    return;
                }

                let formulaStr = '=' + shiftedFormula;

                // Filter out auto-calc formulas to allow the web system's formula engine to take over automatically
                const fStrip = formulaStr.replace(/\s+/g, '').toUpperCase();
                const r = targetRowNumber;
                let isAutoCalc = false;

                // Get current sheet config to check if AutoCalc is explicitly disabled for a column
                const config = window.tableManager?.sheetConfig || {};
                const isAutoCalcEnabled = (fld) => {
                    const cfg = config[fld] || { autoCalc: true };
                    return cfg.autoCalc !== false;
                };

                if (field === 'kubik' && isAutoCalcEnabled('kubik') && (fStrip === `=((N${r}*O${r}*P${r})/1000000)` || fStrip === `=(N${r}*O${r}*P${r})/1000000`)) isAutoCalc = true;
                if (field === 'idx_profit' && isAutoCalcEnabled('idx_profit') && fStrip === `=IFERROR(AJ${r}/V${r},0)`) isAutoCalc = true;
                if (field === 'asuransi' && isAutoCalcEnabled('asuransi') && fStrip === `=AM${r}*0.002`) isAutoCalc = true;
                if (field === 'asuransi_jasindo' && isAutoCalcEnabled('asuransi_jasindo') && fStrip === `=AM${r}*0.001`) isAutoCalc = true;
                if (field === 'total_biaya' && isAutoCalcEnabled('total_biaya') && fStrip === `=AD${r}+AE${r}+AF${r}+AG${r}+AH${r}`) isAutoCalc = true;
                if (field === 'penjualan' && isAutoCalcEnabled('penjualan') && fStrip.includes(`MAX(J${r},K${r})*R${r}`)) isAutoCalc = true;

                if (!isAutoCalc) {
                    finalFormulas[field] = formulaStr;
                }
            });

            if (Object.keys(finalFormulas).length > 0 || Object.keys(newRow._rawComments || {}).length > 0) {
                if (Object.keys(newRow._rawComments || {}).length > 0) finalFormulas.__comments = newRow._rawComments;
                newRow.formulas = JSON.stringify(finalFormulas);
            }

            delete newRow._excelRowNum;
            delete newRow._rawFormulas;
            delete newRow._rawComments;
        };

        const filterByPermission = (rowData) => {
            if (!window.tableManager) return rowData;
            const filtered = {};
            const internalFields = ['sheet_id', '_excelRowNum', '_rawFormulas', '_rawComments', 'formulas', 'id'];

            Object.keys(rowData).forEach(key => {
                if (internalFields.includes(key)) {
                    filtered[key] = rowData[key];
                } else if (typeof window.tableManager.isColEditable === 'function' && window.tableManager.isColEditable(key)) {
                    filtered[key] = rowData[key];
                }
            });
            return filtered;
        };

        for (let i = 0; i < newRows.length; i++) {
            let currentRow = newRows[i];
            let awbToMatch = String(currentRow.awb || '').trim();

            // 1. Cari apakah AWB sudah ada di tabel (Merge by AWB)
            let existingRow = null;
            if (awbToMatch !== '') {
                existingRow = currentTableData.find(r => String(r.awb || '').trim() === awbToMatch && r.nama !== '__SHEET_CONFIG__');
            }

            // 2. Fallback: Gabungkan berdasarkan nomor baris berurutan (Row Index 1 ke Baris 1, dst)
            // Ini untuk mengakomodasi PIC Keuangan yang import file Excel tanpa kolom AWB.
            if (!existingRow) {
                const targetRowByIndex = currentTableData[i];
                if (targetRowByIndex && targetRowByIndex.nama !== '__SHEET_CONFIG__') {
                    existingRow = targetRowByIndex;
                }
            }

            if (existingRow) {
                // MERGE / UPDATE DATA EXISTING
                const targetRowNumber = currentTableData.indexOf(existingRow) + 1;
                processFormulasForTargetRow(currentRow, targetRowNumber);

                if (window.calculationsManager) {
                    currentRow = window.calculationsManager.calculateRow(currentRow);
                }

                // Filter kolom berdasarkan hak akses PIC
                const allowedUpdates = filterByPermission(currentRow);

                // Gabungkan data lama dengan update baru yang diizinkan
                const mergedData = { ...existingRow, ...allowedUpdates };

                bulkUpdateData.push({
                    id: existingRow.id,
                    oldData: existingRow,
                    updates: mergedData
                });
            } else {
                // INSERT DATA BARU
                // Tetap filter hak akses agar kolom yang tidak berhak diisi jadi kosong
                currentRow = filterByPermission(currentRow);

                if (availableEmptyRows.length > 0) {
                    // Timpa baris kosong yang ada
                    const emptyRow = availableEmptyRows.shift();
                    const targetRowNumber = currentTableData.indexOf(emptyRow) + 1;
                    processFormulasForTargetRow(currentRow, targetRowNumber);

                    if (window.calculationsManager) {
                        currentRow = window.calculationsManager.calculateRow(currentRow);
                    }

                    const mergedData = { ...emptyRow, ...currentRow };

                    bulkUpdateData.push({
                        id: emptyRow.id,
                        oldData: emptyRow,
                        updates: mergedData
                    });
                } else {
                    // Insert baris baru di paling bawah
                    const targetRowNumber = currentTableData.length + rowsToInsert.length + 1;
                    processFormulasForTargetRow(currentRow, targetRowNumber);

                    if (window.calculationsManager) {
                        currentRow = window.calculationsManager.calculateRow(currentRow);
                    }

                    rowsToInsert.push(currentRow);
                }
            }
        }

        let totalSuccess = 0;
        showToast(`Memproses ${bulkUpdateData.length} update dan ${rowsToInsert.length} baris baru...`, 'info');

        // 1. Jalankan Bulk Update (Menimpa baris kosong)
        if (bulkUpdateData.length > 0) {
            try {
                const updatedRows = await window.databaseManager.updateRowsBulk(bulkUpdateData);
                if (updatedRows) {
                    const successCount = updatedRows.filter(r => r.success).length;
                    const failCount = updatedRows.length - successCount;
                    totalSuccess += successCount;
                    if (failCount > 0) {
                        console.warn(`Import: ${failCount} dari ${updatedRows.length} update gagal.`);
                    }
                }
            } catch (err) {
                console.error("Gagal melakukan update baris kosong:", err);
            }
        }

        // 2. Jalankan Bulk Insert (Jika ada sisa data baru)
        if (rowsToInsert.length > 0) {
            try {
                const insertedRows = await window.databaseManager.insertRowsBulk(rowsToInsert);
                if (insertedRows) totalSuccess += insertedRows.length;
            } catch (err) {
                console.error("Gagal menambahkan baris baru:", err);
            }
        }

        if (totalSuccess > 0) {
            showToast(`Berhasil import ${totalSuccess} baris data baru!`, 'success');
            // Refresh table agar data baru tampil dengan memaksa ambil dari database
            if (typeof loadAllData === 'function') {
                _dataLoaded = false; // Reset status load
                await loadAllData();
            } else {
                // Fallback reload halaman jika loadAllData tidak tersedia
                setTimeout(() => window.location.reload(), 1500);
            }
        } else {
            showToast('Gagal menyimpan data import ke database.', 'error');
        }

    } catch (err) {
        console.error('Error importing Excel:', err);
        showToast('Terjadi kesalahan saat membaca file Excel: ' + (err.message || err) + '. Pastikan format sesuai.', 'error');
    } finally {
        event.target.value = '';
    }
};
