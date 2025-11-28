from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests

# Se puede usar la URL de settings.py, o definirla aquí directamente:
API_USUARIOS_URL = 'http://localhost:3000/api/usuarios' 

def login_view(request):
    # Si ya está autenticado, redirigir
    if request.user.is_authenticated:
        return redirect('home:index')
    
    if request.method == 'POST':
        # El input en HTML se llama 'username', pero representa el identificador (email o username)
        identifier = request.POST.get('username')
        password = request.POST.get('password')
        
        # Autenticar usando NodeAPIBackend
        # Pasamos 'identifier' explícitamente para que el backend lo use
        user = authenticate(request, identifier=identifier, password=password)
        print(f"DEBUG VIEWS: Resultado de authenticate: {user}")

        if user is not None:
            # ¡Éxito!
            # Convertimos el SimpleNamespace a dict
            request.session['user_session_data'] = user.__dict__
            
            # Opcional: Si necesitas manejar 'is_active' para onboarding
            if not getattr(user, 'is_active', True):
                 return redirect('home:completar_perfil')
            
            return redirect('home:index') 

        messages.error(request, 'Nombre de usuario o contraseña incorrectos.')

    return render(request, 'account/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home:index')

    if request.method == 'POST':
        data = {
            'nombre': request.POST.get('nombre', '').strip(),       
            'apellido': request.POST.get('apellido', '').strip(),   
            'email': request.POST.get('email', '').strip(),       
            'username': request.POST.get('username', '').strip(),
            'password': request.POST.get('password', ''),
        }

        try:
            api_base = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
            resp = requests.post(f"{api_base}/auth/register", json=data, timeout=10)
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con la API Node.js: {e}")
            messages.error(request, 'No pude conectar con la API.')
            return render(request, 'account/register.html', {'prefill': data})

        if resp.status_code == 201:
            messages.success(request, 'Cuenta creada con éxito. Ahora puedes iniciar sesión.')
            return redirect('account:login')

        try:
            msg = resp.json().get('error', 'Error desconocido al registrar el usuario.')
        except Exception:
            msg = f'Error inesperado (Código {resp.status_code}).'
            
        messages.error(request, msg)
        return render(request, 'account/register.html', {'prefill': data})

    return render(request, 'account/register.html')


def logout_view(request):
    # Limpiar sesión manual
    if 'user_session_data' in request.session:
        del request.session['user_session_data']
    
    logout(request) # Limpia cookies y sesión estándar
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('account:login')

@login_required
def index(request):
    return render(request, 'account/index.html')