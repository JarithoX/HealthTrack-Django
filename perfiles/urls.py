from django.urls import path
from . import views

app_name = 'perfiles' 

urlpatterns = [
    path('', views.mi_perfil_view, name='ver_perfil'),
]