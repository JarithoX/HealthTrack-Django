from django.contrib.auth.backends import BaseBackend
from django.conf import settings
import requests
from types import SimpleNamespace

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

class NodeAPIBackend(BaseBackend):
    """
    Backend que actúa como proxy: recibe usuario/pass y los valida contra la API de Node.js.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Permitir 'identifier' o 'username'
        identifier = kwargs.get('identifier', username)

        if not identifier or not password:
            return None
        
        try:
            # POST a la API de Node.js
            resp = requests.post(
                f"{API_BASE_URL}/auth/login", 
                json={'identifier': identifier, 'password': password}, 
                timeout=5
            )
        
            print(f"DEBUG BACKEND: Respuesta de API Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"DEBUG BACKEND: Respuesta de API Data: {data}")
                
                # Asumimos que la API devuelve { success: true, token: '...', user: {...} }
                # O similar. Ajustamos según lo que se espera.
                # Si la API devuelve el usuario dentro de 'user' o 'usuario'
                user_payload = data.get('user') or data.get('usuario') or {}
                token = data.get('token')
                
                if not user_payload and token:
                    # Si solo devuelve token, podríamos necesitar decodificarlo o hacer otra llamada
                    # Pero por ahora asumimos que viene la info básica
                    pass

                # Mapear roles
                rol = user_payload.get('rol', 'user')
                es_admin = (rol == 'admin')
                es_staff = (rol in ['admin', 'profesional'])
                
                # Crear objeto usuario temporal
                user = SimpleNamespace(
                    is_authenticated=True,
                    is_anonymous=False,
                    # IMPORTANTE: is_active depende de si el usuario completó su perfil (campo 'activo' en API)
                    # Si no existe el campo, asumimos False para forzar onboarding.
                    is_active=user_payload.get('activo', False), 
                    is_staff=es_staff,
                    is_superuser=es_admin,
                    # username: Nombre visual (sobrenombre)
                    username=user_payload.get('username') or user_payload.get('nombre') or identifier,
                    email=user_payload.get('email') or identifier,
                    first_name=user_payload.get('nombre', ''),
                    last_name=user_payload.get('apellido', ''),
                    rol=rol,
                    # uid: ID técnico de Firebase
                    uid=user_payload.get('uid'),
                    token=token,
                    backend='account.backend.NodeAPIBackend' # Necesario para que Django sepa quién lo autenticó
                )
                return user
            
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con la API de Node.js: {e}")
            return None
        
    def get_user(self, user_id):
        # En este esquema stateless, no recargamos por ID desde DB.
        return None