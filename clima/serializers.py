from rest_framework import serializers
from .models import Estacion, RegistroClimatico


class EstacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estacion
        fields = '__all__'


class RegistroClimaticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroClimatico
        fields = '__all__'