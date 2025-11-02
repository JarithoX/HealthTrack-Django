# account/backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.conf import settings
import requests

# Intenta obtener la URL de settings, si no, usa el valor local.
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

class FirestoreAuthBackend(BaseBackend):
    """
    Backend personalizado para validar credenciales contra la API Node.js/Firestore.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            # 🚨 1. Llama al nuevo endpoint POST /usuarios/login en Node.js 🚨
            resp = requests.post(
                f"{API_BASE_URL}/usuarios/login", 
                json={'username': username, 'password': password},
                timeout=5
            )
            
            if resp.status_code == 200:
                # 2. Credenciales válidas: Crea/Obtiene el usuario localmente.
                #    Esto es SOLO para mantener la sesión de Django.
                try:
                    # Usamos get_or_create para que la copia de Django exista.
                    user, created = User.objects.get_or_create(
                        username=username, 
                        defaults={'email': f"{username}@temp.healthtrack.com"} # Usar un email temporal
                    )
                    if created:
                        # Evita que se pueda loguear directamente a la DB local si alguien lo intenta
                        user.set_unusable_password() 
                        user.save()
                    return user # Usuario autenticado y listo para la sesión
                except Exception as e:
                    print(f"Error creando/obteniendo usuario local: {e}")
                    return None 
            
            # 3. Credenciales inválidas (401 de la API de Node.js)
            return None 

        except requests.exceptions.RequestException:
            # Error de conexión (Node.js no está corriendo)
            print("Error de conexión con la API de Node.js al intentar login.")
            return None
        
    def get_user(self, user_id):
        # Necesario para que Django pueda cargar el usuario de la sesión
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None