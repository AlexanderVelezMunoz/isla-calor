from django.db import models

class Estacion(models.Model):
    nombre = models.CharField(max_length=100)
    latitud = models.FloatField()
    longitud = models.FloatField()

    def __str__(self):
        return self.nombre

class RegistroClimatico(models.Model):
    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE)
    fecha = models.DateField()
    temperatura = models.FloatField()
