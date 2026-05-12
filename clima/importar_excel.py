import os
import sys
from pathlib import Path
import django
import pandas as pd
from datetime import date


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from clima.models import Estacion, RegistroClimatico

# Ruta del Excel
excel_path = "temperaturas_rellenas_promedio.xlsx"

# Leer Excel
df = pd.read_excel(excel_path)

# Convertir columnas
df.columns = df.columns.map(str)

# Recorrer filas
for _, row in df.iterrows():

    nombre = row["Estacion"]
    latitud = row["Latitud"]
    longitud = row["Longitud"]

    estacion, created = Estacion.objects.get_or_create(
        nombre=nombre,
        defaults={
            "latitud": latitud,
            "longitud": longitud,
            "comuna": "Sin comuna"
        }
    )

    anio = int(row["Año"])

    # Meses 1 al 12
    for mes in range(1, 13):

        if str(mes) in row and pd.notna(row[str(mes)]):

            temperatura = float(row[str(mes)])

            fecha = date(anio, mes, 1)

            RegistroClimatico.objects.create(
                estacion=estacion,
                fecha=fecha,
                temperatura=temperatura
            )

print("✅ Datos importados correctamente")