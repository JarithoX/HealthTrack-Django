from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from .forms import PerfilConfigForm 

API_BASE_URL = 'http://localhost:3000/api' 

def get_api_data(endpoint):
    """Función auxiliar para consultar la API."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        # En producción, esto debería loguearse o mostrarse como un error de conexión
        pass
    return []

# VISTA DE ONBOARDING
@login_required
def completar_perfil_view(request):
    username = request.user.username # estamos usando el username como ID de Firestore. 

    # Si el perfil ya está completo, redirige al index
    usuario_activo = request.user.is_active
    if usuario_activo is True:
        print("Perfil ya completado, redirigiendo al index.")
        return redirect('home:index')

    if request.method == 'POST':
        form = PerfilConfigForm(request.POST)

        if form.is_valid():
            payload = form.cleaned_data.copy() # Datos limpios y validos
            payload['activo'] = True #Para que vea solo una vez el onboarding  
            payload = {k: v for k, v in payload.items() if v not in (None, '', [])} # elimina campos vacíos (None, '', [])                    
            
            # Autenticación con token de sesión (Implementacion futura)
            """"
                        headers = {}
            token = request.session.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
            """
            try:
                # 1. Llamada al endpoint PUT de Node.js
                resp = requests.put(
                    f"{API_BASE_URL}/usuarios/perfil/{username}", 
                    json = payload, 
                    #headers = headers,  -> Implementacion Token futura
                    timeout = 10
                )

                # Manejo de respuestas
                status = resp.status_code 

                if status in (200, 204):
                    messages.success(request, '¡Perfil completado! Bienvenido.')
                    return redirect('home:index') 
                
                elif status in (400, 422):
                    try:
                        msg = resp.json().get('error') or resp.text
                    except ValueError:
                        msg = resp.text
                    messages.error(request, f"Error de validación al completar el perfil: {msg[:200]}") 
                    # cae al render con el form ya con datos del POST

                elif status in (401, 403):
                    request.session.flush() #logout
                    messages.error(request, "Sesión inválida/expirada. Inicia sesión nuevamente.")
                    return redirect('account:login')
                
                elif status == 404: # Usuario no existe en la API
                    messages.warning(request, 
                        "Tu usuario no existe aún en la API. Intenta registrarte nuevamente."
                    )
                    return redirect('account:register')
                
                else: # Otros errores de la api
                    messages.error(request, f"Error en la API ({status}). Intenta más tarde.")
                    
            except requests.Timeout:
                messages.error(request, "La API tardó demasiado en responder.")
            except requests.ConnectionError:
                messages.error(request, "No se pudo conectar con la API. ¿Está la API arriba?")
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")

    else:
        form = PerfilConfigForm()

    context = {
        'form': form,
        'titulo': 'Completa tu Perfil',
        'username': username
    }
    
    return render(request, 'home/completar_perfil.html', context)


# VISTA DE home/index.html (Si el perfil ya está completo)
@login_required
def index(request):
    username = request.user.username

    # 1. Obtener datos del perfil del usuario (para consejos personalizados)
    # Endpoint: GET /api/usuarios/username/:username (asumiendo que devuelve {nombre, peso, altura, etc.})
    perfil_data = get_api_data(f"/usuarios/username/{username}")
    
    # 2. Obtener Hábitos Predefinidos (para la sección de Acción Rápida)
    # Endpoint: GET /api/habitos/predefinidos (ASUMIDO, NECESITAS CREAR ESTE ENDPOINT)
    habitos_predefinidos = get_api_data("/habitos/predefinidos")
    
    # Limitamos a 4 hábitos para el dashboard
    habitos_predefinidos_top = habitos_predefinidos[:4] 

    # 3. Obtener Listado de Profesionales (para la sección Social)
    # Endpoint: GET /api/usuarios/profesionales (ASUMIDO, NECESITAS CREAR ESTE ENDPOINT)
    profesionales = get_api_data("/usuarios/profesionales")
    profesionales_top = profesionales[:3] # Limitamos a 3

    context = {
        'username': username,
        #'nombre_usuario': perfil_data.get('nombre', username), # Usar el nombre si existe
        
        # Datos para las secciones del home
        'perfil_data': perfil_data,
        'habitos_predefinidos': habitos_predefinidos_top,
        'profesionales': profesionales_top,
    }

    return render(request, 'home/index.html', context)
