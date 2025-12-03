from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

@login_required
def mi_perfil_view(request):
    # Lógica para obtener el perfil desde la API
    # ... (El código que íbamos a poner en account, ahora va aquí) ...
    
    # Ejemplo rápido de estructura:
    user_data = request.session.get('user_session_data', {})
    
    context = {
        'usuario': user_data,
        'panel_title': 'Mi Perfil'
    }
    return render(request, 'perfiles/mi_perfil.html', context)