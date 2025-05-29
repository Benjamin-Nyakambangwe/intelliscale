from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect('users:login')

urlpatterns = [
    path('', redirect_to_login, name='home'),  # Redirect root URL to login
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path('scale/', include('scale.urls')),
]