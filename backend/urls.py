from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

def home(request):
    return redirect('login')

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', home),  # raíz redirige al login

    path('login/', auth_views.LoginView.as_view(), name='login'),

    path('', include('clima.urls')),
]