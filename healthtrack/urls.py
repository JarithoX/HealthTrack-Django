from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def redirect_to_login(request):
    return redirect('account:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls', namespace='account')),
    path('home/', include('home.urls')),
    path('habitos/', include('seguimiento.urls')),
    path('', redirect_to_login),  # Redirige la raíz al login
    path('admin_panel/', include('admin_panel.urls')), 
    path('professional_panel/', include('professional_panel.urls')),
]
