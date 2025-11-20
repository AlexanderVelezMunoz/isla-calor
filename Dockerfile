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
    libtiff5 \
    libjpeg62-turbo \
    libpng16-16 \
    libsqlite3-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer variable de entorno GDAL
ENV GDAL_VERSION=3.9.3
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Crear carpeta de la app
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python (incluye Rasterio y Contextily)
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer el puerto interno
EXPOSE 8000

# Comando de arranque con Gunicorn
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
