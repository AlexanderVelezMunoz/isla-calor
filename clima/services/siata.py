import requests
from clima.models import Estacion, RegistroClimatico


def obtener_datos_siata():
    url = "https://datos.siata.gov.co/api/v1/search"

    params = {
        "q": "*",
        "subtree": "Pluviometrica",
        "type": "dataset",
        "per_page": 1
    }

    r = requests.get(url, params=params)
    data = r.json()

    return data


def guardar_datos_siata(df):
    for _, item in df.iterrows():

        codigo = item.get("codigo")
        fecha = item.get("fecha_hora")
        p1 = item.get("p1")
        p2 = item.get("p2")
        calidad = item.get("calidad")

        if not codigo or fecha is None:
            continue

        try:
            estacion = Estacion.objects.get(codigo=codigo)
        except Estacion.DoesNotExist:
            continue

        RegistroClimatico.objects.create(
            estacion=estacion,
            fecha=fecha,
            precipitacion=p1,   # aquí decides tu lógica
            calidad=calidad
        )

        # =========================================================
# TEMPERATURA SIATA CON CACHE
# =========================================================

from django.core.cache import cache
from clima.siata_api import obtener_ultima_temperatura


def obtener_temperatura_cache(doi):

    if not doi:
        return None

    clave = f"temperatura_siata_{doi}"

    temperatura = cache.get(clave)

    if temperatura is not None:
        return temperatura

    try:

        respuesta = obtener_ultima_temperatura(doi)

        if isinstance(respuesta, dict):

            temperatura = respuesta.get("temperatura")

            cache.set(
                clave,
                temperatura,
                timeout=300
            )

            return temperatura

    except Exception:

        return None

    return None