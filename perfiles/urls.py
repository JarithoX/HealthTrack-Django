from django.urls import path
from . import views

app_name = 'perfiles' 

urlpatterns = [
    path('', views.mi_perfil_view, name='ver_perfil'),
    path('editar/', views.editar_perfil_view, name='editar_perfil'),
    path('password/', views.cambiar_password_view, name='cambiar_password'),
]