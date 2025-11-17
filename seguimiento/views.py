# seguimiento/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from .forms import *  # HabitoDefinicionForm, HabitoRegistroForm

import requests
from datetime import datetime, date, timedelta
from collections import defaultdict
import json

# URL BASE de tu API de Node.js
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')


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

            # Añade el username logueado como id_usuario
            data['id_usuario'] = request.user.username

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            try:
                resp = requests.post(
                    f"{API_BASE_URL}/habito-definicion",
                    json=data,
                    headers=headers,
                    timeout=5
                )

                if resp.status_code == 201:
                    messages.success(request, f"Hábito '{data['nombre']}' creado con éxito.")
                    return redirect('habitos:registro_habito')
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

    # 🔹 1. Token
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, "Sesión expirada. Inicia sesión nuevamente.")
        return redirect('login')

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # ------- POST: guardar registro diario -------
    if request.method == 'POST':
        id_habito_def = request.POST.get('id_habito_def')
        valor_registrado = request.POST.get('valor_registrado')
        comentario = request.POST.get('comentario')

        if not id_habito_def or not valor_registrado:
            messages.error(request, "Error: Faltan datos esenciales para el registro.")
            return redirect('habitos:registro_habito')

        data_registro = {
            'id_habito_def': id_habito_def,
            'valor_registrado': valor_registrado,
            'comentario': comentario,
            'fecha': (datetime.today() - timedelta(days=1)).isoformat(),
            'id_usuario': username,
        }

        try:
            resp = requests.post(
                f"{API_BASE_URL}/habito-registro",
                json=data_registro,
                headers=headers,
                timeout=5
            )

            if resp.status_code == 201:
                messages.success(request, "¡Registro guardado con éxito!")
            else:
                messages.error(request, f"Error API al registrar: {resp.text}")

        except requests.RequestException:
            messages.error(request, "Error de conexión con la API de Node.js al intentar guardar.")

        return redirect('habitos:registro_habito')

    # ------- GET: cargar lista de hábitos disponibles -------
    else:
        habitos = []
        try:
            resp = requests.get(
                f"{API_BASE_URL}/habito-definicion/{username}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=5
            )

            if resp.status_code == 200:
                definiciones = resp.json()

                for def_habito in definiciones:
                    registro_form = HabitoRegistroForm()
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


@login_required
def mi_progreso_view(request):
    """
    Vista para mostrar el progreso del usuario con un gráfico.
    Usa GET /api/habito-registro/:username
    """
    username = request.user.username

    # 🔹 Token
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
        resp = requests.get(
            f"{API_BASE_URL}/habito-registro/{username}",
            headers=headers,
            timeout=5
        )

        if resp.status_code == 200:
            registros = resp.json()
        else:
            messages.error(
                request,
                f"Error al obtener registros de hábitos: {resp.status_code} - {resp.text}"
            )

    except requests.RequestException:
        messages.error(request, "Error de conexión con la API de Node.js al obtener el progreso.")

    # ---- Transformar registros en datos para el gráfico ----
    # Conteo de registros por fecha
    conteo_por_fecha = defaultdict(int)

    for reg in registros:
        fecha_iso = reg.get("fecha")
        if not fecha_iso:
            continue
        fecha_simple = fecha_iso.split("T")[0]
        conteo_por_fecha[fecha_simple] += 1

    fechas_ordenadas = sorted(conteo_por_fecha.keys())
    labels = fechas_ordenadas
    data = [conteo_por_fecha[f] for f in fechas_ordenadas]

    # Si no hay datos reales, simulamos para que el gráfico no quede vacío
    if not labels:
        labels = [
            (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(6, -1, -1)
        ]
        data = [0, 1, 0, 2, 1, 3, 2]

    context = {
        "labels_json": json.dumps(labels),
        "data_json": json.dumps(data),
        "registros": registros,
    }

    return render(request, 'seguimiento/mi_progreso.html', context)
