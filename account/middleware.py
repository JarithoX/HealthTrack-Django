from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from types import SimpleNamespace
import sys

def get_user(request):
    # Intentamos leer los datos de la sesión firmada
    if not hasattr(request, '_cached_user'):
        
        user_data = request.session.get('user_session_data')
        
        if user_data:
            try:
                # Reconstruir el usuario "fantasma"
                user = SimpleNamespace(**user_data)
                
                # Asegurar atributos mínimos que Django espera
                user.is_authenticated = True
                user.is_anonymous = False
                if not hasattr(user, 'is_active'):
                    user.is_active = True
                if not hasattr(user, 'is_staff'):
                    user.is_staff = False
                if not hasattr(user, 'is_superuser'):
                    user.is_superuser = False
            
                # Métodos dummy para que el Admin Panel no explote
                user.save = lambda *args, **kwargs: None
                user.delete = lambda *args, **kwargs: None
            
                request._cached_user = user

            except Exception as e:
                print(f"ERROR MIDDLEWARE al reconstruir usuario: {e}", file=sys.stderr)
                request._cached_user = AnonymousUser()

        else:
            print("DEBUG MIDDLEWARE: No se encontró 'user_session_data' en la sesión.", file=sys.stderr)
            request._cached_user = AnonymousUser()
            
    return request._cached_user

class RemoteUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # En lugar de asignar el usuario directamente, usamos SimpleLazyObject.
        # Esto retrasa la ejecución de get_user hasta que alguien realmente pida request.user.
        # Es la clave para que funcione bien con sesiones basadas en cookies.
        request.user = SimpleLazyObject(lambda: get_user(request))