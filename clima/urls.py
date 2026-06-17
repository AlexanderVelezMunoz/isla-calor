from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    generar_mapa,
    registro,
    logout_view,
    EstacionViewSet,
    RegistroClimaticoViewSet
)

router = DefaultRouter()
router.register(r'estaciones', EstacionViewSet)
router.register(r'registros', RegistroClimaticoViewSet)

urlpatterns = [
    path('', generar_mapa, name='inicio'),
    path('mapa_idw/', generar_mapa, name='generar_mapa'),
    path('registro/', registro, name='registro'),
    path('logout/', logout_view, name='logout'),

    # API
    path('api/', include(router.urls)),
]