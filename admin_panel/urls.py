from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Panel principal
    path('dashboard/', views.admin_dashboard_view, name='dashboard'),    
    # CRUD de Usuarios
    path('usuarios/', views.listar_usuarios_view, name='listar_usuarios'),
    #path('usuarios/editar/<str:username>/', views.editar_usuario_view, name='editar_usuario'),
    #path('usuarios/eliminar/<str:username>/', views.eliminar_usuario_view, name='eliminar_usuario'),
]