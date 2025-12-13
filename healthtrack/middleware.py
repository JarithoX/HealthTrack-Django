from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class ProfileCompletionMiddleware:
    """
    Bloquea el acceso a todas las páginas excepto a la de perfil hasta
    que el usuario tenga el campo 'is_active' en True.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URL a la que se redirige forzadamente (la vista de completar perfil)
        self.completion_url = reverse('home:completar_perfil')
        
        # URLs de 'Lista Blanca': Páginas que SÍ puede ver (Login, Logout, Registro, Static, la misma de completar perfil)
        self.allowed_urls = [
            reverse('account:login'),
            reverse('account:register'),
            reverse('account:logout'),
            self.completion_url,
        ]

    def __call__(self, request):
        
        # Si el usuario no está autenticado, no hacemos nada (ya lo maneja @login_required)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Obtener la ruta actual
        current_path = request.path_info
        
        # Verificación CRÍTICA: Si el usuario está logeado Y su perfil NO está activo (incompleto)
        if not request.user.is_active:
            
            # Si está intentando acceder a una URL NO permitida (ej: /index, /mi_progreso)
            # y no es una ruta estática (CSS/JS)
            if (current_path not in self.allowed_urls and 
                not current_path.startswith(settings.STATIC_URL)):
                
                # FORZAR REDIRECCIÓN a la página de completar perfil
                return redirect(self.completion_url)

        # Si el perfil está completo (is_active=True), la petición sigue su curso normal
        response = self.get_response(request)
        return response