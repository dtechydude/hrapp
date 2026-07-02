from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# from employees import views as employees_views 
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.urls import path
from . import views

app_name = 'employees'


urlpatterns = [
    path('', views.StaffListView.as_view(), name='list'),
    path('add/', views.StaffCreateView.as_view(), name='add'),
    path('<uuid:uuid>/edit/', views.StaffUpdateView.as_view(), name='edit'),

]

