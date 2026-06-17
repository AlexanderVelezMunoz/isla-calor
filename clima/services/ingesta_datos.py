import pandas as pd
from datetime import datetime

from clima.models import Estacion, RegistroClimatico


# =========================================================
# CARGA DESDE EXCEL (HÍBRIDO LIMPIO)
# =========================================================
def cargar_excel(ruta_excel):

    df = pd.read_excel(ruta_excel)

    for _, row in df.iterrows():

        codigo = str(row["Estacion"]).strip()

        estacion, _ = Estacion.objects.get_or_create(
            codigo=codigo,
            defaults={
                "nombre": f"Estación {codigo}",
                "latitud": row.get("Latitud"),
                "longitud": row.get("Longitud"),
                "comuna": row.get("Ciudad", "")
            }
        )

        for mes in range(1, 13):

            temp = row.get(mes)   # 🔥 AQUÍ ESTABA EL ERROR

            if pd.isna(temp):
                continue

            fecha = datetime(int(row["Año"]), mes, 1)

            RegistroClimatico.objects.get_or_create(
                estacion=estacion,
                fecha=fecha,
                defaults={
                    "temperatura": temp
                }
            )