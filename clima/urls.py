from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'estaciones', views.EstacionViewSet)
router.register(r'registros', views.RegistroClimaticoViewSet)

urlpatterns = [
    path('', views.generar_mapa, name='inicio'),
    path('mapa_idw/', views.generar_mapa, name='generar_mapa'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('acerca/', views.acerca, name='acerca'),
    path('metodologia/', views.metodologia, name='metodologia'),
    path('fuentes/', views.fuentes, name='fuentes'),
    path('api/', include(router.urls)),
    
]