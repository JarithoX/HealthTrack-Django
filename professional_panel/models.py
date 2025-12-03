from django.db import models
from django.conf import settings

# Create your models here.
class ProfessionalComment(models.Model):
    professional = models.CharField(max_length=150) # Guardamos el username del profesional (auth stateless)
    patient_username = models.CharField(max_length=150) 
    comment = models.TextField()
    is_from_professional = models.BooleanField(default=True) # True: Profesional -> Paciente, False: Paciente -> Profesional
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario para {self.patient_username} por {self.professional}"
