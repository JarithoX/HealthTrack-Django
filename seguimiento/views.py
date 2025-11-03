# Este es el archivo: seguimiento/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from django.conf import settings # Para usar API_BASE_URL
from .forms import *

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

#==============================
#Nueva logica
#=============================

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

@login_required
def crear_habito_view(request):
    if request.method == 'POST':
        form = HabitoDefinicionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Añade el username logueado como id_usuario
            data['id_usuario'] = request.user.username 
            
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/habito-definicion",
                    json=data,
                    timeout=5
                )
                
                if resp.status_code == 201:
                    messages.success(request, f"Hábito '{data['nombre']}' creado con éxito.")
                    return redirect('habitos:registro_habito') # Redirige a la página de registro
                else:
                    messages.error(request, f"Error al crear hábito: {resp.text}")
                    
            except requests.RequestException:
                messages.error(request, "Error de conexión con la API de Node.js.")
                
    else:
        form = HabitoDefinicionForm()
        
    context = {'form': form}
    return render(request, 'seguimiento/crear_habito.html', context)


@login_required
def registro_habitos_view(request):
    username = request.user.username

    #Manejar el POST (Guardar un Registro Diario)
    if request.method == 'POST':
        # Obtenemos los datos del POST (el formulario del hábito que se envió)
        # Todos los campos son "ocultos" excepto el valor_registrado.
        id_habito_def = request.POST.get('id_habito_def')
        valor_registrado = request.POST.get('valor_registrado')
        comentario = request.POST.get('comentario')

        if not id_habito_def or not valor_registrado:
            messages.error(request, "Error: Faltan datos esenciales para el registro.")
            return redirect('habitos:registro_habito')
        
        # Datos a enviar a la API
        data_registro = {
            'id_habito_def': id_habito_def,
            'valor_registrado': valor_registrado,
            'comentario': comentario,
            'fecha': datetime.today().isoformat(), # Formato ISO para la API
            'id_usuario': username,
        }

        try:
            resp = requests.post(
                f"{API_BASE_URL}/habito-registro",
                json=data_registro,
                timeout=5
            )
            
            if resp.status_code == 201:
                # Opcional: Obtener el nombre del hábito si lo necesitas para el mensaje
                # (Por simplicidad, usamos un mensaje genérico)
                messages.success(request, f"¡Registro guardado con éxito!")
            else:
                messages.error(request, f"Error API al registrar: {resp.text}")
                
        except requests.RequestException:
            messages.error(request, "Error de conexión con la API de Node.js al intentar guardar.")

        return redirect('habitos:registro_habito')
    
    # Manejar el GET (Obtener y Mostrar la Lista)
    else:
        habitos = []
        try:
            # 1. Llamada a la API de Node.js para obtener las Definiciones de Hábito
            resp = requests.get(
                f"{API_BASE_URL}/habito-definicion/{username}",
                timeout=5
            )
            
            if resp.status_code == 200:
                # La API debe devolver un array de objetos (predefinidos + propios)
                definiciones = resp.json() 
                
                # 2. Creamos un formulario de registro (diario) por cada definición de hábito
                for def_habito in definiciones:
                    # Instanciamos el HabitoRegistroForm, pero no lo llenamos con datos
                    registro_form = HabitoRegistroForm()
                    
                    # Añadimos datos de la definición al objeto para renderizar
                    def_habito['registro_form'] = registro_form
                    
                    habitos.append(def_habito)
                    
            else:
                messages.error(request, f"Error al cargar hábitos: {resp.text}")
                
        except requests.RequestException:
            messages.error(request, "Error de conexión con la API de Node.js al cargar la lista de hábitos.")
            
        
        context = {
            'habitos': habitos,
            'fecha_actual': datetime.today(),
        }
        return render(request, 'seguimiento/registrar_habito.html', context)
