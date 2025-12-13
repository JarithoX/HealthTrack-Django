from django import forms
from home.forms import PerfilConfigForm

class EditarPerfilForm(PerfilConfigForm):
    # Agregamos campos personales al formulario base de salud
    nombre = forms.CharField(
        label="Nombre",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellido = forms.CharField(
        label="Apellido",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Email y Username suelen ser delicados de cambiar sin re-confirmación.
    # Los mostramos como deshabilitados por seguridad inicial, o editables si la API lo soporta.
    # Por ahora permitimos editar si el usuario lo pide explícitamente, pero es riesgoso.
    # Lo dejaremos editable pero con cuidado en la vista.
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_order = ['nombre', 'apellido', 'peso', 'altura', 'edad', 'genero', 
                      'hora_despertar', 'hora_dormir', 'objetivos', 'condiciones_medicas']
        self.fields = {k: self.fields[k] for k in field_order if k in self.fields}

class EditarPerfilSimpleForm(forms.Form):
    # Formulario simplificado para Admins y Profesionales (solo datos básicos)
    nombre = forms.CharField(
        label="Nombre",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellido = forms.CharField(
        label="Apellido",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual'
        })
    )
    password_nueva = forms.CharField(
        label="Nueva Contraseña",
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 6 caracteres'
        })
    )
    password_confirmacion = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la nueva contraseña'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password_nueva")
        p2 = cleaned_data.get("password_confirmacion")

        if p1 and p2 and p1 != p2:
            self.add_error('password_confirmacion', "Las contraseñas nuevas no coinciden.")
        
        return cleaned_data
