from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('home/', include('home.urls')),
    path('habitos/', include('seguimiento.urls')),
    path('', redirect_to_login),  # Redirige la raíz al login
]
