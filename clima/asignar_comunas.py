import os
import sys
import django
import geopandas as gpd
from shapely.geometry import Point

# === AGREGAR RUTA DEL PROYECTO ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# === DJANGO SETTINGS ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django.setup()

from clima.models import Estacion

# === GEOJSON ===
geojson_path = os.path.join(
    BASE_DIR,
    "medellin_comunas_corregimientos.geojson"
)

# Leer GeoJSON
gdf = gpd.read_file(geojson_path)

# Mostrar columnas
print(gdf.columns)

# CAMBIAR SI ES NECESARIO
columna_comuna = "NOMBRE"

# === RECORRER ESTACIONES ===
for estacion in Estacion.objects.all():

    punto = Point(
        estacion.longitud,
        estacion.latitud
    )

    comuna_encontrada = None

    for _, row in gdf.iterrows():

        if row.geometry.contains(punto):

            comuna_encontrada = row[columna_comuna]
            break

    if comuna_encontrada:

        estacion.comuna = comuna_encontrada
        estacion.save()

        print(f" {estacion.nombre} → {comuna_encontrada}")

    else:

        print(f" No encontrada: {estacion.nombre}")

print("✅ Proceso terminado")