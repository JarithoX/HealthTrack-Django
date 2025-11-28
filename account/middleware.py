from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from types import SimpleNamespace

class RemoteUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Verificar si hay datos de usuario en la sesión
        # Usamos 'user_session_data' para diferenciarlo de cualquier otra cosa
        user_data = request.session.get('user_session_data')

        if user_data:
            # Reconstruir el objeto usuario (RemoteUser)
            user = SimpleNamespace(**user_data)
            
            # Asegurar atributos mínimos
            user.is_authenticated = True
            user.is_anonymous = False
            
            # Asignar al request
            request.user = user
        else:
            # Si no hay sesión, es un usuario anónimo
            request.user = AnonymousUser()
