from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.conf import settings
from .forms import RolUsuarioForm
from django.db import transaction # importación para eliminación atómica
from django.contrib import messages
import requests # Para comunicarse con la API de Node.js (Firebase)

User = get_user_model() 
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
USUARIO_API_URL = f"{API_BASE_URL}/usuarios" # Ajusta si tu endpoint es diferente

# Helper: Verifica si el usuario es Admin o Superuser (is_staff es suficiente para el panel)
def is_admin_or_staff(user):
    return user.is_active and (user.is_staff or user.is_superuser)

# -------------------------------------------------------------------
# 1. VISTA: Dashboard Administrativo
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url='/account/login') # Protege el acceso
def admin_dashboard_view(request):
    # Por ahora, un simple dashboard. Aquí irán estadísticas y gráficos más tarde.
    context = {
        'total_usuarios': User.objects.count(),
        'panel_title': 'Dashboard Administrativo'
    }
    return render(request, 'admin_panel/dashboard.html', context)

# -------------------------------------------------------------------
# 2. VISTA: Listar Usuarios
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url= '/account/login')
def listar_usuarios_view(request):
# 1. Obtener la lista de usuarios de la API de Node.js (Fuente de la verdad)
    try:
        resp = requests.get(USUARIO_API_URL, timeout=5)
        if resp.status_code == 200:
            data_firebase = resp.json() 
        else:
            messages.error(request, "Error al obtener la lista de usuarios de la API.")
            data_firebase = []
            
    except requests.RequestException:
        messages.error(request, "Error de conexión con la API al listar usuarios.")
        data_firebase = []

    # 2. Crea un diccionario de mapeo {username: data_completa}
    firebase_map = {user.get('username'): user for user in data_firebase if user.get('username')}
    # 3. Obtener todos los usuarios locales de Django
    usuarios_locales = User.objects.exclude(username=request.user.username).order_by('username')
    # 4. Combinar datos: Crear una nueva lista de DICCIONARIOS
    usuarios_combinados = []

    for user_local in usuarios_locales:
        username = user_local.username
        firebase_data = firebase_map.get(username, {})
        
        firebase_rol = firebase_data.get('rol', '-')
        is_activo_firebase = firebase_data.get('activo','-')
        
        combinado = {
            'username': username,
            'email': user_local.email,
            'is_staff': user_local.is_staff,
            
            # Datos de Firebase
            'firebase_rol': firebase_rol,
            
            'activo': 'Sí' if str(is_activo_firebase).lower() == 'true' else 'No',
        }
        
        usuarios_combinados.append(combinado)
        
    context = {
        # Ahora pasamos la lista de usuarios enriquecida
        'usuarios': usuarios_combinados
    }
    return render(request, 'admin_panel/listar_usuarios.html', context)

# -------------------------------------------------------------------
# 3. VISTA: Editar Usuario (CRUD Update)
# -------------------------------------------------------------------
@login_required
@user_passes_test(is_admin_or_staff, login_url='/account/login')
def editar_usuario_view(request, username):
    
    # Restricción: No se permite la auto-edición de permisos
    if request.user.username == username:
        messages.error(request, "No puedes editar tu propio rol/estado desde esta vista.")
        return redirect('admin_panel:listar_usuarios')
        
    usuario_local = get_object_or_404(User, username=username)
    
    # 1. Obtener datos actuales de Firebase (Fuente de la verdad)
    try:
        resp = requests.get(f"{USUARIO_API_URL}/username/{username}", timeout=5)
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
            
            data_update = {
                'rol': new_rol,
            }
            
            try:
                # 1. Llamada PUT a la API de Node.js para actualizar en Firebase
                resp = requests.put(
                    f"{USUARIO_API_URL}/perfil/{username}",
                    json=data_update,
                    timeout=5
                )
                
                if resp.status_code == 200:
                    # 2. Sincronizar Permisos en la BD Local de Django
                    usuario_local.is_staff = (new_rol in ['admin', 'profesional'])
                    usuario_local.is_superuser = (new_rol == 'admin')
                    usuario_local.save()
                    
                    messages.success(request, f"Rol de {username} actualizado a '{new_rol}' en Firebase y Django.")
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
        'usuario': usuario_local,
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

    jwt_token = request.session.get('jwt_token')
    
    if not jwt_token:
        messages.error(request, "Error de seguridad: Token no encontrado. Vuelve a iniciar sesión.")
        return redirect('logout') 

    # diccionario de headers para incluir el token 
    headers = {
        'x-token': jwt_token,  # El nombre del header que el Middleware de Node.js espera
        'Content-Type': 'application/json' 
    }
    
    # Restricción: No se permite la auto-eliminación
    if request.user.username == username:
        messages.error(request, "No puedes eliminar tu propia cuenta desde el panel de administración.")
        return redirect('admin_panel:listar_usuarios')
        
    usuario_local = get_object_or_404(User, username=username)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Eliminar en Firebase (Node.js API)
                resp = requests.delete(f"{USUARIO_API_URL}/username/{username}", headers=headers, timeout=5)

                if resp.status_code in [200]: # 200 OK 
                    # 2. Eliminar en la BD local de Django
                    usuario_local.delete()
                    messages.success(request, f"Usuario '{username}' eliminado correctamente de Firebase y Django.")
                    return redirect('admin_panel:listar_usuarios')
                
                elif resp.status_code == 401:
                    messages.error(request, "No tienes permiso (Token no válido o expirado).")

                else:
                    if resp.status_code == 404 and usuario_local in User.objects.all():
                        # Si no existe en Firebase pero sí en Django, eliminar localmente
                        usuario_local.delete()

                        messages.success(request, f"Usuario '{username}' eliminado correctamente BD-Local Django.")
                        return redirect('admin_panel:listar_usuarios')
                    
                    messages.error(request, f"Error API al eliminar usuario: {usuario_local} (Código: {resp.status_code}).")
                    
        except requests.RequestException:
            messages.error(request, "Error de conexión con la API al intentar eliminar.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el usuario local: {e}")

    # Renderiza la página de confirmación de eliminación (GET)
    context = {
        'usuario': usuario_local,
        'panel_title': f'Confirmar Eliminación: {username}'
    }
    return render(request, 'admin_panel/confirmar_eliminacion.html', context)