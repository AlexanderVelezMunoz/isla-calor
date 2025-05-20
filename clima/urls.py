from django.urls import path
from . import views

urlpatterns = [
    path('', views.mapa_idw, name='mapa_idw'),
]
