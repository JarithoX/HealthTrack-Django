from django import forms

#Propósito: Crear o editar la meta del hábito. 
#Es el formulario que el usuario llena una sola vez 
class HabitoDefinicionForm(forms.Form):
    nombre = forms.CharField(label='¿Qué hábito quieres construir?', max_length=100, 
                             widget=forms.TextInput(attrs={'placeholder': 'Ej: Correr 5K, Leer 10 páginas', 'class': 'form-control form-control-lg'}))
    
    TIPO_MEDICION_CHOICES = [
        ('Numero entero', 'Número Entero'),
        ('Booleano', 'Completado / No Completado'),
        ('Flotante', 'Decimal'),
    ]
    # Ocultamos este campo porque se llenará vía JS
    tipo_medicion = forms.ChoiceField(choices=TIPO_MEDICION_CHOICES, widget=forms.HiddenInput())
    
    # Nuevos campos ocultos/opcionales para la UI
    icono = forms.CharField(widget=forms.HiddenInput(), required=False)
    unidad = forms.CharField(widget=forms.HiddenInput(), required=False)

    meta = forms.CharField(label='Mi Objetivo Diario', max_length=50,
                           widget=forms.TextInput(attrs={'placeholder': 'Ej: 30', 'class': 'form-control form-control-lg'}))
    
    frecuencia = forms.CharField(label='Frecuencia', initial='Diaria', 
                                 widget=forms.TextInput(attrs={'placeholder': 'Ej: Diaria, Lunes y Jueves', 'class': 'form-control'}))
    
#Propósito: El formulario que el usuario llenará 
# todos los días para registrar su progreso.
#(Nota: id_habito_def, fecha y id_usuario se añadirán automáticamente
# en la vista de Django antes de enviarlos a la API).
class HabitoRegistroForm(forms.Form):
    # Este campo será dinámico. En la vista, lo ajustarás según el 'tipo_medicion' del hábito.
    valor_registrado = forms.CharField(label='Valor de Hoy', required=True) 
    
    comentario = forms.CharField(label="Comentario (Opcional)", required=False, 
                                 widget=forms.Textarea(attrs={'rows': 2}))