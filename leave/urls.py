"""
leave/urls.py
───────────────────────────────────────────────────────────────────────────
Namespace: leave
Include in root urls.py as:
    path("leave/", include("leave.urls", namespace="leave")),

Named URLs
──────────
  leave:apply          /leave/apply/            employee — apply
  leave:my_requests    /leave/my/               employee — own list
  leave:cancel         /leave/<uuid>/cancel/     employee — withdraw [POST]
  leave:list           /leave/requests/          manager  — all requests
  leave:detail         /leave/<uuid>/            manager  — detail
  leave:approve        /leave/<uuid>/approve/    manager  — [POST]
  leave:decline        /leave/<uuid>/decline/    manager  — [POST]
───────────────────────────────────────────────────────────────────────────
"""
from django.urls import path

from .views import (
    LeaveRequestApproveView,
    LeaveRequestCancelView,
    LeaveRequestCreateView,
    LeaveRequestDeclineView,
    LeaveRequestDetailView,
    LeaveRequestListView,
    MyLeaveRequestListView,
    StaffOnLeaveListView,
)

app_name = "leave"

urlpatterns = [
    # Employee
    path("apply/", LeaveRequestCreateView.as_view(), name="apply-leave"),
    path("myleave/", MyLeaveRequestListView.as_view(), name="my_requests"),
    path("<uuid:uuid>/cancel/", LeaveRequestCancelView.as_view(), name="cancel"),

    # Manager
    path("requests/", LeaveRequestListView.as_view(), name="list"),
    path("on-leave/", StaffOnLeaveListView.as_view(), name="on_leave"),
    path("<uuid:uuid>/", LeaveRequestDetailView.as_view(), name="detail"),
    path("<uuid:uuid>/approve/", LeaveRequestApproveView.as_view(), name="approve"),
    path("<uuid:uuid>/decline/", LeaveRequestDeclineView.as_view(), name="decline"),
]
