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