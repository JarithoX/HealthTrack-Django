from django import forms

#Opciones para genero
GENERO_CHOICES = (
    ('', 'Seleccionar...'),
    ('masculino', 'Masculino'),
    ('femenino', 'Femenino'),
    ('otro', 'Otro'),
)

class PerfilConfigForm(forms.Form):
    peso = forms.FloatField(label="Peso (kg)", min_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 75.5',
            'step': '0.1'
        })
    )
    altura = forms.IntegerField(label="Altura (cm)", min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control','placeholder': 'Ej: 175'})
    )
    genero = forms.ChoiceField(label="Género", choices=GENERO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    edad = forms.IntegerField(label="Edad", min_value=1, max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 30'})
    )
    condiciones_medicas = forms.CharField(label="Condiciones Médicas", required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Opcional: alergias, tratamientos, etc.'
        })
    )

    # Valida que el usuario no deje "Seleccionar..." en blanco
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.error_messages['required'] = 'Este campo es obligatorio.'
        # mensaje específico para el select
        self.fields['genero'].error_messages['required'] = 'Selecciona una opción.'