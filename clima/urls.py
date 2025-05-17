from django.urls import path
from . import views
from .views import api_datos_clima, mapa_calor, resumen_clima, resumen_api

urlpatterns = [
    path('mapa/', views.mapa_calor, name='mapa_calor'),
    path('api/datos/', api_datos_clima, name='api_datos'),
    path('api/resumen/', views.api_resumen_estaciones, name='api_resumen'),
    path('api/resumen/', resumen_api, name='resumen_api'),
    path('resumen/', views.resumen_climatico_view, name='resumen_climatico'),
    path('mapa/', views.mapa_estaciones, name='mapa_estaciones'),

]