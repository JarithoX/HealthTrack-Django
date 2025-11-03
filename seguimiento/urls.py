
from django.urls import path
from . import views  

app_name = 'habitos'

urlpatterns = [
    # URL completa será: /habitos/registrar/
    path('registrar/', views.habitos_registrar, name='habitos_registrar'),
    
    # URL completa será: /habitos/ (para la lista)
    path('historial/', views.habitos_listar, name='habitos_listar'),

    path('crear_habito/', views.crear_habito_view, name='crear_habito'),
    path('registro_habito/', views.registro_habitos_view, name='registro_habito'),
]