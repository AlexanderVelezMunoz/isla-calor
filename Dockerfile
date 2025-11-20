# Imagen base con Python
FROM python:3.11-slim

# Instalar dependencias del sistema para GDAL, Rasterio y Contextily
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libgeos-dev \
    libexpat1 \
    build-essential \
    libtiff-dev \
    libjpeg62-turbo \
    libpng16-16 \
    libsqlite3-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Variables para GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Carpeta del proyecto
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar código completo
COPY . .

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Puerto
EXPOSE 8000

# Comando de arranque
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
