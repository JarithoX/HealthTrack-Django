import requests
from django.conf import settings

def obtener_datos_perfil(request):
    """
    Obtiene los datos del perfil del usuario desde la API externa.
    Usa el token y username almacenados en la sesión.
    """
    session_data = request.session.get('user_session_data', {})
    token = session_data.get('token')
    username = session_data.get('username')

    if not token or not username:
        return None

    api_url = f"{settings.API_BASE_URL}/usuarios/username/{username}"
    headers = {'Authorization': f'Bearer {token}'}

    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"Error al obtener datos del perfil desde API: {e}")
    
    return None
