from django.urls import path
from . import views

app_name = 'professional_panel'

urlpatterns = [
    # Panel principal del profesional
    path('dashboard/', views.professional_dashboard_view, name='dashboard'),
    path('pacientes/', views.listar_pacientes_view, name='listar_pacientes'),
    path('asignar/<str:uid>/', views.asignar_paciente_view, name='asignar_paciente'), # Nueva ruta
    path('pacientes/<str:username>/', views.detalle_paciente_view, name='detalle_paciente'),
    path('pacientes/<str:username>/recomendar/', views.recomendar_habito_view, name='recomendar_habito'),
]
