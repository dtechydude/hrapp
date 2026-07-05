# Staff Deployment & Location Module

Drop these files into your `organization` app (they replace/extend what you
already have — nothing outside `organization/` needs to change).

```
organization/
  models.py       # replace — adds Company.address + audit fields/constraint to StaffDeployment
  managers.py      # new
  services.py      # new
  forms.py         # new
  views.py         # new (or merge if you already have other views here)
  urls.py          # new (or merge)
  admin.py         # new (or merge)
  templates/organization/
    deployment_list.html
    deployment_form.html
    deployment_history.html
```

## 0. New shared `core` app

`core/models.py` now holds `AuditableModel` — the abstract base class
providing `is_active / created_at / updated_at / created_by / updated_by`
that `Company`, `Department`, `StaffRole`, `StaffRank`, and
`StaffDeployment` all inherit from. Any new model anywhere in the
project (payroll, loans, leave, accounting, documents, ...) should
inherit this instead of `models.Model` going forward, per the "every
model must have audit fields" rule.

Add it to `INSTALLED_APPS` **before** `organization`:

```python
INSTALLED_APPS = [
    ...
    "core",
    "organization",
    "employees",
    ...
]
```

## 1. Wire the URLs

In your project's root `urls.py`:

```python
urlpatterns = [
    ...
    path("hr/", include("organization.urls", namespace="organization")),
]
```

Adjust the `"hr/"` prefix to match how the rest of HRPAMS is namespaced.

## 2. Migration required

`core` is a new app with only an abstract model — it has nothing to
migrate itself, but `organization` now depends on it. Run migrations
for both:

```bash
python manage.py makemigrations core organization
python manage.py migrate
```

What changed in `organization`:

- `Company` gains the full Organization Management field set from the
  spec: `code` (auto-generated, e.g. `ORG0001`), `industry`, `address`,
  `contact_person`, `phone`, `email`, `contract_start_date`,
  `contract_end_date`, `status`, `logo`, `notes`.
- `Company`, `Department`, `StaffRole`, `StaffRank`, and
  `StaffDeployment` all now inherit `AuditableModel`
  (`is_active`, `created_at`, `updated_at`, `created_by`, `updated_by`).
- `StaffDeployment` keeps its `UniqueConstraint` guaranteeing a staff
  member can never have two `is_current=True` postings at once.

If you already applied the previous version of this migration (the one
that only added `Company.address` + audit fields directly on
`StaffDeployment`), Django's migration autodetector will generate a
field-move rather than a fresh add — that's expected and safe.

If any existing staff member currently has more than one `is_current=True`
row (shouldn't happen, but worth checking on an existing dataset), the
migration will fail to apply the constraint until that's cleaned up:

```python
# one-off cleanup shell snippet if needed
from organization.models import StaffDeployment
from django.db.models import Count
dupes = (StaffDeployment.objects.filter(is_current=True)
         .values('staff').annotate(c=Count('id')).filter(c__gt=1))
```

## 3. Permissions (Role Based Access Control)

Django auto-creates these permissions for `StaffDeployment` — no custom
permission model needed:

- `organization.view_staffdeployment`
- `organization.add_staffdeployment`
- `organization.change_staffdeployment`

Assign them via **Admin → Groups**:

| Group             | Permissions                                                        |
|-------------------|---------------------------------------------------------------------|
| System Admin      | view, add, change                                                    |
| HR Manager        | view, add, change                                                    |
| Branch Manager    | view                                                                  |
| Auditor           | view                                                                  |

## 4. Dashboard widget (optional)

To surface a "deployed today" tile on `hrpams_dashboard.html`, reuse the
same manager the list view uses — no duplicated query logic:

```python
# in your dashboard view
from organization.models import StaffDeployment

context["deployed_count"] = StaffDeployment.objects.current().count()
```

```html
<a href="{% url 'organization:deployment-list' %}" class="stat-card">
  <div class="stat-icon" style="background:var(--navy)"><i class="bi bi-geo-alt-fill"></i></div>
  <div>
    <div class="stat-value">{{ deployed_count }}</div>
    <div class="stat-label">Staff Currently Deployed</div>
  </div>
</a>
```

## 5. Template assumption

Templates extend `dashboard/base.html` and assume the same blocks and CSS
custom properties already used in your `staff_form.html`
(`page_header`, `breadcrumb`, `extra_css`, `content`, `extra_js`, and
variables like `--navy`, `--gold`, `--border`, `--text-muted`, `.card`,
`.btn-outline`, `.btn-gold`, `.pill`). If your base template uses
different block/variable names, only the block declarations at the top of
each template need renaming — the markup inside is unaffected.

## What this does NOT do (by design, to stay in scope)

- Does not touch `employees/models.py` — `Staff.current_deployment`
  keeps working unchanged since it just reads `is_current=True`.
- Does not add a REST API — the manager/service split means one can be
  added later (DRF serializer calling `deploy_staff()`) without touching
  this code.
- Does not delete/hide old deployments anywhere — history is permanent,
  per the project's audit rules.
