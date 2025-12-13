from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from .forms import RolUsuarioForm
from django.contrib import messages
import requests # Para comunicarse con la API de Node.js (Firebase)
import sys # Para logging en Cloud Run

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
USUARIO_API_URL = f"{API_BASE_URL}/usuarios" # Ajusta si tu endpoint es diferente

# Helper: Verifica si el usuario es Admin o Superuser (is_staff es suficiente para el panel)
def is_admin_or_staff(user):
    return user.is_active and (user.is_staff or user.is_superuser)

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

# -------------------------------------------------------------------
# 1. VISTA: Dashboard Administrativo
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url='/account/login') # Protege el acceso
def admin_dashboard_view(request):
    # Obtener headers con token
    headers = get_auth_headers(request)
    if not headers:
        messages.error(request, "Sesión inválida. Por favor, inicia sesión nuevamente.")
        return redirect('account:login')

# Inicializar contadores
    stats = {
        'total': 0,
        'profesionales': 0,
        'admins': 0,
        'activos': 0,
        'inactivos': 0
    }

    try:
        # Obtenemos la lista completa para calcular métricas
        resp = requests.get(USUARIO_API_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            usuarios = resp.json()
            
            # --- CÁLCULO DE MÉTRICAS EN PYTHON ---
            stats['total'] = len(usuarios)
            stats['profesionales'] = sum(1 for u in usuarios if u.get('rol') == 'profesional')
            stats['admins'] = sum(1 for u in usuarios if u.get('rol') == 'admin')
            stats['activos'] = sum(1 for u in usuarios if u.get('activo') is True)
            stats['inactivos'] = stats['total'] - stats['activos']
            # -------------------------------------

    except requests.RequestException:
        messages.error(request, "Error de conexión al obtener métricas.")

    context = {
        'stats': stats, # Pasamos el diccionario completo
        'panel_title': 'Dashboard Administrativo'
    }
    return render(request, 'admin_panel/dashboard.html', context)

# -------------------------------------------------------------------
# 2. VISTA: Listar Usuarios
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url= '/account/login')
def listar_usuarios_view(request):
    # Obtener headers con token
    headers = get_auth_headers(request)
    if not headers:
        messages.error(request, "Sesión inválida. Por favor, inicia sesión nuevamente.")
        return redirect('account:login')

# 1. Obtener la lista de usuarios de la API de Node.js (Fuente de la verdad)
    print(f"DEBUG: Listando usuarios solicitados por {request.user.username}", file=sys.stderr)
    try:
        resp = requests.get(USUARIO_API_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            usuarios = resp.json() 
        else:
            messages.error(request, "Error al obtener la lista de usuarios de la API.")
            usuarios = []
            
    except requests.RequestException:
        messages.error(request, "Error de conexión con la API al listar usuarios.")
        usuarios = []

    context = {
        # Ahora pasamos la lista de usuarios directa de la API
        'usuarios': usuarios
    }
    return render(request, 'admin_panel/listar_usuarios.html', context)

# -------------------------------------------------------------------
# 3. VISTA: Editar Usuario (CRUD Update)
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url='/account/login')
def editar_usuario_view(request, username):
    # Obtener headers con token
    headers = get_auth_headers(request)
    if not headers:
        messages.error(request, "Sesión inválida. Por favor, inicia sesión nuevamente.")
        return redirect('account:login')
    
    # Restricción: No se permite la auto-edición de permisos
    if request.user.username == username:
        messages.error(request, "No puedes editar tu propio rol/estado desde esta vista.")
        return redirect('admin_panel:listar_usuarios')
        
    # 1. Obtener datos actuales de Firebase (Fuente de la verdad)
    usuario_firebase = {}
    current_rol = 'user'
    
    try:
        resp = requests.get(f"{USUARIO_API_URL}/username/{username}",
         headers=headers,
         timeout=5
        )

        if resp.status_code != 200: #sin exito
            messages.error(request, f"No se pudo cargar el perfil de {username} desde Firebase.")
            return redirect('admin_panel:listar_usuarios')
            
        usuario_firebase = resp.json()
        current_rol = usuario_firebase.get('rol', 'user')
        
    except requests.RequestException:
        messages.error(request, "Error de conexión con la API al cargar el usuario.")
        return redirect('admin_panel:listar_usuarios')

    # -------------------------------------------------------------------
    # Manejo POST (Actualizar)
    # -------------------------------------------------------------------
    if request.method == 'POST':
        form = RolUsuarioForm(request.POST)
        if form.is_valid():
            new_rol = form.cleaned_data['rol']
            
            # --- PROTECCIÓN PIN PARA PROMOVER A ADMIN ---
            if new_rol == 'admin':
                security_pin = request.POST.get('security_pin')
                if security_pin != '123':
                    messages.error(request, "PIN de seguridad incorrecto. No se puede asignar el rol de Administrador.")
                    return redirect('admin_panel:editar_usuario', username=username)
            # --------------------------------------------
            
            data_update = {
                'rol': new_rol,
                'securityPin': request.POST.get('security_pin') # Enviar PIN a la API
            }
            
            try:
                # 1. Llamada PUT a la API de Node.js para actualizar en Firebase
                resp_get = requests.get(
                    f"{USUARIO_API_URL}/username/{username}",
                    headers=headers,
                    timeout=5
                )

                target_uid = username

                if resp_get.status_code == 200:
                    user_data = resp_get.json()
                    # Buscamos el identificador técnico
                    target_uid = user_data.get('firebaseUid') or user_data.get('uid') or user_data.get('id')
                
                resp = requests.put(
                    f"{USUARIO_API_URL}/admin/update/{target_uid}",
                    json=data_update,
                    headers=headers,
                    timeout=5
                )
                if resp.status_code == 200:
                    messages.success(request, f"Rol de {username} actualizado a '{new_rol}' en Firebase.")
                    return redirect('admin_panel:listar_usuarios')
                else:
                    messages.error(request, f"Error API al actualizar rol (Código: {resp.status_code}).")
                    
            except requests.RequestException:
                messages.error(request, "Error de conexión con la API al intentar actualizar.")
    
    # -------------------------------------------------------------------
    # Manejo GET (Mostrar Formulario)
    # -------------------------------------------------------------------
    else:
        # Inicializar el formulario con los datos actuales obtenidos de Firebase
        form = RolUsuarioForm(initial={'rol': current_rol})

    context = {
        'form': form,
        'usuario': usuario_firebase, # Pasamos el dict de la API
        'current_rol': current_rol,
        'panel_title': f'Editar Usuario: {username}'
    }
    return render(request, 'admin_panel/editar_usuario.html', context)


# -------------------------------------------------------------------
# 4. VISTA: Eliminar Usuario (CRUD Delete)
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url='/account/login')
def eliminar_usuario_view(request, username):
    # Obtener headers con token
    headers = get_auth_headers(request)

    if not headers:
        messages.error(request, "Sesión inválida. Por favor, inicia sesión nuevamente.")
        return redirect('account:login')

    # Obtener datos del usuario para mostrar en el template 
    usuario_firebase = {'username': username} # Fallback mínimo
    try:
        resp = requests.get(f"{USUARIO_API_URL}/username/{username}", 
        headers=headers, 
        timeout=5
        )

        if resp.status_code == 200:
            usuario_firebase = resp.json()
            print(f"DEBUG: Datos usuario objetivo ({username}): {usuario_firebase}", file=sys.stderr)
    except Exception as e:
        print(f"DEBUG ERROR fetching user {username}: {e}", file=sys.stderr)
        pass
    
    # Restricción: No se permite la auto-eliminación
    if request.user.username == username:
        messages.error(request, "No puedes eliminar tu propia cuenta desde el panel de administración.")
        return redirect('admin_panel:listar_usuarios')

    # Restricción: No se permite eliminar a otros administradores
    # Restricción: No se permite eliminar a otros administradores SIN PIN
    if usuario_firebase.get('rol') == 'admin':
        # Esta verificación preliminar es para GET, en POST se valida el PIN
        if request.method == 'GET':
             messages.warning(request, "Atención: Estás a punto de eliminar a un Administrador. Se requerirá un PIN de seguridad.")
    
    if request.method == 'POST':
        try:
            # --- PROTECCIÓN PIN PARA ELIMINAR ADMIN ---
            if usuario_firebase.get('rol') == 'admin':
                security_pin = request.POST.get('security_pin')
                if security_pin != '123':
                    messages.error(request, "PIN de seguridad incorrecto. Eliminación de Administrador cancelada.")
                    return redirect('admin_panel:lista_usuarios') # Fallback seguro
            # ------------------------------------------
            # 1. Eliminar en Firebase (Node.js API)
            # Enviamos el PIN en el body (si la API lo soporta) o dependemos de headers
            delete_payload = {'securityPin': request.POST.get('security_pin')}
            
            resp = requests.delete(f"{USUARIO_API_URL}/username/{username}", 
            json=delete_payload,
            headers=headers, 
            timeout=5
            )

            if resp.status_code in [200, 204]: # 200 OK 
                messages.success(request, f"Usuario '{username}' eliminado correctamente de Firebase.")
                return redirect('admin_panel:listar_usuarios')
            
            elif resp.status_code == 401:
                messages.error(request, "No tienes permiso (Token no válido o expirado).")

            else:
                messages.error(request, f"Error API al eliminar usuario: {username} (Código: {resp.status_code}).")
                
        except requests.RequestException:
            messages.error(request, "Error de conexión con la API al intentar eliminar.")
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")

    # Renderiza la página de confirmación de eliminación (GET)
    context = {
        'usuario': usuario_firebase,
        'panel_title': f'Confirmar Eliminación: {username}'
    }
    return render(request, 'admin_panel/confirmar_eliminacion.html', context)