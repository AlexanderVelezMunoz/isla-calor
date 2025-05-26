from django.urls import path
from . import views

urlpatterns = [
    path('mapa_idw/', views.generar_mapa, name='generar_mapa'),
]
