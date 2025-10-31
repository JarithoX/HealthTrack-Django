from django import forms

class PerfilConfigForm(forms.Form):
    peso = forms.FloatField(label="Peso (kg)", min_value=1.0)
    altura = forms.IntegerField(label="Altura (cm)", min_value=1)
    genero = forms.ChoiceField(label="Género", choices=[
        ('', 'Seleccionar...'),
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro')
    ])
    edad = forms.IntegerField(label="Edad", min_value=1, max_value=120)
    condiciones_medicas = forms.CharField(label="Condiciones Médicas", required=False, widget=forms.Textarea)