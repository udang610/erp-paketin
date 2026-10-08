/**
 * Universal Confirmation & Action Modal Controller for ERP Paketin
 * Matches modern visual cue & signal emphasis UX patterns.
 */
(function(window) {
    'use strict';

    let modalInstance = null;
    let currentResolver = null;
    let targetForm = null;
    let targetActionUrl = null;
    let inputConfig = null;

    const THEMES = {
        danger: {
            iconClass: 'ph-bold ph-trash',
            ringColor: '#ef4444',
            iconBg: '#fee2e2',
            iconColor: '#ef4444',
            btnClass: 'btn-danger',
            defaultConfirm: 'Hapus'
        },
        warning: {
            iconClass: 'ph-bold ph-warning',
            ringColor: '#f59e0b',
            iconBg: '#fef3c7',
            iconColor: '#f59e0b',
            btnClass: 'btn-warning text-dark',
            defaultConfirm: 'Lanjutkan'
        },
        success: {
            iconClass: 'ph-bold ph-seal-check',
            ringColor: '#10b981',
            iconBg: '#d1fae5',
            iconColor: '#10b981',
            btnClass: 'btn-success',
            defaultConfirm: 'Konfirmasi'
        },
        info: {
            iconClass: 'ph-bold ph-info',
            ringColor: '#2563eb',
            iconBg: '#dbeafe',
            iconColor: '#2563eb',
            btnClass: 'btn-primary',
            defaultConfirm: 'OK'
        }
    };

    function getCsrfToken() {
        const input = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    function initModal() {
        const modalEl = document.getElementById('globalConfirmModal');
        if (!modalEl) return null;

        if (!modalInstance && window.bootstrap && window.bootstrap.Modal) {
            modalInstance = new bootstrap.Modal(modalEl, {
                backdrop: 'static',
                keyboard: true
            });

            const okBtn = document.getElementById('globalConfirmOkBtn');
            const cancelBtn = document.getElementById('globalConfirmCancelBtn');
            const inputContainer = document.getElementById('globalConfirmInputContainer');
            const inputTextarea = document.getElementById('globalConfirmInputTextarea');
            const inputFeedback = document.getElementById('globalConfirmInputFeedback');

            okBtn.addEventListener('click', function() {
                let val = '';
                if (inputConfig) {
                    val = (inputTextarea ? inputTextarea.value : '').trim();
                    if (inputConfig.required && !val) {
                        if (inputFeedback) inputFeedback.style.display = 'block';
                        if (inputTextarea) inputTextarea.focus();
                        return;
                    }
                }

                const resolver = currentResolver;
                currentResolver = null;

                modalInstance.hide();

                if (targetActionUrl) {
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = targetActionUrl;

                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = getCsrfToken();
                    form.appendChild(csrfInput);

                    if (inputConfig && inputConfig.name) {
                        const reasonInput = document.createElement('input');
                        reasonInput.type = 'hidden';
                        reasonInput.name = inputConfig.name;
                        reasonInput.value = val;
                        form.appendChild(reasonInput);
                    }

                    document.body.appendChild(form);
                    form.submit();
                    return;
                }

                if (targetForm) {
                    if (inputConfig && inputConfig.name) {
                        let existingInput = targetForm.querySelector(`[name="${inputConfig.name}"]`);
                        if (!existingInput) {
                            existingInput = document.createElement('input');
                            existingInput.type = 'hidden';
                            existingInput.name = inputConfig.name;
                            targetForm.appendChild(existingInput);
                        }
                        existingInput.value = val;
                    }
                    targetForm.submit();
                    targetForm = null;
                    return;
                }

                if (resolver) {
                    resolver(inputConfig ? { confirmed: true, value: val } : true);
                }
            });

            cancelBtn.addEventListener('click', function() {
                if (currentResolver) {
                    currentResolver(false);
                    currentResolver = null;
                }
                resetState();
            });

            modalEl.addEventListener('hidden.bs.modal', function() {
                if (currentResolver) {
                    currentResolver(false);
                    currentResolver = null;
                }
                resetState();
            });
        }
        return modalInstance;
    }

    function resetState() {
        targetForm = null;
        targetActionUrl = null;
        inputConfig = null;
        const inputFeedback = document.getElementById('globalConfirmInputFeedback');
        if (inputFeedback) inputFeedback.style.display = 'none';
        const inputTextarea = document.getElementById('globalConfirmInputTextarea');
        if (inputTextarea) inputTextarea.value = '';
    }

    /**
     * Show modern confirmation / prompt modal
     * @param {Object} options
     */
    function showConfirm(options = {}) {
        const modal = initModal();
        if (!modal) {
            return Promise.resolve(window.confirm(options.title || options.description || 'Konfirmasi tindakan?'));
        }

        resetState();

        const themeKey = THEMES[options.theme] ? options.theme : 'danger';
        const themeConfig = THEMES[themeKey];

        const titleEl = document.getElementById('globalConfirmTitle');
        const descEl = document.getElementById('globalConfirmDesc');
        const iconEl = document.getElementById('globalConfirmIcon');
        const iconContainer = document.getElementById('globalConfirmIconCore');
        const wrapperEl = document.getElementById('globalConfirmSignalWrapper');
        const okBtn = document.getElementById('globalConfirmOkBtn');
        const cancelBtn = document.getElementById('globalConfirmCancelBtn');

        const frictionContainer = document.getElementById('globalConfirmFrictionContainer');
        const frictionInput = document.getElementById('globalConfirmFrictionInput');

        const inputContainer = document.getElementById('globalConfirmInputContainer');
        const inputLabel = document.getElementById('globalConfirmInputLabel');
        const inputTextarea = document.getElementById('globalConfirmInputTextarea');
        const inputFeedback = document.getElementById('globalConfirmInputFeedback');

        titleEl.textContent = options.title || 'Konfirmasi Tindakan?';
        descEl.innerHTML = options.description || '';

        // Dynamic theme styling
        wrapperEl.style.color = themeConfig.ringColor;
        iconContainer.style.backgroundColor = themeConfig.iconBg;
        iconContainer.style.color = themeConfig.iconColor;
        iconContainer.style.border = `1.5px solid ${themeConfig.ringColor}40`;

        const iconClass = options.icon ? `ph-bold ${options.icon}` : themeConfig.iconClass;
        iconEl.className = iconClass;

        // Button texts & styling
        okBtn.className = `btn ${themeConfig.btnClass} w-50 py-2 fw-bold shadow-sm`;
        okBtn.textContent = options.confirmText || themeConfig.defaultConfirm;
        cancelBtn.textContent = options.cancelText || 'Batal';

        // Reason / Prompt input
        if (options.input || options.requireReason || options.reason) {
            inputConfig = typeof options.input === 'object' ? options.input : {
                name: options.inputName || 'void_reason',
                label: options.inputLabel || 'Alasan *',
                placeholder: options.inputPlaceholder || 'Masukkan alasan secara detail...',
                required: options.requireReason !== false
            };

            if (inputContainer) {
                inputContainer.style.display = 'block';
                if (inputLabel) {
                    inputLabel.innerHTML = inputConfig.label || 'Alasan *';
                }
                if (inputTextarea) {
                    inputTextarea.value = options.inputValue || '';
                    inputTextarea.placeholder = inputConfig.placeholder || 'Masukkan alasan secara detail...';
                    inputTextarea.oninput = function() {
                        if (inputFeedback && inputTextarea.value.trim().length > 0) {
                            inputFeedback.style.display = 'none';
                        }
                    };
                }
            }
        } else {
            if (inputContainer) inputContainer.style.display = 'none';
        }

        // Friction Mechanism
        if (options.frictionText && options.frictionText.trim().length > 0) {
            const requiredText = options.frictionText.trim();
            frictionContainer.style.display = 'block';
            frictionInput.value = '';
            frictionInput.placeholder = `Ketik "${requiredText}" untuk konfirmasi`;
            okBtn.disabled = true;

            frictionInput.oninput = function() {
                if (frictionInput.value.trim().toLowerCase() === requiredText.toLowerCase()) {
                    okBtn.disabled = false;
                } else {
                    okBtn.disabled = true;
                }
            };
        } else {
            frictionContainer.style.display = 'none';
            frictionInput.value = '';
            frictionInput.oninput = null;
            okBtn.disabled = false;
        }

        targetForm = options.form || null;
        targetActionUrl = options.actionUrl || null;

        return new Promise((resolve) => {
            currentResolver = resolve;
            modal.show();
            setTimeout(() => {
                if (options.input && inputTextarea) {
                    inputTextarea.focus();
                } else if (options.frictionText && frictionInput) {
                    frictionInput.focus();
                } else if (themeKey === 'danger') {
                    // UX Best practice: focus on Cancel for destructive action to prevent accidental Enter
                    cancelBtn.focus();
                } else {
                    okBtn.focus();
                }
            }, 250);
        });
    }

    // High-level PaketinModal API
    window.PaketinModal = {
        confirm: showConfirm,
        danger: (title, description, confirmText, frictionText) => showConfirm({ title, description, theme: 'danger', confirmText, frictionText }),
        warning: (title, description, confirmText) => showConfirm({ title, description, theme: 'warning', confirmText }),
        success: (title, description, confirmText) => showConfirm({ title, description, theme: 'success', confirmText }),
        info: (title, description, confirmText) => showConfirm({ title, description, theme: 'info', confirmText }),
        void: function(actionUrl, itemName, options = {}) {
            return showConfirm({
                title: options.title || 'Konfirmasi Void',
                description: `Apakah Anda yakin ingin void <strong>${itemName || ''}</strong>?<br>Tindakan ini tidak dapat dibatalkan.`,
                theme: 'danger',
                confirmText: options.confirmText || 'Konfirmasi Void',
                cancelText: 'Batal',
                icon: 'ph-warning-circle',
                actionUrl: actionUrl,
                input: {
                    name: 'void_reason',
                    label: 'Alasan Void <span class="text-danger">*</span>',
                    placeholder: 'Masukkan alasan void secara detail...',
                    required: true
                },
                ...options
            });
        },
        delete: function(actionUrl, itemName, options = {}) {
            return showConfirm({
                title: options.title || 'Hapus Data?',
                description: `Apakah Anda yakin ingin menghapus <strong>${itemName || 'data ini'}</strong> secara permanen dari daftar?`,
                theme: 'danger',
                confirmText: options.confirmText || 'Ya, Hapus',
                cancelText: 'Batal',
                icon: 'ph-trash',
                actionUrl: actionUrl,
                ...options
            });
        }
    };

    // Global Compatibility Bridges (for legacy calls across operations/master templates)
    window.showVoidModal = function(actionUrl, itemName) {
        window.PaketinModal.void(actionUrl, itemName);
    };

    window.showHideModal = function(actionUrl) {
        window.PaketinModal.delete(actionUrl, 'data void ini');
    };

    window.showDeleteModal = function(actionUrl, itemName) {
        window.PaketinModal.delete(actionUrl, itemName);
    };

    window.showDeleteMasterModal = function(actionUrl, itemName) {
        window.PaketinModal.delete(actionUrl, itemName, {
            title: 'Hapus Data Master?',
            description: `Apakah Anda yakin ingin menghapus data <strong>${itemName || ''}</strong>?<br><span class="text-danger small fw-semibold">Data yang dihapus akan hilang permanen dari database.</span>`
        });
    };

    // Auto bind data-attributes
    document.addEventListener('DOMContentLoaded', function() {
        document.addEventListener('click', function(e) {
            const trigger = e.target.closest('[data-paketin-confirm]');
            if (!trigger) return;

            e.preventDefault();
            e.stopPropagation();

            const title = trigger.getAttribute('data-confirm-title') || trigger.getAttribute('data-paketin-confirm') || 'Konfirmasi Tindakan?';
            const description = trigger.getAttribute('data-confirm-desc') || '';
            const theme = trigger.getAttribute('data-confirm-theme') || 'danger';
            const confirmText = trigger.getAttribute('data-confirm-btn') || 'Konfirmasi';
            const cancelText = trigger.getAttribute('data-cancel-btn') || 'Batal';
            const frictionText = trigger.getAttribute('data-confirm-friction') || '';
            const icon = trigger.getAttribute('data-confirm-icon') || '';

            const form = trigger.closest('form');

            showConfirm({
                title,
                description,
                theme,
                confirmText,
                cancelText,
                frictionText,
                icon,
                form: form || null
            }).then((confirmed) => {
                if (confirmed && trigger.tagName === 'A' && trigger.href && !trigger.href.startsWith('javascript:')) {
                    window.location.href = trigger.href;
                }
            });
        });
    });

})(window);
