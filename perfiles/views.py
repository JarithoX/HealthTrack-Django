from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
import requests

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
USUARIO_API_URL = f"{API_BASE_URL}/usuarios"

@login_required
def mi_perfil_view(request):
    # 1. Obtener datos básicos de la sesión
    user_session = request.session.get('user_session_data', {})
    token = user_session.get('token')
    username = request.user.username

    user_data = user_session # Fallback inicial

    # 2. Intentar obtener el perfil completo desde la API (Firebase)
    if token and username:
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(f"{USUARIO_API_URL}/username/{username}", headers=headers, timeout=5)
            
            if resp.status_code == 200:
                user_data = resp.json()
                # Opcional: Actualizar la sesión con los datos frescos (cuidado con el token)
                # user_data['token'] = token 
                # request.session['user_session_data'] = user_data
            else:
                print(f"Error al obtener perfil: {resp.status_code}")
                # No mostramos error al usuario para no interrumpir, usamos datos de sesión
        except requests.RequestException as e:
            print(f"Error de conexión API: {e}")

    # 3. Enriquecer objetivos con metadatos (iconos, textos)
    objetivos_usuario = user_data.get('objetivos', [])
    objetivos_enriquecidos = []

    OBJETIVOS_METADATA = {
        'vivir_saludable': {'icon': 'bi-heart-pulse-fill', 'label': 'Vivir más saludable', 'color': 'text-danger'},
        'aliviar_presion': {'icon': 'bi-flower1', 'label': 'Aliviar estrés', 'color': 'text-success'},
        'probar_cosas': {'icon': 'bi-stars', 'label': 'Probar cosas nuevas', 'color': 'text-warning'},
        'centrarme': {'icon': 'bi-bullseye', 'label': 'Centrarme más', 'color': 'text-primary'},
        'mejor_relacion': {'icon': 'bi-people-fill', 'label': 'Mejorar relaciones', 'color': 'text-info'},
        'dormir_mejor': {'icon': 'bi-moon-fill', 'label': 'Dormir mejor', 'color': 'text-dark'},
    }

    if objetivos_usuario:
        for obj_key in objetivos_usuario:
            meta = OBJETIVOS_METADATA.get(obj_key)
            if meta:
                objetivos_enriquecidos.append(meta)
            else:
                # Fallback para objetivos desconocidos
                objetivos_enriquecidos.append({'icon': 'bi-check-circle', 'label': obj_key, 'color': 'text-secondary'})

    context = {
        'usuario': user_data,
        'objetivos_enriquecidos': objetivos_enriquecidos,
        'panel_title': 'Mi Perfil'
    }
    return render(request, 'perfiles/mi_perfil.html', context)