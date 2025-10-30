from django.shortcuts import render

# Create your views here.
def index(request):
    """Vista para la página de inicio."""
    # La lógica para obtener datos (si es necesario) iría aquí.
    context = {
        'titulo': 'Bienvenido a Health Track',
        'descripcion': 'Sistema de seguimiento de salud y bienestar.'
    }
    # Renderiza la plantilla HTML
    return render(request, 'home/index.html', context)