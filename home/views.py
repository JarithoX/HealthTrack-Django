from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def index(request):
    """Vista para la página de inicio."""
    # La lógica para obtener datos (si es necesario) iría aquí.
    context = {
        'titulo': 'Bienvenido a Health Track',
        'descripcion': 'Sistema de seguimiento de salud y bienestar.'
    }
    # Renderiza la plantilla HTML
    return render(request, 'home/index.html', context)