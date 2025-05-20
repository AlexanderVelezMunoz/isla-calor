from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('mapa_idw/', include('clima.urls')),
    path('', RedirectView.as_view(url='/mapa_idw/', permanent=False)),
]
