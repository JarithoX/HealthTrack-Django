# seguimiento/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

# Importa tus formularios aquí (asumo que se llama forms.py)
from .forms import HabitoDefinicionForm # Asumo que el formulario es HabitoDefinicionForm

import requests
from datetime import date
import json

# --- DEFINICIÓN CENTRALIZADA DE URLS ---
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

# Definimos las URLs específicas
HABITO_DEFINICION_URL = f"{API_BASE_URL}/habito-definicion"
HABITO_REGISTRO_URL = f"{API_BASE_URL}/habito-registro"
# ---------------------------------------


@login_required
def crear_habito_view(request):
    # 🔹 1. Sacar token de la sesión
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, "Sesión expirada. Inicia sesión nuevamente.")
        return redirect('login')

    if request.method == 'POST':
        form = HabitoDefinicionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['id_usuario'] = request.user.username.lower() # Aseguramos minúsculas

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            try:
                resp = requests.post(
                    HABITO_DEFINICION_URL,
                    json=data,
                    headers=headers,
                    timeout=5
                )

                if resp.status_code == 201:
                    messages.success(request, f"Hábito '{data['nombre']}' creado con éxito.")
                    return redirect('habitos:registro_habito')
                else:
                    error_msg = resp.json().get('error', resp.text) if resp.content else "Error API desconocido."
                    messages.error(request, f"Error al crear hábito: {error_msg}")

            except requests.RequestException:
                messages.error(request, "Error de conexión con la API de Node.js.")

    else:
        form = HabitoDefinicionForm()

    context = {'form': form}
    return render(request, 'seguimiento/crear_habito.html', context)


@login_required
def registro_habitos_view(request):
    # 🔹 1. Normalización del Username (Necesario tanto para GET como para POST)
    username = request.user.username
    normalized_username = username.lower() 

    # 🔹 2. Configuración de Headers (Necesario tanto para GET como para POST)
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, "Sesión expirada. Inicia sesión nuevamente.")
        return redirect('login')
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # ------- POST: guardar registro individual -------
    if request.method == 'POST':
        # Obtenemos los campos del formulario
        id_habito_def = request.POST.get('id_habito_def')
        valor_registrado = request.POST.get('valor_registrado')
        comentario = request.POST.get('comentario')
        
        # Fecha del formulario o fecha actual
        fecha_registro = request.POST.get('fecha_registro', date.today().isoformat())

        # ⚠️ VALIDACIÓN FINAL EN DJANGO: Si el ID falla, detenemos aquí y damos un mensaje claro.
        if not id_habito_def:
            # Aquí se capturará si el HTML no envió el ID
            messages.error(request, "Error de envío: El identificador del hábito (id_habito_def) no fue recibido. Verifique la plantilla HTML.")
            return redirect('habitos:registro_habito')

        data_registro = {
            'id_habito_def': id_habito_def,
            # Enviamos el valor como viene (vacío para checkbox desmarcado, valor para numérico)
            'valor_registrado': valor_registrado, 
            'comentario': comentario,
            'fecha': fecha_registro,
            'id_usuario': normalized_username, # ✅ Aseguramos el envío del ID de usuario
        }
        
        # --- DEBUG FINAL EN DJANGO ---
        print(f"DEBUG DJANGO POST FINAL: Enviando a Node.js: {data_registro}")
        # -----------------------------

        try:
            resp = requests.post(
                HABITO_REGISTRO_URL, 
                json=data_registro,
                headers=headers,
                timeout=5
            )

            if resp.status_code == 201:
                messages.success(request, "¡Registro guardado con éxito!")
            else:
                # Intenta obtener el mensaje de error de la API (incluyendo el error 400 de Node.js)
                error_msg = resp.json().get('error', resp.text) if resp.content else f"Error API desconocido (código {resp.status_code})."
                messages.error(request, f"Error API al registrar: {error_msg}")

        except requests.RequestException:
            messages.error(request, "Error de conexión con la API de Node.js al intentar guardar.")

        return redirect('habitos:registro_habito')


    # ------- GET: Cargar definiciones de hábitos (Sin cambios, ya verificamos que funciona) -------
    if request.method == 'GET':
        habitos = []
        try:
            url_get = f"{HABITO_DEFINICION_URL}/{normalized_username}"
            
            response = requests.get(
                url_get, 
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                habitos = response.json()
            else:
                messages.error(request, f"Error al cargar las definiciones de hábitos: Código {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            messages.error(request, f"No se pudo conectar con la API de Node.js: {e}")
            
        context = {
            'definiciones': habitos, 
            'habitos': habitos,
            'fecha_actual': date.today().isoformat(),
        }
        return render(request, 'seguimiento/registrar_habito.html', context)


@login_required
def mi_progreso_view(request):
    username = request.user.username.lower()

    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, "Sesión expirada. Inicia sesión nuevamente.")
        return redirect('login')

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    registros = []

    try:
        url_progreso = f"{HABITO_REGISTRO_URL}/{username}"
        resp = requests.get(url_progreso, headers=headers, timeout=5)

        if resp.status_code == 200:
            registros = resp.json()
        else:
            # Manejamos error silenciosamente
            pass 

    except requests.RequestException:
        messages.error(request, "Error de conexión al obtener el progreso.")

    # -------------------------------------------------------
    # 📊 LÓGICA DE PROCESAMIENTO DE DATOS para el Gráfico
    # -------------------------------------------------------
    
    datos_por_habito = {}
    registros_ordenados = sorted(registros, key=lambda x: x['fecha'])

    for reg in registros_ordenados:
        nombre = reg.get('nombre_habito')
        valor = reg.get('valor_registrado')
        fecha = reg.get('fecha', '').split('T')[0]
        meta = reg.get('meta')
        tipo = reg.get('tipo_medicion')

        if nombre and nombre not in datos_por_habito:
            datos_por_habito[nombre] = {
                'fechas': [],
                'valores': [],
                'meta': meta,
                'tipo': tipo
            }
        
        if nombre:
            datos_por_habito[nombre]['fechas'].append(fecha)
            
            # Si es binario, guardamos 1 o 0. Si es número, el valor real.
            if tipo == 'Binario':
                datos_por_habito[nombre]['valores'].append(1 if valor else 0)
            else:
                datos_por_habito[nombre]['valores'].append(valor)

    # Convertimos a JSON string
    datos_grafico_json = json.dumps(datos_por_habito)

    context = {
        "registros": registros,
        "datos_grafico_json": datos_grafico_json,
        "lista_habitos": list(datos_por_habito.keys())
    }

    return render(request, 'seguimiento/mi_progreso.html', context)
    
    
@login_required
def eliminar_habito_view(request, id_habito):
    """
    Elimina una definición de hábito llamando a la API de Node.js
    """
    # 1. Configurar Headers (Token)
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, "Sesión expirada.")
        return redirect('login')
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    # 2. Llamada DELETE a Node.js
    try:
        url_delete = f"{HABITO_DEFINICION_URL}/{id_habito}"
        
        resp = requests.delete(url_delete, headers=headers, timeout=5)

        if resp.status_code == 200:
            messages.success(request, "Hábito eliminado correctamente.")
        else:
            error_msg = resp.json().get('error', resp.text) if resp.content else "Error API desconocido."
            messages.error(request, f"No se pudo eliminar: {error_msg}")

    except requests.RequestException:
        messages.error(request, "Error de conexión al intentar eliminar el hábito.")

    # Redirigir de vuelta a la lista de registros
    return redirect('habitos:registro_habito')