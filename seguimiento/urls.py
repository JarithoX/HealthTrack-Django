
from django.urls import path
from . import views  

urlpatterns = [
    # URL completa será: /habitos/registrar/
    path('registrar/', views.habitos_registrar, name='habitos_registrar'),
    
    # URL completa será: /habitos/ (para la lista)
    path('', views.habitos_listar, name='habitos_listar'),
]