import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-for-dev-only')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = list(set(list(config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())) + ['localhost', '127.0.0.1', 'testserver']))

INSTALLED_APPS = [
    'unfold',  # Must be before django.contrib.admin
    'unfold.contrib.filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.organizations',
    'apps.employees',
    'apps.crm',
    'apps.finance',
    'apps.operations',
    'apps.master',
    'apps.hr.attendance',
    'apps.hr.leave',
    'apps.hr.approvals',
    'apps.hr.documents',
    'apps.hr.payroll',
    'apps.hr.asset_request',
    'apps.notifications',
    'apps.audit',
]

AUTH_USER_MODEL = 'accounts.User'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ─── Django Unfold Admin Theme ───
UNFOLD = {
    "SITE_TITLE": "Paketin Cargo",
    "SITE_HEADER": "Paketin Admin",
    "SITE_SUBHEADER": "ERP Administration Panel",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "STYLES": [
        lambda request: "/static/css/admin_custom.css",
    ],
    "COLORS": {
        "primary": {
            "50": "#fef2f2",
            "100": "#fee2e2",
            "200": "#fecaca",
            "300": "#fca5a5",
            "400": "#f87171",
            "500": "#ed1c2e",
            "600": "#dc2626",
            "700": "#b91c1c",
            "800": "#991b1b",
            "900": "#7f1d1d",
            "950": "#450a0a",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Pengguna & Akses",
                "separator": True,
                "items": [
                    {
                        "title": "Pengguna",
                        "icon": "person",
                        "link": "/admin/accounts/user/",
                    },
                    {
                        "title": "Roles",
                        "icon": "shield_person",
                        "link": "/admin/accounts/role/",
                    },
                    {
                        "title": "Izin Menu",
                        "icon": "lock_open",
                        "link": "/admin/accounts/menupermission/",
                    },
                    {
                        "title": "Pengaturan Visibilitas Menu",
                        "icon": "visibility",
                        "link": "/admin/accounts/menuvisibilitysetting/",
                    },
                ],
            },
            {
                "title": "Organisasi",
                "separator": True,
                "items": [
                    {
                        "title": "Karyawan",
                        "icon": "badge",
                        "link": "/admin/employees/employee/",
                    },
                    {
                        "title": "Cabang",
                        "icon": "apartment",
                        "link": "/admin/organizations/branch/",
                    },
                    {
                        "title": "Departemen",
                        "icon": "corporate_fare",
                        "link": "/admin/organizations/department/",
                    },
                ],
            },
            {
                "title": "Semua Model",
                "collapsible": True,
                "items": [
                    {
                        "title": "Lihat Semua",
                        "icon": "apps",
                        "link": "/admin/",
                    },
                ],
            },
        ],
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.erp_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

_DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')
_DB_NAME = config('DB_NAME', default='db.sqlite3')

if _DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': _DB_ENGINE,
            'NAME': BASE_DIR / _DB_NAME,
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': _DB_ENGINE,
            'NAME': _DB_NAME,
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
        }
    }

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL', default=DEBUG, cast=bool)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/.*\.paketin\.co\.id$",
    r"^https:\/\/.*\.paketin\.id$",
] if not DEBUG else []

# Upload Limits & Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'id'
LANGUAGES = [
    ('id', 'Indonesia'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_NAME = 'language'
LANGUAGE_COOKIE_AGE = 31536000
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

DATE_FORMAT = 'd/m/Y'
SHORT_DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'

DATE_INPUT_FORMATS = [
    '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
    '%d/%m/%y', '%d %b %Y',
]
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

from datetime import timedelta
from django.urls import reverse_lazy

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
}

# ─── Django Unfold Admin Configuration ───
UNFOLD = {
    "SITE_TITLE": "Paketin Cargo ERP",
    "SITE_HEADER": "Paketin Cargo Admin",
    "SITE_SUBHEADER": "Pusat Kontrol & Hak Akses",
    "SITE_URL": "/",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Akses & Pengguna",
                "separator": True,
                "items": [
                    {
                        "title": "Pengguna (Users)",
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "Role & Divisi",
                        "icon": "shield_person",
                        "link": reverse_lazy("admin:accounts_role_changelist"),
                    },
                    {
                        "title": "Izin Fitur (MenuPermission)",
                        "icon": "lock_open",
                        "link": reverse_lazy("admin:accounts_menupermission_changelist"),
                    },
                ],
            },
            {
                "title": "Data Master",
                "separator": True,
                "items": [
                    {
                        "title": "Customer / Klien",
                        "icon": "business",
                        "link": reverse_lazy("admin:master_customer_changelist"),
                    },
                    {
                        "title": "Cabang (Branch)",
                        "icon": "apartment",
                        "link": reverse_lazy("admin:organizations_branch_changelist"),
                    },
                    {
                        "title": "Departemen",
                        "icon": "corporate_fare",
                        "link": reverse_lazy("admin:organizations_department_changelist"),
                    },
                    {
                        "title": "Jabatan (Position)",
                        "icon": "badge",
                        "link": reverse_lazy("admin:organizations_position_changelist"),
                    },
                ],
            },
            {
                "title": "Operasional",
                "separator": True,
                "items": [
                    {
                        "title": "Shipment / Resi",
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:operations_shipment_changelist"),
                    },
                    {
                        "title": "Manifest",
                        "icon": "description",
                        "link": reverse_lazy("admin:operations_manifest_changelist"),
                    },
                    {
                        "title": "Pick Up Order",
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:operations_pickuporder_changelist"),
                    },
                ],
            },
            {
                "title": "CRM & Sales",
                "separator": True,
                "items": [
                    {
                        "title": "Klien CRM",
                        "icon": "storefront",
                        "link": reverse_lazy("admin:crm_client_changelist"),
                    },
                    {
                        "title": "Peluang (Lead)",
                        "icon": "filter_alt",
                        "link": reverse_lazy("admin:crm_lead_changelist"),
                    },
                    {
                        "title": "Kontrak",
                        "icon": "handshake",
                        "link": reverse_lazy("admin:crm_contract_changelist"),
                    },
                    {
                        "title": "Quotation",
                        "icon": "request_quote",
                        "link": reverse_lazy("admin:crm_quotation_changelist"),
                    },
                ],
            },
            {
                "title": "Keuangan (Finance)",
                "separator": True,
                "items": [
                    {
                        "title": "Invoice",
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:finance_invoice_changelist"),
                    },
                ],
            },
            {
                "title": "HR & Karyawan",
                "separator": True,
                "items": [
                    {
                        "title": "Karyawan",
                        "icon": "people",
                        "link": reverse_lazy("admin:employees_employee_changelist"),
                    },
                    {
                        "title": "Perangkat Presensi",
                        "icon": "devices",
                        "link": reverse_lazy("admin:employees_registereddevice_changelist"),
                    },
                ],
            },
        ],
    },
    "COLORS": {
        "primary": {
            "50": "254 242 242",
            "100": "254 226 226",
            "200": "254 202 202",
            "300": "252 165 165",
            "400": "248 113 113",
            "500": "239 68 68",
            "600": "220 38 38",
            "700": "185 28 28",
            "800": "153 27 27",
            "900": "127 29 29",
            "950": "69 10 10",
        },
    },
}
