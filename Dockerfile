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
ENV GDAL_VERSION=3.9.3
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Carpeta principal
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Recolectar archivos estáticos
RUN python backend/manage.py collectstatic --noinput

# Railway usa esta variable automáticamente
ENV PORT=8000

# Exponer puerto
EXPOSE 8000

# Ejecutar Gunicorn con el módulo correcto
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:${PORT}"]
