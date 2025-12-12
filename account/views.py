from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests
import sys

def login_view(request):
    # Si ya está autenticado, redirigir según el rol
    if request.user.is_authenticated:
        user_rol = getattr(request.user, 'rol', None)
        if user_rol == 'admin':
            return redirect('admin_panel:dashboard')
        elif user_rol == 'profesional':
            return redirect('professional_panel:dashboard')
        else:  # Rol 'user' o sin rol definido
            return redirect('home:index')
    
    if request.method == 'POST':
        try:
            # El input en HTML se llama 'username', pero representa el identificador (email o username)
            identifier = request.POST.get('username')
            password = request.POST.get('password')
            
            # Autenticar usando NodeAPIBackend
            # Pasamos 'identifier' explícitamente para que el backend lo use
            user = authenticate(request, identifier=identifier, password=password)

            if user is not None:
                session_data = {
                    'uid': user.uid,
                    'username': user.username,
                    'email': user.email,
                    'rol': getattr(user, 'rol', 'user'),
                    'token': getattr(user, 'token', ''),
                    'is_active': getattr(user, 'is_active', True),
                    'is_staff': getattr(user, 'is_staff', False),
                    'is_superuser': getattr(user, 'is_superuser', False),
                }

                # --- DEBUGGING SESSION SIZE ---
                try:
                    import json
                    session_json = json.dumps(session_data)
                    size_bytes = len(session_json.encode('utf-8'))
                    print(f"DEBUG SESSION SIZE: {size_bytes} bytes", file=sys.stderr)
                    if size_bytes > 3800:
                        print("WARNING: Session data is VERY close to the 4KB cookie limit!", file=sys.stderr)
                except Exception as e:
                    print(f"Error calculating session size: {e}", file=sys.stderr)
                # ------------------------------

                request.session['user_session_data'] = session_data

                request.session.modified = True
                
                # Redirección basada en roles
                user_rol = session_data.get('rol') # Usamos el dato limpio
                if user_rol == 'admin':
                    return redirect('admin_panel:dashboard')
                elif user_rol == 'profesional':
                    return redirect('professional_panel:dashboard')
                
                # Lógica para usuarios normales (rol 'user' o sin rol definido)
                # Para manejar 'is_active' al onboarding
                if not session_data.get('is_active', True):
                     return redirect('home:completar_perfil')
                
                return redirect('home:index') 

            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')

        except Exception as e:
            import traceback
            print(f"CRITICAL ERROR IN LOGIN_VIEW: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            messages.error(request, 'Ocurrió un error inesperado al iniciar sesión. Por favor, intenta de nuevo.')

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
            api_base = settings.API_BASE_URL
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