import requests
from django.conf import settings

# URL base de tu API (definida en settings o hardcoded por ahora)
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://localhost:3000/api')

from datetime import datetime

# ... (imports)

def get_messages(patient_username):
    """Obtiene los mensajes consultando la API de Node.js."""
    try:
        url = f"{API_BASE_URL}/chat/{patient_username}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data_list = response.json()
            # Mapear respuesta de la API a lo que espera el template
            messages = []
            for item in data_list:
                # Parsear timestamp si es string
                ts = item.get('timestamp')
                if isinstance(ts, str):
                    try:
                        # Intenta formato ISO básico
                        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except ValueError:
                        pass # Si falla, se deja como string (o se podría usar dateutil)

                msg = {
                    'comment': item.get('contenido', ''),
                    'professional': item.get('remitente_id', ''),
                    'patient_username': patient_username,
                    'is_from_professional': item.get('remitente_tipo') == 'profesional',
                    'created_at': ts, 
                    'timestamp': ts
                }
                messages.append(msg)
            return messages
        else:
            print(f"Error API Chat: {response.status_code}")
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
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Error enviando mensaje a API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error enviando mensaje a API: {e}")
        return False
