import requests
from django.conf import settings

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

"""
⚠️ Precaución Rendimiento:		
La única desventaja es el rendimiento. 
Estás haciendo una llamada a la API externa (requests.get) 
para obtener el rol en cada solicitud HTTP (cada vez que se carga una página).
"""
def get_firebase_user_role(username):
    """Consulta la API para obtener el rol de Firebase de un usuario."""
    try:
        # Usa el endpoint que devuelve un usuario por username (router.get('/username/:username'))
        url = f"{API_BASE_URL}/usuarios/username/{username}" 
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            # Asumiendo que la respuesta es {'rol': 'admin', ...} o similar
            return data.get('rol', 'user').lower() 
        
        # Si no se encuentra (404) o error, por defecto es 'user'
        return 'user' 
        
    except requests.RequestException:
        # En caso de error de conexión, por defecto es 'user'
        return 'user'

def user_navigation_context(request):

    if request.user.is_authenticated:
        username = request.user.username
        
        firebase_rol = get_firebase_user_role(username)

        # 1. Definir la ruta del template de navegación
        if firebase_rol == 'admin':
            nav_template = 'includes/nav_admin.html'
            nav_color_class = 'bg-danger' # 🚨 Color: Rojo

        elif firebase_rol == 'profesional':
            nav_template = 'includes/nav_profesional.html'
            nav_color_class = 'bg-success' # 🚨 Color: Verde

        else: # Default: 'user'
            nav_template = 'includes/nav_user.html'
            nav_color_class = 'bg-primary' # 🚨 Color: Azul
            
        return {
            'FIREBASE_ROL': firebase_rol,
            'NAV_TEMPLATE': nav_template,
            'NAV_CLASS': nav_color_class, 
        }
    return {}