from django.urls import path
from .views import generar_mapa, registro, logout_view

urlpatterns = [

    path('', generar_mapa, name='inicio'),

    path('mapa_idw/', generar_mapa, name='generar_mapa'),

    path('registro/', registro, name='registro'),

    path('logout/', logout_view, name='logout'),

]