from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('perfil/completar/', views.completar_perfil_view, name='completar_perfil'),
    path('mensajes/', views.mensajes_view, name='mensajes'),
]