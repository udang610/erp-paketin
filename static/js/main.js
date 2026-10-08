/**
 * CRM Paketin Cargo - Main JavaScript
 * Handles sidebar toggle, auto-dismiss alerts, and UI interactions.
 */
document.addEventListener('DOMContentLoaded', function () {

    // ─── Sidebar Toggle ─────────────────────────
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const body = document.body;

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            if (window.innerWidth < 992) {
                sidebar.classList.toggle('show');
            } else {
                body.classList.toggle('sidebar-collapsed');
            }
        });

        // Close sidebar on outside click (mobile)
        document.addEventListener('click', function (e) {
            if (window.innerWidth < 992 && sidebar.classList.contains('show')) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }

    // ─── Auto-dismiss alerts ────────────────────
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });


    // ─── Confirm Delete & Action Forms ─────────────────────────
    const deleteForms = document.querySelectorAll('form[data-confirm]');
    deleteForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (form.dataset.confirmed === 'true') {
                return; // already confirmed
            }
            e.preventDefault();
            const message = form.getAttribute('data-confirm') || 'Apakah Anda yakin ingin melanjutkan tindakan ini?';
            if (window.PaketinModal) {
                window.PaketinModal.confirm({
                    title: 'Konfirmasi Tindakan',
                    description: message,
                    theme: 'danger',
                    confirmText: 'Lanjutkan',
                    cancelText: 'Batal'
                }).then(function(confirmed) {
                    if (confirmed) {
                        form.dataset.confirmed = 'true';
                        form.submit();
                    }
                });
            } else if (confirm(message)) {
                form.dataset.confirmed = 'true';
                form.submit();
            }
        });
    });

    // ─── Tooltip initialization ─────────────────
    // Set field date default to today for all type="date" inputs
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(function(el) {
        if (!el.value) {
            el.value = today;
        }
    });

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

    // ─── Reminder Notification System ───────────
    // Sound system with robust autoplay policy handling
    let notifAudioUnlocked = false;
    let notifAudioElement = null;
    let notifAudioBuffer = null;
    let notifAudioCtx = null;

    // Preload notification sound on page load
    function preloadNotificationSound() {
        try {
            notifAudioElement = new Audio('/static/notif.wav');
            notifAudioElement.preload = 'auto';
            notifAudioElement.volume = 1.0;
            notifAudioElement.loop = true;
            notifAudioElement.load();

            // Also preload via Web Audio API as fallback
            notifAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            fetch('/static/notif.wav')
                .then(r => r.arrayBuffer())
                .then(buf => notifAudioCtx.decodeAudioData(buf))
                .then(decoded => { notifAudioBuffer = decoded; })
                .catch(() => {}); // Silently fail for Web Audio fallback
        } catch (e) {
            console.log('Audio preload warning:', e);
        }
    }
    preloadNotificationSound();

    // Unlock audio on ANY user interaction (click, touch, key, scroll)
    function unlockAudio() {
        if (notifAudioUnlocked) return;
        notifAudioUnlocked = true;

        // Resume AudioContext if suspended
        if (notifAudioCtx && notifAudioCtx.state === 'suspended') {
            notifAudioCtx.resume();
        }

        // Play silent audio to unlock the element
        if (notifAudioElement) {
            const originalVol = notifAudioElement.volume;
            notifAudioElement.volume = 0;
            notifAudioElement.loop = false;
            const p = notifAudioElement.play();
            if (p) {
                p.then(() => {
                    notifAudioElement.pause();
                    notifAudioElement.currentTime = 0;
                    notifAudioElement.volume = originalVol;
                    notifAudioElement.loop = true;
                }).catch(() => {
                    notifAudioElement.volume = originalVol;
                    notifAudioElement.loop = true;
                    notifAudioUnlocked = false; // Retry on next interaction
                });
            }
        }
    }

    // Listen to ALL user interaction events to unlock audio
    ['click', 'touchstart', 'keydown', 'scroll', 'mousedown'].forEach(evt => {
        document.addEventListener(evt, unlockAudio, { once: false, passive: true });
    });

    // Web Audio API fallback player
    let webAudioSource = null;
    function playWithWebAudio() {
        if (!notifAudioCtx || !notifAudioBuffer) return false;
        try {
            if (notifAudioCtx.state === 'suspended') notifAudioCtx.resume();
            if (webAudioSource) { try { webAudioSource.stop(); } catch(e) {} }
            webAudioSource = notifAudioCtx.createBufferSource();
            webAudioSource.buffer = notifAudioBuffer;
            webAudioSource.loop = true;
            webAudioSource.connect(notifAudioCtx.destination);
            webAudioSource.start(0);
            return true;
        } catch (e) {
            return false;
        }
    }

    function stopWebAudio() {
        if (webAudioSource) {
            try { webAudioSource.stop(); } catch(e) {}
            webAudioSource = null;
        }
    }

    function playNotificationSound() {
        // Method 1: HTML5 Audio (primary)
        if (notifAudioElement) {
            notifAudioElement.currentTime = 0;
            notifAudioElement.volume = 1.0;
            notifAudioElement.loop = true;
            const playPromise = notifAudioElement.play();
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    // Success - HTML5 Audio is playing
                }).catch(error => {
                    console.log('HTML5 Audio blocked, trying Web Audio API...', error);
                    // Method 2: Web Audio API fallback
                    if (!playWithWebAudio()) {
                        // Both methods failed - show visual fallback
                        showSoundBlockedBanner();
                    }
                });
            }
        } else {
            // No HTML5 Audio - try Web Audio API
            if (!playWithWebAudio()) {
                showSoundBlockedBanner();
            }
        }
    }

    function stopNotificationSound() {
        if (notifAudioElement) {
            notifAudioElement.pause();
            notifAudioElement.currentTime = 0;
        }
        stopWebAudio();
        // Remove sound blocked banner if exists
        const banner = document.getElementById('soundBlockedBanner');
        if (banner) banner.remove();
    }

    function showSoundBlockedBanner() {
        // Only show once
        if (document.getElementById('soundBlockedBanner')) return;
        const banner = document.createElement('div');
        banner.id = 'soundBlockedBanner';
        banner.innerHTML = `
            <div style="position:fixed;top:0;left:0;right:0;z-index:99999;background:#dc3545;color:white;text-align:center;padding:10px 20px;font-size:0.95rem;display:flex;align-items:center;justify-content:center;gap:12px;">
                <i class="ph-duotone ph-speaker-slash" style="font-size:1.3rem;"></i>
                <span>Suara notifikasi diblokir browser. </span>
                <button onclick="retryNotifSound()" style="background:white;color:#dc3545;border:none;padding:5px 15px;border-radius:4px;cursor:pointer;font-weight:600;">
                    🔊 Aktifkan Suara
                </button>
            </div>
        `;
        document.body.appendChild(banner);
    }

    // Global function for retry button
    window.retryNotifSound = function() {
        const banner = document.getElementById('soundBlockedBanner');
        if (banner) banner.remove();
        // User clicked - audio should now be unlocked
        unlockAudio();
        setTimeout(() => playNotificationSound(), 100);
    };

    // Stop sound when user dismisses the reminder toast
    document.body.addEventListener('click', function(e) {
        if (e.target.closest('.btn-close')) {
            const alertNode = e.target.closest('.alert-dismissible');
            if (alertNode && alertNode.querySelector('.alert-heading')?.textContent === 'Reminder') {
                stopNotificationSound();
            }
        }
    });

    function checkReminders() {
        fetch('/crm/api/due-reminders/')
            .then(res => res.json())
            .then(data => {
                if (data.reminders && data.reminders.length > 0) {
                    let shouldPlaySound = false;
                    data.reminders.forEach(reminder => {
                        const key = 'reminder_notified_' + reminder.id;
                        if (!localStorage.getItem(key)) {
                            localStorage.setItem(key, 'true');
                            shouldPlaySound = true;
                            
                            // Tampilkan alert/toast yang lebih besar
                            const alertHtml = `
                            <div class="alert alert-info alert-dismissible fade show shadow-lg" role="alert" style="position:fixed; top:20px; right:20px; z-index:9999; min-width: 350px; font-size: 1.1rem; padding: 1.5rem; border-left: 5px solid #0dcaf0; background-color: #f8ffff;">
                                <div class="d-flex align-items-center">
                                    <i class="ph-duotone ph-bell-ringing me-3 text-info" style="font-size: 2.2rem;"></i>
                                    <div>
                                        <h5 class="alert-heading mb-1 text-dark fw-bold">Reminder</h5>
                                        <div class="text-dark">${reminder.title}</div>
                                    </div>
                                </div>
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" style="position: absolute; top: 8px; right: 8px; transform: scale(0.75);" title="Snooze / Tutup"></button>
                            </div>`;
                            document.body.insertAdjacentHTML('beforeend', alertHtml);
                        }
                    });
                    if (shouldPlaySound) {
                        playNotificationSound();
                    }
                }
            })
            .catch(err => console.error(err));
    }

    // Check reminders only if authenticated (sidebar exists)
    if (document.getElementById('sidebar')) {
        checkReminders(); // Cek langsung tanpa delay
        setInterval(checkReminders, 10000); // Check every 10 seconds
    }

    // ─── Custom Autocomplete untuk Nama Perusahaan ───────────
    const companyInputs = document.querySelectorAll('input[list="companyList"]');
    const datalist = document.getElementById('companyList');
    
    if (companyInputs.length > 0 && datalist) {
        const options = Array.from(datalist.options).map(opt => opt.value);
        
        companyInputs.forEach(input => {
            // Hapus atribut list agar datalist native (kotak hitam) tidak muncul
            input.removeAttribute('list');
            
            // Gunakan parent langsung sebagai penampung relative
            const parent = input.parentNode;
            parent.classList.add('position-relative');
            
            const dropdown = document.createElement('ul');
            dropdown.className = 'dropdown-menu w-100 shadow';
            dropdown.style.maxHeight = '200px';
            dropdown.style.overflowY = 'auto';
            dropdown.style.position = 'absolute';
            dropdown.style.top = '100%';
            dropdown.style.left = '0';
            dropdown.style.zIndex = '1050';
            dropdown.style.marginTop = '0.1rem';
            
            // Sisipkan dropdown ke parent
            parent.appendChild(dropdown);
            
            function showDropdown(query) {
                dropdown.innerHTML = '';
                // Jika input kosong, tampilkan semua, jika tidak, filter
                const filtered = options.filter(opt => opt.toLowerCase().includes(query.toLowerCase()));
                
                if (filtered.length === 0) {
                    dropdown.classList.remove('show');
                    return;
                }
                
                filtered.forEach(opt => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.className = 'dropdown-item text-truncate cursor-pointer';
                    a.href = '#';
                    a.textContent = opt;
                    
                    // Highlight text yang dicari
                    if (query) {
                        const regex = new RegExp(`(${query})`, "gi");
                        a.innerHTML = opt.replace(regex, "<strong>$1</strong>");
                    }
                    
                    a.addEventListener('click', function(e) {
                        e.preventDefault();
                        input.value = opt;
                        dropdown.classList.remove('show');
                    });
                    li.appendChild(a);
                    dropdown.appendChild(li);
                });
                
                // Pastikan dropdown selebar input group atau input
                dropdown.style.width = parent.offsetWidth + 'px';
                dropdown.classList.add('show');
            }
            
            // Event listeners
            input.addEventListener('focus', () => showDropdown(input.value));
            input.addEventListener('input', () => showDropdown(input.value));
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') dropdown.classList.remove('show');
            });
            
            // Sembunyikan saat klik di luar
            document.addEventListener('click', (e) => {
                if (!parent.contains(e.target)) {
                    dropdown.classList.remove('show');
                }
            });
        });
    }
    
    // ==========================================
    // Global Search (Ctrl+K)
    // ==========================================
    const searchModal = document.getElementById('globalSearchModal');
    const searchInput = document.getElementById('globalSearchInput');
    const searchResults = document.getElementById('globalSearchResults');
    const searchEmptyState = document.getElementById('globalSearchEmptyState');
    let searchTimeout;

    if (searchModal && searchInput && searchResults) {
        // Keyboard shortcut Ctrl+K
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                new bootstrap.Modal(searchModal).show();
            }
        });

        // Focus input when modal opens
        searchModal.addEventListener('shown.bs.modal', function () {
            searchInput.focus();
        });

        // Clear input when modal closes
        searchModal.addEventListener('hidden.bs.modal', function () {
            searchInput.value = '';
            searchResults.innerHTML = '';
            searchResults.appendChild(searchEmptyState);
        });

        // Search typing logic
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.appendChild(searchEmptyState);
                return;
            }

            // Loading state
            searchResults.innerHTML = `<div class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-danger mb-2" role="status"></div>
                <p class="mb-0">Mencari...</p>
            </div>`;

            searchTimeout = setTimeout(() => {
                fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        searchResults.innerHTML = '';
                        if (data.results && data.results.length > 0) {
                            data.results.forEach(item => {
                                const a = document.createElement('a');
                                a.href = item.url;
                                a.className = 'list-group-item list-group-item-action d-flex align-items-center py-3 border-0 border-bottom';
                                
                                a.innerHTML = `
                                    <div class="bg-light rounded-circle p-2 d-flex align-items-center justify-content-center me-3" style="width: 40px; height: 40px;">
                                        <i class="ph-duotone ${item.icon} text-secondary fs-5"></i>
                                    </div>
                                    <div class="flex-grow-1 min-w-0">
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <h6 class="mb-0 text-truncate">${item.title}</h6>
                                            <span class="badge bg-secondary-subtle text-secondary" style="font-size: 0.65rem;">${item.type}</span>
                                        </div>
                                        <div class="text-muted text-truncate small">${item.subtitle}</div>
                                    </div>
                                `;
                                searchResults.appendChild(a);
                            });
                        } else {
                            searchResults.innerHTML = `
                                <div class="text-center text-muted py-4">
                                    <i class="ph-duotone ph-file-dashed fs-1 mb-2 text-light"></i>
                                    <p class="mb-0">Tidak ditemukan hasil untuk "<strong>${query}</strong>"</p>
                                </div>
                            `;
                        }
                    })
                    .catch(err => {
                        console.error("Search error:", err);
                        searchResults.innerHTML = `<div class="text-center text-danger py-4">Terjadi kesalahan. Silakan coba lagi.</div>`;
                    });
            }, 300); // 300ms debounce
        });
    }
});
