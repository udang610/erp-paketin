---
name: erp-paketin-engineering-standard
description: >-
  Comprehensive engineering guidelines, hybrid architecture standards, UI/UX conventions,
  PDF rendering rules, security hardening, and ORM patterns for the ERP Paketin Cargo platform.
---

# ERP Paketin Cargo — Engineering & Development Standards

This document serves as the definitive reference manual and skill guide for developers, AI assistants, and senior software engineers working on the **ERP Paketin Cargo** system.

---

## 1. System Overview & Technology Stack

ERP Paketin Cargo is an enterprise monolithic platform built on **Django 6.1 (Python 3.13)**. It consolidates Logistics/Operations, CRM/Sales, HRGA, and Finance into a single unified source of truth.

| Layer | Technologies & Libraries |
|---|---|
| **Backend Framework** | Django 6.1, Django REST Framework (DRF), Python 3.13 |
| **Admin Panel** | Django Unfold (Tailwind-based Admin Theme) |
| **Database** | SQLite 3 (Development) / PostgreSQL (Production) with Django ORM |
| **Frontend (MPA)** | Django Templates, Bootstrap 5, Phosphor Icons (`ph-bold`, `ph-fill`), Select2 |
| **Frontend (Finance SPA)**| Vanilla JavaScript ES6+ (`static/finance/src/js/`), Chart.js |
| **Maps & Geospatial** | Leaflet.js with ArcGIS Dark Gray Canvas tile layer |
| **PDF Generation** | `xhtml2pdf` (PISA Engine), ReportLab, Python `qrcode`, Pillow |
| **Security & Auth** | Django Session Auth + DRF SimpleJWT Token Rotation, Rate Limiting Cache |

---

## 2. Codebase Architecture & Directory Layout

The codebase strictly adheres to standard Django modularity:

```
erp-paketin/
├── config/                     # Core Project Configuration
│   ├── settings.py             # Security, installed apps, auth, database, assets
│   ├── urls.py                 # Root URL router & API endpoints
│   ├── wsgi.py / asgi.py       # WSGI & ASGI entry points
│   └── navigation.py           # Sidebar & Unfold admin menu definitions
├── apps/                       # Modular Django Applications
│   ├── core/                   # Shared context processors, security, validators, dashboard
│   ├── accounts/               # Custom user model, roles, MenuVisibilitySetting
│   ├── operations/             # POS, shipments, manifests, tracking, POD, return, void
│   ├── master/                 # Master data: Customer, Vendor, Branch, Bank, Vehicle, Coverage
│   ├── crm/                    # Leads, Clients, Quotations, Contracts, Sales Activities
│   ├── finance/                # Invoicing, LDP, AR/AP, KPI Worksheet SPA & DRF APIs
│   ├── hr/                     # HR subsystems (attendance, leave, documents, approvals)
│   ├── employees/              # Employee profiles, departments, positions
│   ├── organizations/          # Company tree, branch hierarchies
│   ├── notifications/          # Activity log & role-targeted notification center
│   └── audit/                  # System audit logs
├── templates/                  # Centralized Django Template Root (Module -> Menu -> Action)
│   ├── base.html               # Global application shell (header, sidebar, search, modals)
│   ├── 404.html / 500.html     # Sanitized custom error pages
│   ├── crm/                    # Modul Sales/CRM (clients/, leads/, contracts/, quotations/, activities/, reports/)
│   ├── operations/             # Modul Operations (shipments/, manifests/, pickups/, incoming/, pod/, do_balik/, returns/, tracking/, void/, reports/)
│   ├── finance/                # Modul Finance (invoices/, ldp/, invoice_process/, worksheet/, reports/)
│   ├── hrga/                   # Modul HRGA (employees/, attendance/, attendance_policy/, leave/, documents/, organizations/)
│   ├── master/                 # Modul Data Master (banks/, branches/, coverage/, customers/, vehicles/, prices/, services/, vendors/)
│   ├── accounts/               # Auth & User Profile templates (users/, login)
│   ├── notifications/          # Activity Log & Notifications
│   ├── audit/                  # System Audit Logs
│   └── components/             # Reusable UI primitives (pagination, widgets)
├── static/                     # Static Assets (CSS, JS, images, icons)
│   ├── css/style.css           # Global design tokens, layout styles, chrome tabs
│   ├── js/main.js              # Global scripts, command palette (Ctrl+K), auto-close
│   └── js/paketin-masking.js   # Global input masks (NPWP, phone, bank accounts)
├── media/                      # Dynamic User Uploads (partitioned by domain)
├── docs/                       # Project documentation & architectural plans
├── scripts/                    # Utility, seeding, and maintenance scripts
└── manage.py                   # Django CLI entrypoint
```

---

## 3. Hybrid Architecture Pattern

ERP Paketin utilizes a **Hybrid Multi-Page / Single-Page Application (MPA + SPA)** architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             ERP PAKETIN SHELL                               │
│                         (templates/base.html)                               │
└──────────────────────┬───────────────────────────────┬──────────────────────┘
                       │                               │
       ┌───────────────▼──────────────┐ ┌──────────────▼──────────────┐
       │   Multi-Page App (MPA)       │ │    Finance SPA Worksheet    │
       │  (Dashboard, Ops, CRM, HR)   │ │ (templates/finance/index)   │
       ├──────────────────────────────┤ ├─────────────────────────────┤
       │ • Server-Side Rendered (SSR) │ │ • Client-Side Rendered (CSR)│
       │ • Django Context & Forms     │ │ • Vanilla JS ES6 Modules    │
       │ • Bootstrap 5 + Select2      │ │ • DRF JSON REST Endpoints   │
       │ • Instant HTML Response      │ │ • Zero-reload Spreadsheet   │
       └───────────────┬──────────────┘ └──────────────┬──────────────┘
                       │                               │
                       └───────────────┬───────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │   Bridged Authentication      │
                       │ (Session Auth + JWT Rotation) │
                       └───────────────────────────────┘
```

### Bridged Authentication Flow
1. User logs in via standard web session (`django.contrib.auth`).
2. When loading `/finance/`, the SPA calls `authManager.init()` $\rightarrow$ `GET /accounts/api/me/` with `credentials: 'include'`.
3. Backend validates the session cookie via `@login_required` / DRF `SessionAuthentication` and returns user profile JSON.
4. Subsequent API requests are protected via both Django Session and JWT Bearer tokens.

---

## 4. UI/UX Design System & Global Standards

All templates extending `templates/base.html` must comply with the following UI standards:

### 4.1 Global Canvas & Background
- **Gradient Background**: `linear-gradient(135deg, #eef5f1 0%, #e2ece6 45%, #f1f6f3 100%) fixed` on `body`.
- **Transparent Page Shell**: `.main-wrapper` and `.page-content` have `background: transparent !important`.
- Card wrappers should not wrap headers or action bars. Headers float directly on the gradient, while white backgrounds are strictly reserved for data tables (`.table-responsive`) and forms (`.card`).

### 4.2 Topbar & Dynamic Page Titles
- Topbar includes the dynamic `.page-title` positioned immediately to the right of the sidebar toggle button (`#sidebarToggle` / `<`).
- Filled via `{% block page_title %}` or context fallback `{{ title }}`.
- Global Command Palette trigger is accessible via `Ctrl + K` or the search box.

### 4.3 Standard Action Bar & Pop-up Dropdown Filter
Every list view across all modules must implement the standard **Minimalist Action Bar**:

```html
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <!-- Left: Universal Search & Pop-up Filter -->
    <div class="d-flex align-items-center gap-2">
        <!-- 1. Clean Search Input -->
        <div class="search-box-clean position-relative">
            <i class="ph-bold ph-magnifying-glass position-absolute top-50 start-0 translate-middle-y ms-3 text-muted"></i>
            <input type="text" name="q" value="{{ search_query|default:'' }}" class="form-control ps-5" 
                   placeholder="Cari data..." style="min-width: 260px; border-radius: 8px;">
        </div>

        <!-- 2. Pop-up Filter Dropdown -->
        <div class="dropdown">
            <button type="button" class="btn btn-outline-secondary bg-white position-relative shadow-sm" 
                    data-bs-toggle="dropdown" data-bs-auto-close="outside" style="border-radius: 8px;">
                <i class="ph-bold ph-faders me-1"></i> Filter
                {% if active_filters_count %}
                <span class="active-filter-dot position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle"></span>
                {% endif %}
            </button>
            <div class="dropdown-menu dropdown-menu-start filter-dropdown-menu p-3 shadow-lg border-0" 
                 style="width: 320px; z-index: 1060; border-radius: 12px;">
                <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
                    <span class="fw-bold text-dark fs-6">Filter Lanjutan</span>
                    <i class="ph-bold ph-sliders-horizontal text-muted"></i>
                </div>
                <!-- Filter Fields (Date, Status, Branch, etc.) -->
                <div class="mb-2">
                    <label class="form-label small fw-semibold text-muted mb-1">Rentang Tanggal</label>
                    <input type="text" name="date_range" class="form-control form-control-sm flatpickr-range" placeholder="Pilih tanggal...">
                </div>
                <!-- 50/50 Footer Action Buttons -->
                <div class="d-flex gap-2 pt-2 border-top mt-3">
                    <a href="?" class="btn btn-sm btn-light border w-50 fw-semibold text-secondary">Reset</a>
                    <button type="submit" class="btn btn-sm btn-danger w-50 fw-semibold">Terapkan</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Right: Action Buttons (Export, Add New) -->
    <div class="d-flex align-items-center gap-2">
        <button type="button" class="btn btn-outline-secondary bg-white shadow-sm" style="border-radius: 8px;">
            <i class="ph-bold ph-download-simple me-1"></i> Export
        </button>
        <a href="create/" class="btn btn-danger shadow-sm" style="border-radius: 8px;">
            <i class="ph-bold ph-plus me-1"></i> Buat Baru
        </a>
    </div>
</div>
```

### 4.4 Data Tables & Status Alignment
- **Table Hover**: `#f8fafc` on `:hover`.
- **Action Dropdowns**: Card containers must have `overflow: visible;` so action dropdown menus (`.dropdown-menu`) are not clipped.
- **Status Badges**: Centered in status columns using solid pill badges (`.badge rounded-pill`).
  - Red: `bg-danger text-white` (e.g. Returned, Void, DO Balik Pending, Overdue).
  - Amber: `bg-warning text-dark` (e.g. Pending, Draft).
  - Cyan / Blue: `bg-info text-white` (e.g. Transit, Sent, In Progress).
  - Green: `bg-success text-white` (e.g. Delivered/POD, Paid, Won, Approved).

### 4.5 Chrome-Style Tabs (`.nav-tabs-custom`)
Used in Dashboard and Operations menus (e.g. Pickup, Manifests):
- **Uniform Tab Width**: `min-width: 175px`.
- **Gliding Indicator**: Sliding pill animated via `cubic-bezier(0.4, 0, 0.2, 1)`.
- **Zero Bottom Gap**: Tab borders seamlessly connect with table headers (`thead th`).
- **Edge-to-Edge Dividers**: `1px` vertical divider (`#94a3b8`) between inactive tabs.

---

## 5. Operations & Logistics Business Rules

### 5.1 Branch-Based AWB Generation
Resi format: `[BRANCH_CODE]-CRD-[YYYYMMDD]-[CUST_CODE]-[0001]`
- Branch code is extracted from `request.user.employee_profile.branch.code` (fallback `BKS`).
- Daily sequence is filtered via `.filter(resi_number__contains=f"CRD-{date_str}")` to avoid UUID collisions.

### 5.2 Volumetric & Multi-Colly Engine
- **Volumetric Divisors**: Express/Air: `5000`, Land/Sea: `4000`, Bulky: `3000`.
- **Chargeable Weight**: $\max(\text{actual\_weight}, \text{volume\_weight})$.
- **Multi-Colly Items**: Split parent resi into `ShipmentItem` and `ShipmentColly` instances (`RES-0001-1-01`).
- **ORM Naming Convention**:
  - `Shipment` uses English dimension fields: `length`, `width`, `height`.
  - `ShipmentItem` uses Indonesian dimension fields: `panjang`, `lebar`, `tinggi`, and method `get_volume_weight()`. **Never use `item.length` in templates.**

### 5.3 Tracking & Incoming Optimization
- **Prefetching**: Never iterate over raw `Tracking` querysets. Always iterate `Shipment.objects.prefetch_related('tracking_history')`.
- Render latest scan in template via `{% with latest_scan=item.tracking_history.first %}` where ordering is `-occurred_at`.

### 5.4 Universal Void
- Single centralized endpoint: `/operations/void/credit/`.
- Removes obsolete cash void submenus.
- Logs cancellation via `apps.audit.utils.log_action` with operator details and reason.

---

## 6. High-Precision PDF Generation (`xhtml2pdf`)

When writing PDF templates in `templates/operations/` or `templates/finance/`:

### 6.1 Layout Engine Constraints
1. **No CSS Flexbox / Grid**: You MUST use `<table>` with explicit percentage/pixel widths.
2. **Page Margins**:
   - Continuous AWB: `@page { size: 215mm 110mm; margin: 2mm 3mm; }`
   - A4 3-in-1: `@page { size: a4 portrait; margin: 2mm 4mm; }`
   - Invoice A4: `@page { size: a4 portrait; margin: 10mm 15mm 10mm 15mm; }`
3. **Prevent Multi-Page Spills (A4 3-in-1)**:
   - Line height `1.0` - `1.15`.
   - Small table padding (`1.2px 2.5px`).
   - Limit multi-koli items: `{% for item in items|slice:":2" %}` + `+N Koli` summary row.
   - Explicit signature block height (`32px`).

### 6.2 Barcodes and QR Codes
- **Code128 Barcodes**: Always insert `<br/><br/>` immediately after `<pdf:barcode>` to prevent the barcode from drawing over the text below it.
  ```html
  <pdf:barcode value="{{ resi }}" type="code128" barWidth="0.85" barHeight="18" />
  <br/><br/>
  <div>{{ resi }}</div>
  ```
- **QR Codes**: Never use `<pdf:barcode type="qr" />`. Generate Python `qrcode` base64 data URI in views and render `<img src="{{ qr_data_uri }}" width="42" height="42" />`.

### 6.3 Cutting Lines with Scissor Icon
```html
<table cellpadding="0" cellspacing="0" style="width: 100%; border: none; margin: 1mm 0 2mm 0;">
    <tr>
        <td style="width: 93%; vertical-align: middle; padding: 0; overflow: hidden;">
            <div style="font-size: 8px; color: #444444; line-height: 10px; height: 10px; overflow: hidden; white-space: nowrap;">
                . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
            </div>
        </td>
        <td style="width: 4%; vertical-align: middle; text-align: center; border: none; padding: 0 1px;">
            <img src="{{ scissor_path }}" width="20" height="10" style="vertical-align: middle;" />
        </td>
        <td style="width: 3%; vertical-align: middle; text-align: right; padding: 0;">
            <div style="font-size: 8px; color: #444444; line-height: 10px; height: 10px; overflow: hidden; white-space: nowrap;">
                . . . .
            </div>
        </td>
    </tr>
</table>
```

### 6.4 Invoice PDF Specifics
- **Filename Sanitization**: In `invoice_pdf` view, sanitize slashes (`/` $\rightarrow$ `-`) in `Content-Disposition` header to prevent Chrome/Windows from defaulting the filename to `pdf.pdf`.
- **Title Tag**: Include `<title>Invoice {{ invoice.invoice_number }}</title>` in `<head>` for correct tab titles.
- **Stacked DRAFT Title**: If status is `DRAFT`, display small stacked `DRAFT` label above `INVOICE`. If `APPROVED`, display clean single `INVOICE` title.
- **Bank Info Table**: Split 68% Bank Name / 32% Account Number to guarantee 1-row layout without word wrapping.

---

## 7. Finance & Invoicing Lifecycle

1. **Invoice Status Separation**:
   - `/finance/invoices/` strictly filters active invoices (`DRAFT`, `SENT`, `PARTIAL`).
   - `PAID` (Lunas) invoices are excluded from active AR lists and accessible only under `/finance/invoice-process/?tab=completed`.
2. **Financial Calculation Formula**:
   - $\text{Subtotal} = \text{Freight} - \text{Discount} + \text{Surcharge} + \text{Packing} + \text{Other}$
   - $\text{PPN} = \text{Subtotal} \times 1.1\%$
   - $\text{Materai} = \begin{cases} \text{Rp 10.000} & \text{if } (\text{Subtotal} + \text{PPN}) > \text{Rp 5.000.000} \\ \text{Rp 0} & \text{otherwise} \end{cases}$
   - $\text{Grand Total} = \text{Subtotal} + \text{PPN} + \text{Materai} + \text{Insurance}$
3. **KPI Worksheet Auto-Sync**:
   - On invoice creation (`invoice_create`) and approval (`invoice_approve`), per-resi line items automatically sync to the `KPI Finance 2026` worksheet database.

---

## 8. Security & OWASP Hardening Standards

### 8.1 Brute-Force Rate Limiting
- `apps/core/security.py` provides `CustomLoginView` backed by Django cache rate limiting (max 10 failed attempts per IP/username per 5 minutes).

### 8.2 Token Lifetime & Rotation
- DRF SimpleJWT Access Token lifetime: **60 minutes**.
- Refresh token lifetime: **7 days** with `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True`.

### 8.3 File Upload Security (`apps/core/validators.py`)
- Whitelisted file extensions: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.webp`, `.docx`, `.xlsx`.
- Maximum image size: 5 MB; maximum document size: 10 MB.
- Configured `FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB` and `DATA_UPLOAD_MAX_MEMORY_SIZE = 10MB`.

### 8.4 Error Isolation
- Custom production error views `templates/404.html` and `templates/500.html` render user-friendly brand templates and never leak stacktraces or SQL diagnostics.

---

## 9. Quality Control & Testing Checklist

Before committing or deploying code, execute the following QC workflow:

1. **Django System Integrity Check**:
   ```bash
   .\venv\Scripts\python manage.py check
   ```
2. **Dry-Run Migration Check**:
   ```bash
   .\venv\Scripts\python manage.py makemigrations --check --dry-run
   ```
3. **Automated Unit Tests**:
   ```bash
   .\venv\Scripts\python manage.py test apps.notifications apps.operations apps.accounts apps.finance
   ```
4. **Static Asset Collection**:
   ```bash
   .\venv\Scripts\python manage.py collectstatic --noinput --dry-run
   ```
5. **Route Smoke Test**: Verify HTTP 200 responses across core views (Dashboard, Shipment List, Manifests, Invoice List, Master List, Employee List, Notifications).
