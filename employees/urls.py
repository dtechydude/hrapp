"""
employees/urls.py
───────────────────────────────────────────────────────────────────────────
URL Configuration for the employees (staff) app.

Namespace: staff
Include in root urls.py as:
    path("staff/", include("employees.urls", namespace="staff")),

Named URLs
──────────
  staff:list            /staff/
  staff:create          /staff/add/
  staff:detail          /staff/<uuid>/
  staff:update          /staff/<uuid>/edit/
  staff:deactivate      /staff/<uuid>/deactivate/     [POST]
  staff:toggle_status   /staff/<uuid>/toggle-status/  [POST]
───────────────────────────────────────────────────────────────────────────
"""

from django.urls import path

from .views import (
    StaffCreateView,
    StaffDetailView,
    StaffListView,
    StaffUpdateView,
    StaffDeactivateView,
    StaffStatusToggleView,
)

app_name = "employees"

urlpatterns = [
    # List all staff
    path(
        "",
        StaffListView.as_view(),
        name="employee-list",
    ),

    # Register a new staff member
    path(
        "add/",
        StaffCreateView.as_view(),
        name="add-employee",
    ),

    # View a staff profile
    path(
        "<uuid:uuid>/",
        StaffDetailView.as_view(),
        name="detail",
    ),

    # Edit a staff record
    path(
        "<uuid:uuid>/edit/",
        StaffUpdateView.as_view(),
        name="update",
    ),

    # Soft deactivate (superuser only, POST)
    path(
        "<uuid:uuid>/deactivate/",
        StaffDeactivateView.as_view(),
        name="deactivate",
    ),

    # Toggle ACTIVE ↔ SUSPENDED (POST)
    path(
        "<uuid:uuid>/toggle-status/",
        StaffStatusToggleView.as_view(),
        name="toggle_status",
    ),
]
