from django.urls import path
from dashboard import views as dashboard_views
from . import views

app_name ='dashboard'

urlpatterns = [

     path('', dashboard_views.landing_page, name='app-home'), 

     path('dashboard/', dashboard_views.dashboard, name="portal-home"),     
    

]
