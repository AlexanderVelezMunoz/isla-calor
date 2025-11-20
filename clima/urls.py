from django.urls import path
from . import views

urlpatterns = [
    path('', views.generar_mapa, name='inicio'),  # 👈 ruta raíz
    path('mapa_idw/', views.generar_mapa, name='generar_mapa'),
]
