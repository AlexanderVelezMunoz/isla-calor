from django.db import models

class Estacion(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    latitud = models.FloatField()
    longitud = models.FloatField()
    comuna = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre


class RegistroClimatico(models.Model):
    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE)
    fecha = models.DateField()
    temperatura = models.FloatField()

    def __str__(self):
        return f"{self.estacion.nombre} - {self.fecha}"
    