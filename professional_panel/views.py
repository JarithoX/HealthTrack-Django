from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib import messages
import requests
from . import services

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

# Helper: Verifica si el usuario es Profesional
def is_professional(user):
    # Aquí deberías implementar la lógica real para verificar si es profesional.
    # Por ahora, permitimos acceso si está autenticado y activo, 
    # pero idealmente verificarías un campo 'rol' o pertenencia a un grupo.
    return user.is_active 

# Helper para obtener headers con token
def get_auth_headers(request):
    user_data = request.session.get('user_session_data', {})
    token = user_data.get('token')

    if not token or not isinstance(token, str) or len(token) < 50:
        return None
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

@login_required
@user_passes_test(is_professional, login_url='/account/login')
def professional_dashboard_view(request):
    headers = get_auth_headers(request)
    if not headers:
        messages.error(request, "Sesión inválida. Por favor, inicia sesión nuevamente.")
        return redirect('account:login')

    # Calcular cantidad de pacientes
    pacientes_count = 0
    try:
        resp = requests.get(USUARIO_API_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            all_users = resp.json()
            # Misma lógica de filtro: NO admin ni profesional
            pacientes = [u for u in all_users if u.get('rol') not in ['admin', 'profesional']]
            pacientes_count = len(pacientes)
    except:
        pass

    context = {
        'panel_title': 'Panel del Profesional',
        'pacientes_count': pacientes_count
    }
    return render(request, 'professional_panel/dashboard.html', context)

# --- CONSTANTES API ---
USUARIO_API_URL = f"{API_BASE_URL}/usuarios"
HABITO_DEFINICION_URL = f"{API_BASE_URL}/habito-definicion"
HABITO_REGISTRO_URL = f"{API_BASE_URL}/habito-registro"

@login_required
@user_passes_test(is_professional, login_url='/account/login')
def listar_pacientes_view(request):
    headers = get_auth_headers(request)
    if not headers:
        messages.error(request, "Sesión inválida.")
        return redirect('account:login')

    usuarios = []
    try:
        resp = requests.get(USUARIO_API_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            all_users = resp.json()
            # Filtramos para mostrar todos los usuarios que NO sean admin ni profesional
            usuarios = [u for u in all_users if u.get('rol') not in ['admin', 'profesional']] 
    except requests.RequestException:
        messages.error(request, "Error al obtener lista de pacientes.")

    context = {
        'usuarios': usuarios,
        'panel_title': 'Mis Pacientes'
    }
    return render(request, 'professional_panel/listar_pacientes.html', context)

@login_required
@user_passes_test(is_professional, login_url='/account/login')
def detalle_paciente_view(request, username):
    headers = get_auth_headers(request)
    if not headers:
        return redirect('account:login')

    # 1. Obtener datos del usuario
    usuario = {}
    try:
        resp = requests.get(f"{USUARIO_API_URL}/username/{username}", headers=headers, timeout=5)
        if resp.status_code == 200:
            usuario = resp.json()
    except:
        pass

    # 2. Obtener hábitos definidos
    habitos = []
    try:
        resp = requests.get(f"{HABITO_DEFINICION_URL}/{username}", headers=headers, timeout=5)
        if resp.status_code == 200:
            habitos = resp.json()
    except:
        pass

    # 3. Obtener registros de progreso
    registros = []
    try:
        resp = requests.get(f"{HABITO_REGISTRO_URL}/{username}", headers=headers, timeout=5)
        if resp.status_code == 200:
            registros = resp.json()
    except:
        pass

    # 4. Manejo de Comentarios (Firestore)
    if request.method == 'POST':
        comentario_texto = request.POST.get('comentario')
        if comentario_texto:
            success = services.send_message(
                professional_username=request.user.username,
                patient_username=username,
                content=comentario_texto,
                is_from_professional=True
            )
            if success:
                messages.success(request, "Comentario enviado correctamente.")
            else:
                messages.error(request, "Error: No se pudo conectar con la API de Chat. Verifica que tu servidor Node.js esté corriendo.")
            return redirect('professional_panel:detalle_paciente', username=username)

    # Obtener comentarios históricos de Firestore
    comentarios = services.get_messages(patient_username=username)
    # Ordenar por fecha descendente para la vista (el servicio devuelve ascendente)
    comentarios.reverse()

    context = {
        'usuario': usuario,
        'habitos': habitos,
        'registros': registros,
        'comentarios': comentarios,
        'panel_title': f'Expediente: {username}'
    }
    return render(request, 'professional_panel/detalle_paciente.html', context)
