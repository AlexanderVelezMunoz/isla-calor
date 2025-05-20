import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'g84n^t#m+k#h69%5t_)x@re7rirf@3m3!@5@%67t^b^n!fp9p3'

DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',        # Administración
    'django.contrib.auth',         # Autenticación
    'django.contrib.contenttypes', # Tipos de contenido
    'django.contrib.sessions',     # Gestión de sesiones
    'django.contrib.messages',     # Mensajes
    'django.contrib.staticfiles',  # Archivos estáticos (css, js, imágenes)
    'clima',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración mínima para bases de datos (usa sqlite por defecto)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Config para archivos estáticos
STATIC_URL = '/static/'


ROOT_URLCONF = 'backend.urls'  # <- Asegúrate que este módulo exista

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 👈🏽 ruta absoluta a templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ... otras configuraciones (INSTALLED_APPS, DATABASES, etc.) ...
