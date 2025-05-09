from django.urls import path
from . import views
from .views import api_datos_clima

urlpatterns = [
    path('mapa/', views.mapa_calor, name='mapa_calor'),
    path('api/datos/', api_datos_clima, name='api_datos'),
]