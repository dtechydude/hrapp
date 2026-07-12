from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.views.generic import TemplateView # For a simple placeholder home page




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls', namespace='dashboard')),
    path('users/', include('users.urls')),
    path('employees/', include('employees.urls', namespace='employees')), 
    path('organization/', include('organization.urls', namespace='organization')), 
    path('payroll/', include('payroll.urls', namespace='payroll')), 
    path("leave/", include("leave.urls", namespace="leave")),



   
       
    # Add this line below to fix the NoReverseMatch error
    path("ckeditor5/", include('django_ckeditor_5.urls'), name="ck_editor_5_upload_file"),


    # Placeholder for a home page (create templates/home.html)
    path('', TemplateView.as_view(template_name='home.html'), name='home'), 
    # This 'home' URL name is used in report_card_detail.html and StudentDashboardView fallback
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='some_general_dashboard_or_home_page'), # Fallback for unlinked users 

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
