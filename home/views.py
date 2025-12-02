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
    # Usamos el UID técnico para la API, no el username visual
    uid = request.user.uid 

    # Si el perfil ya está completo, redirige al index
    usuario_activo = request.user.is_active
    if usuario_activo is True:
        print("Perfil ya completado, redirigiendo al index.")
        return redirect('home:index')

    if request.method == 'POST':
        form = PerfilConfigForm(request.POST)

        if form.is_valid():
            payload = form.cleaned_data.copy() # Datos limpios y validos
            payload['hora_despertar'] = str(payload['hora_despertar'])
            payload['hora_dormir'] = str(payload['hora_dormir'])
            payload['activo'] = True #Para que vea solo una vez el onboarding  
            payload = {k: v for k, v in payload.items() if v not in (None, '', [])} # elimina campos vacíos (None, '', [])                    
            
            # Autenticación con token de sesión (Implementacion futura)
            print(f"DEBUG HOME: Enviando payload a API: {payload}")
            """"
                        headers = {}
            token = request.session.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
            """
            try:
                # 1. Llamada al endpoint PUT de Node.js
                resp = requests.put(
                    f"{API_BASE_URL}/usuarios/perfil/{uid}", 
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
        'username': request.user.username # Visual
    }
    
    return render(request, 'home/completar_perfil.html', context)


# VISTA DE home/index.html (Si el perfil ya está completo)
@login_required
def index(request):
    # 1 Recuperar datos del usuario desde la sesión
    # Tambien se puede obtener de la API
    user_data = request.session.get('user_session_data', {})
    token = user_data.get('token')

    # Obtener la lista de objetivos
    # Si no hay objetivos, se muestra una lista vacía
    mis_objetivos = user_data.get('objetivos', [])

    # 2. Diccionario Maestro de Recomendaciones (Hardcoded por ahora)
    # Clave = El value del checkbox del Wizard
    recomendaciones = []
    
    try:
        # Preparamos headers (aunque este endpoint podría ser público, mejor enviar token por si acaso)
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        # Enviamos los objetivos a la API para que nos devuelva las plantillas coincidentes
        response = requests.post(
            f"{API_BASE_URL}/habitos-recomendados",
            json={'objetivos': mis_objetivos},
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            respuesta_json = response.json() 
            recomendaciones = respuesta_json.get('data', [])  # Lista de objetos desde Firebase
            print('DEBUG: Recomendaciones: ', recomendaciones)
        else:
            print(f"Error API Recomendaciones: {response.status_code} - {response.text}")

    except requests.RequestException as e:
        print(f"Error de conexión API: {e}")
        # Recomendaciones estará vacío, el template lo manejará

    # 3. Contexto para el Template
    context = {
        'recomendaciones': recomendaciones, # Ahora son datos reales de Firebase
        'nombre_usuario': request.user.username,
        # Aquí iría la lógica de racha futura
        'racha_dias': 0 
    }
    return render(request, 'home/index.html', context)
