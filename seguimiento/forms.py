
from django import forms

class HabitoForm(forms.Form):

    calorias = forms.IntegerField(label="Calorías", min_value=0)
    pasos = forms.IntegerField(label="Pasos", min_value=0)
    horas_sueno = forms.FloatField(label="Horas de Sueño", min_value=0, max_value=24)
    litros_agua = forms.FloatField(label="Litros de Agua", min_value=0)
    comentario = forms.CharField(label="Comentario", widget=forms.Textarea, required=False)

    