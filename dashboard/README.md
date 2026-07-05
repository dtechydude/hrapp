# Dashboard: Real Stats, Real Chart, Real Downloads

## What changed

1. **`templates/dashboard/hrpams_dashboard.html`**
   - Removed ~2,100 lines of dead, never-rendered duplicate markup
     (everything that was wrapped in `{% comment %}...{% endcomment %}`
     at the bottom of your file).
   - Chart repurposed from fake "Monthly Payroll vs Deductions" to
     real **"Staff & Organization Growth (6 Months)"** — payroll
     numbers don't exist yet, so showing fake ones indefinitely would
     violate the "never generate quick hacks" rule. Swap it back once
     payroll ships (the `growth_chart_data` context key is the only
     thing to change).
   - Page-header **Export** button is now a working dropdown with
     three real downloads: Client Organizations, Staff List,
     Deployment List.
   - Payroll KPI card, Payroll Breakdown donut, and Payroll Approval
     Queue table are explicitly commented `PAYROLL PLACEHOLDER` so
     it's obvious in the markup what's real vs. pending.

2. **`dashboard/views.py` + `dashboard/services.py`** — the actual
   `DashboardView` supplying real numbers: `total_active_staff`,
   `total_organizations`, `suspended_staff`, `staff_on_leave`,
   `new_hires_this_month`, and the 6-month growth chart data.

3. **`core/exports.py`** — one reusable `export_queryset_as_csv()`
   helper. Every future "download list" button (payroll register,
   loan schedule, leave report, ...) calls this instead of writing
   `csv.writer` boilerplate again.

4. **`organization/views.py` / `organization/urls.py`** (updated —
   these already existed from the deployment module) — two new views:
   `OrganizationExportView`, `DeploymentExportView`.

5. **`employees/exports.py`** (new, standalone) — `StaffExportView`.
   Kept separate from your existing `employees/views.py` /
   `employees/urls.py` since those weren't shared with me; don't
   overwrite yours, just add the one import + one URL line noted in
   the file's docstring.

## Wiring steps

**1. Drop in the files** matching the folder structure above onto
your existing apps (`dashboard/`, `organization/`, `employees/`,
`core/`, and the template path).

**2. Route the dashboard view** in your project urls (if not already):

```python
from dashboard.views import DashboardView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard-home"),
    ...
]
```

**3. Add the staff export URL** — the one line `employees/exports.py` asks for:

```python
# employees/urls.py
from .exports import StaffExportView

urlpatterns = [
    ...,
    path("export/", StaffExportView.as_view(), name="staff-export"),
]
```

**4. Permissions** — the three export views reuse permissions that
already exist from prior modules (`organization.view_company`,
`organization.view_staffdeployment`, `employees.view_staff`). If your
`Company` model's Meta doesn't set a custom `verbose_name` in a way
that breaks Django's auto-generated permission codename, this just
works; otherwise check `Company._meta.permissions` in the shell.

**5. No new migrations** — nothing here touches models.

## What's intentionally left alone

- Recent Activity feed, Recently Active Staff table, Quick Actions,
  Module Activity, Upcoming Events — all already have proper
  `{% if %}` / `{% for %}` scaffolding waiting for real querysets;
  wiring those up is a good next step once their respective apps
  (notifications, leave, documents) exist.
- Payroll sections — clearly marked, untouched, waiting for that
  module.