from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib import messages
import requests
import sys
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
            current_pro_uid = request.session.get('user_session_data', {}).get('uid')
            
            # Contar solo los asignados a ESTE profesional
            mis_pacientes = [
                u for u in all_users 
                if u.get('rol') == 'user' and u.get('assignedProfessionalId') == current_pro_uid
            ]
            pacientes_count = len(mis_pacientes)
            
            # Contar disponibles (sin asignar)
            disponibles = [
                u for u in all_users
                if u.get('rol') == 'user' and not u.get('assignedProfessionalId')
            ]
            disponibles_count = len(disponibles)
            
    except Exception as e:
        print(f"Error dashboard count: {e}", file=sys.stderr)
        pass

    context = {
        'panel_title': 'Panel del Profesional',
        'pacientes_count': pacientes_count,
        'disponibles_count': disponibles_count
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

    mis_pacientes = []
    pacientes_disponibles = []
    
    current_pro_uid = request.session.get('user_session_data', {}).get('uid')

    try:
        resp = requests.get(USUARIO_API_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            all_users = resp.json()
            # Filtramos usuarios que sean 'user' (no admin/pro)
            candidates = [u for u in all_users if u.get('rol') not in ['admin', 'profesional']]
            
            for u in candidates:
                assigned_id = u.get('assignedProfessionalId')
                
                # LOGICA DE CLASIFICACIÓN
                if assigned_id == current_pro_uid:
                    mis_pacientes.append(u)
                elif not assigned_id:
                    # Si no tiene asignado nadie, está disponible
                    pacientes_disponibles.append(u)
                else:
                    # Está asignado a OTRO profesional (Opcional: mostrar o esconder)
                    # Por ahora los escondemos para no ensuciar la vista
                    pass

    except requests.RequestException:
        messages.error(request, "Error al obtener lista de pacientes.")

    context = {
        'mis_pacientes': mis_pacientes,
        'pacientes_disponibles': pacientes_disponibles,
        'panel_title': 'Gestión de Pacientes'
    }
    return render(request, 'professional_panel/listar_pacientes.html', context)

@login_required
@user_passes_test(is_professional, login_url='/account/login')
def asignar_paciente_view(request, uid):
    headers = get_auth_headers(request)
    current_pro_uid = request.session.get('user_session_data', {}).get('uid')
    
    if not headers or not current_pro_uid:
        return redirect('account:login')
        
    try:
        payload = {'professionalUid': current_pro_uid}
        # Endpoint definido en la guía: /api/usuarios/assign/:uid
        assign_url = f"{USUARIO_API_URL}/assign/{uid}"
        
        print(f"DEBUG: Asignando paciente {uid} a pro {current_pro_uid}", file=sys.stderr)
        
        resp = requests.put(assign_url, json=payload, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            messages.success(request, "Paciente asignado correctamente.")
        else:
            err = resp.json().get('error') or resp.text
            messages.error(request, f"Error al asignar: {err}")
            
    except Exception as e:
        print(f"Error asignacion: {e}", file=sys.stderr)
        messages.error(request, "Error técnico al intentar asignar.")

    return redirect('professional_panel:listar_pacientes')

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

# --- HABIT TEMPLATES ---
HABIT_TEMPLATES = {
    'sueno_optimo': {
        'nombre': 'Sueño Reparador',
        'descripcion': 'Dormir al menos 8 horas para recuperación óptima.',
        'meta': 8,
        'tipo_medicion': 'Numerico',
        'unidad': 'horas',
        'frecuencia': 'diario'
    },
    'hidratacion': {
        'nombre': 'Hidratación Básica',
        'descripcion': 'Beber 2 litros de agua a lo largo del día.',
        'meta': 2000,
        'tipo_medicion': 'Numerico',
        'unidad': 'ml',
        'frecuencia': 'diario'
    },
    'caminata': {
        'nombre': 'Caminata Diaria',
        'descripcion': 'Caminar a paso ligero para activar metabolismo.',
        'meta': 30,
        'tipo_medicion': 'Numerico',
        'unidad': 'minutos',
        'frecuencia': 'diario'
    },
    'frutas': {
        'nombre': 'Consumo de Frutas',
        'descripcion': 'Comer 2 porciones de fruta fresca.',
        'meta': 2,
        'tipo_medicion': 'Numerico',
        'unidad': 'piezas',
        'frecuencia': 'diario'
    },
    'meditacion': {
        'nombre': 'Meditación / Mindfulness',
        'descripcion': 'Pausa para reducir el estrés.',
        'meta': 10,
        'tipo_medicion': 'Numerico',
        'unidad': 'minutos',
        'frecuencia': 'diario'
    }
}

@login_required
@user_passes_test(is_professional, login_url='/account/login')
def recomendar_habito_view(request, username):
    headers = get_auth_headers(request)
    if not headers:
        return redirect('account:login')

    # Obtener datos básicos del paciente (necesitamos su UID para la API de hábitos)
    patient_uid = None
    try:
        resp = requests.get(f"{USUARIO_API_URL}/username/{username}", headers=headers, timeout=5)
        if resp.status_code == 200:
            patient_data = resp.json()
            # La API devuelve el objeto usuario, usamos su ID (firebaseUid o id)
            patient_uid = patient_data.get('firebaseUid') or patient_data.get('id')
    except:
        pass

    if not patient_uid:
        messages.error(request, "No se pudo identificar al paciente.")
        return redirect('professional_panel:detalle_paciente', username=username)

    if request.method == 'POST':
        template_key = request.POST.get('template_key')
        custom_msg = request.POST.get('mensaje_personalizado', '')
        
        selected_habit = HABIT_TEMPLATES.get(template_key)
        
        if selected_habit:
            # Construir payload para la API de Hábitos
            payload = selected_habit.copy()
            # FIX: El sistema de usuarios usa 'username' como ID de los hábitos, no el UID
            # Verificado en seguimiento/views.py
            target_id = username.lower() 
            
            payload['id_usuario'] = target_id 
            payload['userId'] = target_id 
            # Campo clave para la funcionalidad "Recomendado por"
            # Usamos el nombre del usuario profesional actual
            payload['assignedBy'] = request.user.username 
            
            # Opcional: Podríamos adjuntar el mensaje personalizado en la descripción
            if custom_msg:
                payload['descripcion'] = f"{payload['descripcion']} (Nota: {custom_msg})"

            try:
                # URL API: POST /api/habito-definicion
                # Ajustar si tu URL es diferente
                resp_post = requests.post(f"{API_BASE_URL}/habito-definicion", json=payload, headers=headers, timeout=5)
                
                if resp_post.status_code in [200, 201]:
                    messages.success(request, f"Hábito '{selected_habit['nombre']}' asignado correctamente.")
                    return redirect('professional_panel:detalle_paciente', username=username)
                else:
                    err = resp_post.json().get('error') or resp_post.text
                    messages.error(request, f"Error API al asignar hábito: {err}")
            except Exception as e:
                print(f"Error asignando habito: {e}", file=sys.stderr)
                messages.error(request, "Error de conexión al asignar hábito.")
        else:
            messages.error(request, "Debes seleccionar una plantilla válida.")

    context = {
        'username': username,
        'templates': HABIT_TEMPLATES,
        'panel_title': f'Recomendar Hábito a {username}'
    }
    return render(request, 'professional_panel/recomendar_habito.html', context)
