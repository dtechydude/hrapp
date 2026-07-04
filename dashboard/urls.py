from django.urls import path
from dashboard import views as dashboard_views
from . import views
from .views import DashboardHomeView


app_name ='dashboard'

urlpatterns = [

     path('', dashboard_views.landing_page, name='app-home'), 

     path('dashboard/', dashboard_views.dashboard, name="portal-home"),  
     path('staff/', DashboardHomeView.as_view(), name="staff-home"),
   
    

]
