from django.urls import path
from dashboard import views as dashboard_views
from . import views
from .views import DashboardHomeView, DashboardView


app_name ='dashboard'

urlpatterns = [

    path('', DashboardView.as_view(), name="app-home"),
    # path('', dashboard_views.admin_dashboard, name='app-home'),     
    path('staff/', DashboardHomeView.as_view(), name="staff-home"),
    

          

]
