from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib import messages
import requests # Para comunicarse con la API de Node.js (Firebase)

User = get_user_model() 
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
USUARIO_API_URL = f"{API_BASE_URL}/usuarios" # Ajusta si tu endpoint es diferente

# Helper: Verifica si el usuario es Admin o Superuser (is_staff es suficiente para el panel)
def is_admin_or_staff(user):
    return user.is_active and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin_or_staff, login_url='/account/login') # Protege el acceso
def admin_dashboard_view(request):
    # Por ahora, un simple dashboard. Aquí irán estadísticas y gráficos más tarde.
    context = {
        'total_usuarios': User.objects.count(),
        'panel_title': 'Dashboard Administrativo'
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url= '/account/login')
def listar_usuarios_view(request):
    # Obtiene todos los usuarios locales de Django. Excluimos al superusuario actual
    # para evitar que el admin se elimine accidentalmente a sí mismo.
    usuarios_locales = User.objects.exclude(username=request.user.username).order_by('username')
    
    # NOTA: En este punto, solo tenemos datos locales. El rol de Firebase se leerá 
    # cuando implementemos la edición o si se necesitan datos de Firestore.

    context = {
        'usuarios': usuarios_locales
    }
    return render(request, 'admin_panel/listar_usuarios.html', context)

