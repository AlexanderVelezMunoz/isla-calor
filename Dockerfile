FROM python:3.11-slim

# Dependencias del sistema para GDAL y Rasterio
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

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Instalar requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar todo el código
COPY . .

# Crear carpeta de estáticos
RUN mkdir -p /app/staticfiles

# Ejecutar collectstatic
RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 8000

# INICIAR Gunicorn apuntando al proyecto correcto
CMD ["gunicorn", "isla_calor.wsgi:application", "--bind", "0.0.0.0:${PORT}"]
