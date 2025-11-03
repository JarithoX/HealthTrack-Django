from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests

from django.contrib.auth.models import User

# Se puede usar la URL de settings.py, o definirla aquí directamente:
API_USUARIOS_URL = 'http://localhost:3000/api/usuarios' 

def login_view(request):
    # La lógica de autenticación actual usa el account/backend.py para consultar en firebase.
    if request.user.is_authenticated:
        return redirect('home:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # 🚨 LÓGICA DE ONBOARDING POST-LOGIN - USANDO EL CAMPO LOCAL user.is_active🚨
            
            if not user.is_active:
                    messages.warning(request, "Bienvenido. Completa tu perfil.")
                    return redirect('home:completar_perfil')   
            #Si is_active es True, va al home 
            return redirect('home:index') 

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
            api_base = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api') #Configurada en settings.py
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