from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from .forms import PerfilConfigForm # Importa el formulario que creaste en home/forms.py

API_BASE_URL = 'http://localhost:3000/api' # O usa settings si ya lo configuraste

# VISTA DE ONBOARDING (La nueva vista principal temporal)
@login_required
def completar_perfil_view(request):
    # 🚨 NOTA IMPORTANTE: En la lógica real, aquí consultarías a la API
    # para saber si el perfil ya tiene 'peso', 'altura', etc.,
    # y si están completos, redirigirías a 'home:index'.
    # Por ahora, asumimos que debe completarse.
    
    if request.method == 'POST':
        form = PerfilConfigForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data # Datos limpios y válidos
            
            # 🚨 Clave: Aquí estamos usando el username como ID de Firestore.
            # Esto funciona si así lo tienes mapeado en Node.js
            username = request.user.username 
            
            try:
                # 1. Llamada al endpoint PUT de Node.js (que debes crear)
                resp = requests.put(
                    f"{API_BASE_URL}/usuarios/perfil/{username}", 
                    json=data, 
                    timeout=10
                )
                
                if resp.status_code == 200:
                    messages.success(request, '¡Perfil completado! Bienvenido.')
                    return redirect('home:index') # Redirigir al dashboard final
                else:
                    # Captura el error de la API (ej. 400 Bad Request)
                    try:
                        msg = resp.json().get('error', 'Error al guardar los datos de salud.')
                    except:
                        msg = 'Error de API inesperado al completar perfil.'
                    messages.error(request, msg)
            
            except requests.RequestException:
                messages.error(request, 'Error de conexión con la API de salud. ¿Está Node.js corriendo?')

    else:
        form = PerfilConfigForm()
        
    context = {
        'form': form,
        'titulo': 'Completa tu Perfil',
        'descripcion': 'Solo un paso más para empezar a monitorear tu salud.'
    }
    
    # 🚨 NOTA: Usa la nueva ruta de plantilla 'home/completar_perfil.html'
    return render(request, 'home/completar_perfil.html', context)


# VISTA DE DASHBOARD/INDEX (Si el perfil ya está completo)
@login_required
def index(request):
    # Aquí iría la lógica para consultar las métricas y hábitos del usuario
    context = {
        'titulo': 'Dashboard Principal',
        'descripcion': 'Revisa tu progreso diario y las estadísticas.',
    }
    # Asegúrate de que esta vista se llama 'home/index.html'
    return render(request, 'home/index.html', context)