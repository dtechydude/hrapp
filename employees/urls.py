from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# from users import views as user_views 
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


app_name ='employees'

urlpatterns = [
       
    # path('profile/', user_views.profile_edit, name="profile"),
       
]
