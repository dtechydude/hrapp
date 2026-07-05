from django.urls import path

from . import views

app_name = "organization"

urlpatterns = [
    path(
        "deployments/",
        views.DeploymentListView.as_view(),
        name="deployment-list",
    ),
    path(
        "deployments/deploy/",
        views.DeploymentCreateView.as_view(),
        name="deployment-create",
    ),
    path(
        "deployments/<int:pk>/end/",
        views.EndDeploymentView.as_view(),
        name="deployment-end",
    ),
    path(
        "deployments/staff/<int:staff_id>/history/",
        views.DeploymentHistoryView.as_view(),
        name="deployment-history",
    ),
    path(
        "deployments/export/",
        views.DeploymentExportView.as_view(),
        name="deployment-export",
    ),
    path(
        "organizations/export/",
        views.OrganizationExportView.as_view(),
        name="organization-export",
    ),
]