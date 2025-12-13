from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
import requests

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')
USUARIO_API_URL = f"{API_BASE_URL}/usuarios"

@login_required
def mi_perfil_view(request):
    # 1. Obtener datos básicos de la sesión
    user_session = request.session.get('user_session_data', {})
    token = user_session.get('token')
    username = request.user.username

    user_data = user_session # Fallback inicial

    # 2. Intentar obtener el perfil completo desde la API (Firebase)
    if token and username:
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(f"{USUARIO_API_URL}/username/{username}", headers=headers, timeout=5)
            
            if resp.status_code == 200:
                user_data = resp.json()
                # Opcional: Actualizar la sesión con los datos frescos (cuidado con el token)
                # user_data['token'] = token 
                # request.session['user_session_data'] = user_data
            else:
                print(f"Error al obtener perfil: {resp.status_code}")
                # No mostramos error al usuario para no interrumpir, usamos datos de sesión
        except requests.RequestException as e:
            print(f"Error de conexión API: {e}")

    # 3. Enriquecer objetivos con metadatos (iconos, textos)
    objetivos_usuario = user_data.get('objetivos', [])
    objetivos_enriquecidos = []

    OBJETIVOS_METADATA = {
        'vivir_saludable': {'icon': 'bi-heart-pulse-fill', 'label': 'Vivir más saludable', 'color': 'text-danger'},
        'aliviar_presion': {'icon': 'bi-flower1', 'label': 'Aliviar estrés', 'color': 'text-success'},
        'probar_cosas': {'icon': 'bi-stars', 'label': 'Probar cosas nuevas', 'color': 'text-warning'},
        'centrarme': {'icon': 'bi-bullseye', 'label': 'Centrarme más', 'color': 'text-primary'},
        'mejor_relacion': {'icon': 'bi-people-fill', 'label': 'Mejorar relaciones', 'color': 'text-info'},
        'dormir_mejor': {'icon': 'bi-moon-fill', 'label': 'Dormir mejor', 'color': 'text-dark'},
    }

    if objetivos_usuario:
        for obj_key in objetivos_usuario:
            meta = OBJETIVOS_METADATA.get(obj_key)
            if meta:
                objetivos_enriquecidos.append(meta)
            else:
                # Fallback para objetivos desconocidos
                objetivos_enriquecidos.append({'icon': 'bi-check-circle', 'label': obj_key, 'color': 'text-secondary'})

    context = {
        'usuario': user_data,
        'objetivos_enriquecidos': objetivos_enriquecidos,
        'panel_title': 'Mi Perfil'
    }
    return render(request, 'perfiles/mi_perfil.html', context)

from .forms import EditarPerfilForm, CambiarPasswordForm, EditarPerfilSimpleForm
import sys
import traceback

@login_required
def editar_perfil_view(request):
    try:
        user_session = request.session.get('user_session_data', {})
        token = user_session.get('token')
        uid = user_session.get('uid') or request.user.uid
        
        # Datos iniciales (mezcla de sesión y user actual)
        initial_data = user_session.copy()

        # ---------------------------------------------------------
        # FETCH DATOS FRESCOS PARA PRE-POBLAR EL FORMULARIO
        # ---------------------------------------------------------
        if token and user_session.get('username'):
            try:
                username = user_session.get('username')
                headers_api = {'Authorization': f'Bearer {token}'}
                # Reutilizamos la URL de ver perfil
                resp_fresh = requests.get(f"{USUARIO_API_URL}/username/{username}", headers=headers_api, timeout=4)
                if resp_fresh.status_code == 200:
                    fresh_data = resp_fresh.json()
                    # Actualizamos initial_data con lo que viene de la BD
                    initial_data.update(fresh_data)
                    # Opcional: refrescar la sesión también para que no se quede vieja
                    request.session['user_session_data'].update(fresh_data)
                    request.session.modified = True
            except Exception as e:
                print(f"Warning: No se pudo refrescar datos perfil para edición: {e}", file=sys.stderr)
        # ---------------------------------------------------------
        
        # Asegurar formatos de hora para el formulario
        if 'hora_despertar' in initial_data:
            initial_data['hora_despertar'] = str(initial_data['hora_despertar'])
        if 'hora_dormir' in initial_data:
            initial_data['hora_dormir'] = str(initial_data['hora_dormir'])
            
        # Seleccionar formulario según rol
        FormClass = EditarPerfilForm
        if user_session.get('rol') != 'user':
            FormClass = EditarPerfilSimpleForm

        if request.method == 'POST':
            form = FormClass(request.POST, initial=initial_data)
            if form.is_valid():
                payload = form.cleaned_data.copy()
                
                # Convertir horas a string (solo si existen)
                if 'hora_despertar' in payload:
                    payload['hora_despertar'] = str(payload['hora_despertar'])
                if 'hora_dormir' in payload:
                    payload['hora_dormir'] = str(payload['hora_dormir'])
                
                # Limpiar datos vacíos GENERAL
                payload = {k: v for k, v in payload.items() if v not in (None, '', [])}
                
                print(f"DEBUG PERFIL COMPLETE PAYLOAD: {payload}", file=sys.stderr)

                # --- SEPARACIÓN DE PAYLOADS (Identidad vs Perfil) ---
                identity_fields = ['nombre', 'apellido', 'email', 'username']
                identity_payload = {k: v for k, v in payload.items() if k in identity_fields}
                profile_payload = {k: v for k, v in payload.items() if k not in identity_fields}
                
                try:
                    headers = {'Authorization': f'Bearer {token}'} if token else {}
                    success_msg = []
                    
                    # 1. ACTUALIZAR IDENTIDAD (Si hay datos) -> PUT /usuarios/{uid}
                    if identity_payload:
                        print(f"DEBUG: Enviando Identity Update a {USUARIO_API_URL}/{uid}: {identity_payload}", file=sys.stderr)
                        resp_ident = requests.put(
                            f"{USUARIO_API_URL}/{uid}",
                            json=identity_payload,
                            headers=headers,
                            timeout=10
                        )
                        if resp_ident.status_code in (200, 204):
                             user_session.update(identity_payload)
                             success_msg.append("Datos personales")
                        else:
                            print(f"Error Identity Update: {resp_ident.text}", file=sys.stderr)
                            # No lanzamos error fatal si falla esto, pero advertimos?
                            # Para Admin es critico.
                            if user_session.get('rol') != 'user':
                                messages.warning(request, "No se pudo actualizar el nombre. Revisa la API.")

                    # 2. ACTUALIZAR PERFIL DE SALUD (Si hay datos) -> PUT /usuarios/perfil/{uid}
                    if profile_payload:
                        print(f"DEBUG: Enviando Profile Update a {API_BASE_URL}/usuarios/perfil/{uid}: {profile_payload}", file=sys.stderr)
                        resp_prof = requests.put(
                            f"{API_BASE_URL}/usuarios/perfil/{uid}", 
                            json=profile_payload, 
                            headers=headers,
                            timeout=10
                        )
                        if resp_prof.status_code in (200, 204):
                            user_session.update(profile_payload)
                            success_msg.append("Perfil de salud")
                        else:
                             print(f"Error Profile Update: {resp_prof.text}", file=sys.stderr)
                             messages.warning(request, "Error al actualizar métricas de salud.")

                    # Gestión de sesión y Feedback
                    if success_msg:
                        request.session['user_session_data'] = user_session
                        request.session.modified = True
                        messages.success(request, f"Actualizado correctamente: {', '.join(success_msg)}.")
                    elif not identity_payload and not profile_payload:
                         messages.info(request, "No se detectaron cambios para enviar.")
                    else:
                        # Si hubo payloads pero ninguno pasó (mensajes de error arriba)
                        pass 

                except requests.RequestException as e:
                    print(f"Error al enviar datos perfil: {e}", file=sys.stderr)
                    messages.error(request, "Error de conexión al guardar cambios.")
                    # No redirigimos aquí para que el usuario vea el error en el formulario si es necesario
                
                # --- LÓGICA DE CAMBIO DE PASSWORD COMBINADO (PARA TODOS) ---
                curr_pass = request.POST.get('current_password')
                new_pass = request.POST.get('new_password')
                conf_pass = request.POST.get('confirm_password')

                # Solo si intentó cambiar password (escribió algo en nueva contraseña)
                if new_pass:
                        if not curr_pass:
                            messages.warning(request, "Perfil actualizado, pero PASSWORD NO: Faltó la contraseña actual.")
                        elif new_pass != conf_pass:
                            messages.error(request, "Perfil actualizado, pero PASSWORD NO: Las nuevas contraseñas no coinciden.")
                        else:
                            # 1. Verificar contraseña actual (simulando login)
                            try:
                                # La API espera 'identifier' para el login, no 'email' directo
                                login_payload = {'identifier': user_session.get('email'), 'password': curr_pass}
                                # URL AUTH LOGIN (Ajustar según tu routing, asumo /auth/login)
                                API_AUTH_LOGIN = f"{API_BASE_URL}/auth/login"
                                
                                login_resp = requests.post(API_AUTH_LOGIN, json=login_payload, timeout=5)
                                
                                if login_resp.status_code == 200:
                                    # 2. Actualizar password (usando endpoint de update usuario con 'password')
                                    # NOTA: Tu API debe soportar recibir 'password' en el PUT de /usuarios/{uid}
                                    # O el workaround que definimos. Asumimos que PUT / usuarios / {uid} funciona
                                    update_pass_payload = {'password': new_pass}
                                    
                                    # OJO: Se reutiliza target_uid definido arriba o se busca de nuevo
                                    target_uid_pwd = uid # El uid de la sesion
                                    
                                    resp_pwd = requests.put(
                                        f"{USUARIO_API_URL}/{target_uid_pwd}", 
                                        json=update_pass_payload,
                                        headers=headers,
                                        timeout=5
                                    )
                                    
                                    if resp_pwd.status_code == 200:
                                        messages.success(request, "¡Contraseña actualizada correctamente!")
                                    else:
                                        messages.error(request, "Error API al cambiar password.")
                                else:
                                    messages.error(request, "Contraseña actual incorrecta. No se pudo cambiar.")
                                    
                            except Exception as e:
                                print(f"Error password admin update: {e}", file=sys.stderr)
                                messages.error(request, "Error técnico al cambiar contraseña.")

                return redirect('perfiles:ver_perfil')
            else:
                # DEBUG: Imprimir errores de validación si falla
                print(f"Error Validación Form Perfil ({user_session.get('rol')}): {form.errors}", file=sys.stderr)
                messages.error(request, "Por favor corrige los errores del formulario.")
        else:
            form = FormClass(initial=initial_data)

        return render(request, 'perfiles/editar_perfil.html', {'form': form, 'user_session_data': user_session})
    
    except Exception as e:
        print(f"CRITICAL ERROR EDITAR_PERFIL_VIEW: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        messages.error(request, "Ocurrió un error inesperado al cargar la edición de perfil.")
        return redirect('perfiles:ver_perfil')

@login_required
def cambiar_password_view(request):
    try:
        user_session = request.session.get('user_session_data', {})
        token = user_session.get('token')
        uid = user_session.get('uid')
        
        if request.method == 'POST':
            form = CambiarPasswordForm(request.POST)
            if form.is_valid():
                current_password = form.cleaned_data['password_actual']
                new_password = form.cleaned_data['password_nueva']
                
                try:
                    # Endpoint asuimido: /auth/change-password
                    # Debe recibir uid/email, currentPassword, newPassword
                    payload = {
                        'uid': uid, # O 'userId' dependiendo de la API
                        'currentPassword': current_password,
                        'newPassword': new_password
                    }
                    
                    headers = {'Authorization': f'Bearer {token}'} if token else {}
                    
                    resp = requests.post(
                        f"{API_BASE_URL}/auth/change-password",
                        json=payload,
                        headers=headers,
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        messages.success(request, 'Contraseña actualizada. Por favor inicia sesión nuevamente.')
                        # Desloguear para forzar re-login con nueva pass
                        from django.contrib.auth import logout
                        logout(request)
                        return redirect('account:login')
                    elif resp.status_code == 400 or resp.status_code == 401:
                        # Probablemente password actual incorrecta
                        msg = resp.json().get('error', 'Contraseña actual incorrecta o datos inválidos.')
                        messages.error(request, msg)
                    else:
                        messages.error(request, f"Error del servidor ({resp.status_code}). Intenta más tarde.")
                        
                except requests.RequestException as e:
                    messages.error(request, f"No se pudo conectar con el servidor: {e}")
                    
        else:
            form = CambiarPasswordForm()
            
        return render(request, 'perfiles/cambiar_password.html', {'form': form})
        
    except Exception as e:
        print(f"CRITICAL ERROR CAMBIAR_PASSWORD_VIEW: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        messages.error(request, "Ocurrió un error inesperado al cargar cambio de contraseña.")
        return redirect('perfiles:ver_perfil')
