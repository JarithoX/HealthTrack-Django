from django import forms

class RolUsuarioForm(forms.Form):
    
    ROL_CHOICES = [
        ('user', 'Usuario Estándar'),
        ('profesional', 'Profesional de Salud'),
        ('admin', 'Administrador de Sistema'),
    ]
    
    rol = forms.ChoiceField(
        label='Rol del Usuario',
        choices=ROL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
