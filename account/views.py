from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Si ya está autenticado, va al home
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Al iniciar sesión, va al home
    return render(request, 'account/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        data = {
            'nombres': request.POST.get('nombres', '').strip(),
            'apellidos': request.POST.get('apellidos', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'edad': request.POST.get('fecha_nacimiento', '').strip(),  # YYYY-MM-DD
            'sexo': request.POST.get('sexo', '').strip(),
            'condiciones_medicas': request.POST.get('condiciones_medicas', '').strip(),
            'username': request.POST.get('username', '').strip(),
            'password': request.POST.get('password', ''),
        }

        # Llamada a tu API Node → Firestore
        try:
            api_base = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
            resp = requests.post(f"{api_base}/usuarios", json=data, timeout=10)
        except requests.RequestException:
            messages.error(request, 'No pude conectar con la API. ¿Está corriendo en http://localhost:3000?')
            return render(request, 'account/register.html', {'prefill': data})

        if resp.status_code == 201:
            # OPCIONAL: crear también el usuario local de Django para que tu login actual funcione
            try:
                if not User.objects.filter(username=data['username']).exists():
                    User.objects.create_user(
                        username=data['username'],
                        email=data['email'],
                        password=data['password']
                    )
            except Exception:
                # No bloquear el registro si falla la creación local
                pass

            messages.success(request, 'Cuenta creada con éxito. Inicia sesión.')
            return redirect('login')

        # Errores de la API
        try:
            msg = resp.json().get('error', 'No se pudo registrar el usuario.')
        except Exception:
            msg = 'No se pudo registrar el usuario.'
        messages.error(request, msg)
        return render(request, 'account/register.html', {'prefill': data})

    return render(request, 'account/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def index(request):
    return render(request, 'account/index.html')
