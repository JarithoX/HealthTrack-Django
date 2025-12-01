from django import forms

class RolUsuarioForm(forms.Form):
    
    ROL_CHOICES = [
        ('user', 'Usuario'),
        ('profesional', 'Profesional de Salud'),
        ('admin', 'Administrador'),
    ]
    
    rol = forms.ChoiceField(
        label='Rol del Usuario',
        choices=ROL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
