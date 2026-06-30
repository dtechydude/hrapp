# HRPAMS Django Templates

Extracted and Django-ified from the HRPAMS dashboard design.

## File Structure

```
hrpams_templates/
├── static/
│   └── css/
│       └── hrpams.css          ← All shared CSS (design tokens, components)
└── templates/
    ├── base.html               ← Sidebar + topbar shell, all blocks defined
    └── registration/           ← Django auth views, no extra config needed
        ├── login.html
        ├── logged_out.html
        ├── password_reset_form.html
        ├── password_reset_done.html
        ├── password_reset_confirm.html
        └── password_reset_complete.html
```

---

## Django Setup

### 1. settings.py

```python
INSTALLED_APPS = [
    ...
    'django.contrib.staticfiles',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # point to your templates folder
        ...
    }
]

STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']   # point to your static folder

# Auth redirects
LOGIN_URL          = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'   # or omit to show logged_out.html

# Email (for password reset)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# ... your SMTP settings
```

### 2. urls.py (project level)

```python
from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    # This registers all of:
    #   accounts/login/                   → login
    #   accounts/logout/                  → logout
    #   accounts/password_reset/          → password_reset
    #   accounts/password_reset/done/     → password_reset_done
    #   accounts/reset/<uidb64>/<token>/  → password_reset_confirm
    #   accounts/reset/done/              → password_reset_complete
    ...
]
```

### 3. Using base.html in your views

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Dashboard{% endblock %}
{% block breadcrumb %}Dashboard{% endblock %}

{# Mark the active nav item #}
{% block nav_dashboard %}active{% endblock %}

{% block content %}
  <div class="page-header">
    <div>
      <div class="page-title">Good morning, {{ request.user.first_name }} 👋</div>
      <div class="page-subtitle">Here's what's happening today</div>
    </div>
  </div>

  {# Your page content here #}
{% endblock %}
```

---

## Nav Active State Pattern

Each sidebar link has a corresponding block you can override with `active`:

| Block name               | Link                  |
|--------------------------|-----------------------|
| `nav_dashboard`          | Dashboard             |
| `nav_staff_open`         | Staff Management btn  |
| `nav_staff_list`         | All Staff             |
| `nav_staff_add`          | Add New Staff         |
| `nav_org_open`           | Organizations btn     |
| `nav_org_list`           | All Organizations     |
| `nav_payroll_open`       | Payroll btn           |
| `nav_payroll_run`        | Run Payroll           |
| `nav_attendance`         | Attendance            |
| `nav_leave_open`         | Leave Management btn  |
| `nav_settings`           | Settings              |
| *(see base.html for all)*|                       |

---

## Context Variables (from views / context processors)

| Variable                   | Used in                        |
|----------------------------|--------------------------------|
| `unread_notifications_count` | topbar dot + sidebar badge   |
| `attendance_pending_count`   | sidebar Attendance badge     |
| `payroll_pending`            | sidebar Payroll `!` badge    |

Add these via a custom context processor or pass them directly from your views.

---

## CSS Classes Reference

See `hrpams.css` — every component is documented with section headers:

- **Layout**: `.app-shell`, `.sidebar`, `.main-area`, `.topbar`, `.page-content`
- **Buttons**: `.btn`, `.btn-primary`, `.btn-gold`, `.btn-outline`, `.btn-danger`, `.btn-sm`, `.btn-xs`
- **Cards**: `.card`, `.card-header`, `.card-body`, `.kpi-card`
- **Status pills**: `.pill.active`, `.pill.pending`, `.pill.suspended`, `.pill.on-leave`, etc.
- **Tables**: `.data-table`, `.data-table-wrap`
- **Forms / Auth**: `.form-control`, `.form-group`, `.form-label`, `.auth-shell`, `.auth-card`
- **Grids**: `.kpi-grid`, `.grid-2`, `.grid-3`, `.quick-grid`
