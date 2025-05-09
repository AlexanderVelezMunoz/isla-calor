from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # 👈 Importar redirección

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/mapa/')),  # 👈 Redirige la raíz a /mapa/
    path('', include('clima.urls')),              # 👈 Asegura que las rutas de 'clima' estén conectadas
]
