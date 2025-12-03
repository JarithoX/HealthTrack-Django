import requests
from django.conf import settings

# URL base de tu API (definida en settings o hardcoded por ahora)
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

def get_messages(patient_username):
    """Obtiene los mensajes consultando la API de Node.js."""
    try:
        url = f"{API_BASE_URL}/chat/{patient_username}"
        print(f"DEBUG: GET Request URL: {url}") # Debug print
        response = requests.get(url, timeout=5)
        print(f"DEBUG: GET Response Code: {response.status_code}") # Debug print
        
        if response.status_code == 200:
            data_list = response.json()
            # Mapear respuesta de la API a lo que espera el template
            messages = []
            for item in data_list:
                msg = {
                    'comment': item.get('contenido', ''),
                    'professional': item.get('remitente_id', ''),
                    'patient_username': patient_username,
                    'is_from_professional': item.get('remitente_tipo') == 'profesional',
                    'created_at': item.get('timestamp'), # La API debe devolver string ISO o similar
                    'timestamp': item.get('timestamp')
                }
                messages.append(msg)
            return messages
        else:
            print(f"Error API Chat: {response.status_code}")
            print(f"DEBUG: Response Content: {response.text}") # Debug print
            return []
            
    except Exception as e:
        print(f"Error conectando con API de Chat: {e}")
        return []

def send_message(professional_username, patient_username, content, is_from_professional):
    """Envía un mensaje a través de la API de Node.js."""
    try:
        url = f"{API_BASE_URL}/chat/{patient_username}"
        
        payload = {
            'contenido': content,
            'remitente_id': professional_username if is_from_professional else patient_username,
            'remitente_tipo': 'profesional' if is_from_professional else 'paciente'
        }
        
        print(f"DEBUG: POST Request URL: {url}") # Debug print
        print(f"DEBUG: POST Payload: {payload}") # Debug print
        
        response = requests.post(url, json=payload, timeout=5)
        
        print(f"DEBUG: POST Response Code: {response.status_code}") # Debug print
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Error enviando mensaje a API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error enviando mensaje a API: {e}")
        return False
