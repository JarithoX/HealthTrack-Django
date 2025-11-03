
from django import forms

class HabitoForm(forms.Form):

    calorias = forms.IntegerField(label="Calorías", min_value=0)
    pasos = forms.IntegerField(label="Pasos", min_value=0)
    horas_sueno = forms.FloatField(label="Horas de Sueño", min_value=0, max_value=24)
    litros_agua = forms.FloatField(label="Litros de Agua", min_value=0)
    comentario = forms.CharField(label="Comentario", widget=forms.Textarea, required=False)
   
#Propósito: Crear o editar la meta del hábito. 
#Es el formulario que el usuario llena una sola vez 
#al crear un nuevo hábito (ej. "Quiero correr 5 km diarios").
class HabitoDefinicionForm(forms.Form):
    nombre = forms.CharField(label='Nombre del Hábito', max_length=100, 
                             widget=forms.TextInput(attrs={'placeholder': 'Ej: Correr 5K, Leer 10 páginas'}))
    
    TIPO_MEDICION_CHOICES = [
        ('Numero entero', 'Número Entero (Ej: Pasos, Minutos, Páginas)'),
        ('Binario', 'Completado / No Completado (Ej: Meditar, Tomar medicina)'),
        ('Flotante', 'Decimal (Ej: Litros de agua, Horas de sueño)'),
    ]
    tipo_medicion = forms.ChoiceField(label='Tipo de Medición', choices=TIPO_MEDICION_CHOICES, 
                                      widget=forms.Select(attrs={'class': 'form-select'}))
    
    meta = forms.CharField(label='Meta o Valor Objetivo', max_length=50,
                           widget=forms.TextInput(attrs={'placeholder': 'Ej: 5000, 1 (si es Binario), 1.5'}))
    
    frecuencia = forms.CharField(label='Frecuencia', initial='Diaria', 
                                 widget=forms.TextInput(attrs={'placeholder': 'Ej: Diaria, Lunes y Jueves'}))
    
#Propósito: El formulario que el usuario llenará 
# todos los días para registrar su progreso.
#(Nota: id_habito_def, fecha y id_usuario se añadirán automáticamente
# en la vista de Django antes de enviarlos a la API).
 
class HabitoRegistroForm(forms.Form):
    # Este campo será dinámico. En la vista, lo ajustarás según el 'tipo_medicion' del hábito.
    valor_registrado = forms.CharField(label='Valor de Hoy', required=True) 
    
    comentario = forms.CharField(label="Comentario (Opcional)", required=False, 
                                 widget=forms.Textarea(attrs={'rows': 2}))