# Este es el archivo: seguimiento/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from .forms import HabitoForm 

import requests  
from datetime import datetime

# URL BASE de tu API de Node.js
NODE_API_URL = 'http://localhost:3000' 

@login_required 
def habitos_registrar(request):
    # 1. Inicializa el formulario para la petición GET o para el POST fallido
    if request.method == 'POST':
        form = HabitoForm(request.POST)
    else:
        form = HabitoForm()
        
    # 2. PROCESA el POST
    if request.method == 'POST' and form.is_valid():
        datos = form.cleaned_data
        
        payload = {
            'calorias': datos['calorias'],
            'pasos': datos['pasos'],
            'horas_sueno': datos['horas_sueno'],
            'litros_agua': datos['litros_agua'],
            'comentario': datos['comentario'],
            'username': request.user.username, 
            'fecha': datetime.now().isoformat() 
        }
        
        try:
            api_endpoint = f'{NODE_API_URL}/api/habitos' 
            response = requests.post(api_endpoint, json=payload)
            
            if response.status_code == 201 or response.status_code == 200:
                messages.success(request, '¡Tu hábito se registró con éxito!')
                # ↓↓↓ REDIRECCIÓN EXITOSA, TERMINA LA FUNCIÓN ↓↓↓
                return redirect('habitos_listar') 
            else:
                # Si Node.js falla, mostramos el error y el código CONTINÚA
                error_msg = response.json().get('error', f'Error: {response.status_code}')
                messages.error(request, f'No se pudo guardar: {error_msg}')

        except requests.exceptions.ConnectionError:
            messages.error(request, 'Error de conexión: El servidor Node.js no está corriendo.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error inesperado: {e}')
            
    
    contexto = {'form': form}
    return render(request, 'seguimiento/registro_habitos.html', contexto)

@login_required
def habitos_listar(request):
    NODE_API_URL = 'http://localhost:3000' 
    
    try:
        
        username = request.user.username
        api_endpoint = f'{NODE_API_URL}/api/habitos/{username}' 
        
        response = requests.get(api_endpoint)
        
        if response.status_code == 200:
            
            habitos = response.json().get('habitos', [])
        else:
            messages.error(request, f'No se pudieron obtener los hábitos. Código {response.status_code}')
            habitos = []
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Error de conexión: Asegúrate de que tu servidor Node.js esté funcionando.')
        habitos = []
    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado: {e}')
        habitos = []
    contexto = {'habitos': habitos}
    return render(request, 'seguimiento/lista_habitos.html', contexto)


