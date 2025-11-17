
from django.urls import path
from . import views  

app_name = 'habitos'

urlpatterns = [
    path('crear_habito/', views.crear_habito_view, name='crear_habito'),
    path('registro_habito/', views.registro_habitos_view, name='registro_habito'),
    path('mi_progreso/', views.mi_progreso_view, name='mi_progreso'),
]