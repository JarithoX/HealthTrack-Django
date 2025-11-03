from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.conf import settings
import requests

User = get_user_model()

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

class FirestoreAuthBackend(BaseBackend):
    """
    Backend personalizado para validar credenciales y sincronizar permisos con la API Node.js/Firestore.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            # 🚨 1. Llama al endpoint de login en Node.js (que ahora devuelve rol y activo) 🚨
            resp = requests.post(
                f"{API_BASE_URL}/usuarios/login", 
                json={'username': username, 'password': password},
                timeout=5
            )
            
            if resp.status_code == 200:
                user_data = resp.json()
                # 2. 2. Obtener o crear el usuario local de Django (get_or_create)
                # Usamos el email real si la API lo devuelve, si no, uno temporal.
                user, created = User.objects.get_or_create(
                    username=username, 
                    defaults={'email': user_data.get('email', f"{username}@temp.healthtrack.com")} 
                )

                if created:
                    # Si es nuevo, evitamos el login con contraseña local
                    user.set_unusable_password() 

                # 3. 🚨 SINCRONIZACIÓN DE ROLES (Mapeo de Firebase a Django Flags) 🚨
                firebase_rol = user_data.get('rol', 'user')
                firebase_activo = user_data.get('activo', False)
                
                # Reiniciar flags de staff/superuser
                user.is_staff = False
                user.is_superuser = False
                
                if firebase_rol == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                elif firebase_rol == 'profesional':
                    # Usamos is_staff para el acceso al panel del profesional
                    user.is_staff = True 
                    
                # Sincronizar estado 'activo' (importante para el onboarding)
                user.is_active = firebase_activo
                
                # 4. GUARDAR LOS CAMBIOS EN LA BD LOCAL
                user.save() 
                return user # ¡Autenticación exitosa y sincronizada!
            
            else:
                return None # Credenciales inválidas (401 de la API)

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con la API de Node.js al intentar login: {e}")
            return None
        
    def get_user(self, user_id):
        # Necesario para que Django pueda cargar el usuario de la sesión
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None