from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests

from django.contrib.auth.models import User

# URL de la API de Node.js: se puede definir en settings.py o directamente aquí
# Si no usas settings.py, usa esta:
API_USUARIOS_URL = 'http://localhost:3000/api/usuarios' 


def login_view(request):
    # La lógica de autenticación actual usa el backend de Django (base de datos local).
    # Para usar el usuario creado en Firestore, necesitarías un Custom Authentication Backend.
    # Por ahora, mantendremos esta lógica si tienes usuarios de prueba en Django.
    if request.user.is_authenticated:
        return redirect('home:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            username = request.user.username
            # 🚨 LÓGICA DE ONBOARDING POST-LOGIN 🚨
            try:
                # 1. Consultar el perfil del usuario a la API de Node.js/Firestore
                #    (Asumimos un endpoint GET /api/usuarios/{username})
                resp = requests.get(f"{API_USUARIOS_URL}/usuarios/username/{username}", timeout=5)
                
                if resp.status_code == 200:
                    user_data = resp.json()
                    
                # 🚨 LÓGICA DE VERIFICACIÓN SIMPLIFICADA 🚨
                    is_active = user_data.get('activo', False) # Por defecto, si el campo no existe, es False
                    
                    if not is_active:   
                        messages.warning(request, "Bienvenido. Por favor, completa tu perfil para continuar.")
                        # Redirigir a la vista de Onboarding
                        return redirect('home:completar_perfil')
                    
                # Si la API falla (ej. 404), o si el perfil está completo
                return redirect('home:index')
                
            except requests.RequestException:
                # Si la API de Node.js no está corriendo, asume que debe ir al index.
                # Es mejor loguear al usuario que bloquearlo si la API tiene un fallo temporal.
                messages.warning(request, "Error al verificar el estado del perfil. Continuar bajo tu propia responsabilidad.")
                return redirect('home:index')
        
        # Si el usuario no existe en la DB local, pero sí en Firestore, el login fallará.
        messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    return render(request, 'account/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home:index')

    if request.method == 'POST':
        # 🚨 CORRECCIÓN CLAVE: Mapear campos del formulario HTML a la estructura esperada por la API Node.js/Firestore
        data = {
            'nombre': request.POST.get('nombre', '').strip(),       
            'apellido': request.POST.get('apellido', '').strip(),   
            'email': request.POST.get('email', '').strip(),       
            'username': request.POST.get('username', '').strip(),
            'password': request.POST.get('password', ''),
        }

        # Llamada a tu API Node → Firestore
        try:
            # Puedes usar API_USUARIOS_URL definida arriba o la de settings.
            api_base = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
            resp = requests.post(f"{api_base}/usuarios", json=data, timeout=10)
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con la API Node.js: {e}")
            messages.error(request, 'No pude conectar con la API. Asegúrate de que Node.js esté corriendo en http://localhost:3000.')
            return render(request, 'account/register.html', {'prefill': data})

        if resp.status_code == 201:
            # 💡 Paso opcional: Crear el usuario en la DB local de Django para que el login_view funcione
            try:
                # Comprobar si el usuario ya existe para evitar errores (aunque la API debería ser la fuente principal de unicidad)
                if not User.objects.filter(username=data['username']).exists():
                    User.objects.create_user(
                        username=data['username'],
                        email=data['email'],
                        # ⚠️ Importante: Usar la contraseña en texto plano para crear el usuario local.
                        # El login_view de Django la hasheará automáticamente.
                        password=data['password'] 
                    )
                messages.success(request, 'Cuenta creada con éxito. Ahora puedes iniciar sesión.')
                return redirect('login')
                
            except Exception as e:
                 # Si falla la creación local, notifica pero igual redirige al login (el usuario está en Firestore)
                print(f"Advertencia: Falló la creación del usuario local en Django. {e}")
                messages.warning(request, 'Cuenta creada en la base de datos de salud, pero el login en esta web podría fallar.')
                return redirect('login')


        # Manejo de errores devueltos por la API de Node.js (400, 409, etc.)
        try:
            msg = resp.json().get('error', 'Error desconocido al registrar el usuario.')
        except Exception:
            # Si la API no devuelve JSON (ej. 500 error en Node.js)
            msg = f'Error inesperado al registrar usuario (Código {resp.status_code}).'
            print(f"Respuesta de la API no válida: {resp.text}")
            
        messages.error(request, msg)
        return render(request, 'account/register.html', {'prefill': data})

    return render(request, 'account/register.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('login')

@login_required
def index(request):
    return render(request, 'account/index.html')