# =========================================================
# CONEXIÓN CON API SIATA DATAVERSE
# =========================================================

import requests
import pandas as pd
import io

BASE_URL = "https://datos.siata.gov.co/api/v1"


# =========================================================
# PRUEBA GENERAL DE CONEXIÓN
# =========================================================

def probar_conexion_siata():

    try:

        respuesta = requests.get(
            f"{BASE_URL}/search",
            params={
                "q": "*",
                "type": "dataset",
                "per_page": 5
            },
            timeout=15
        )

        respuesta.raise_for_status()

        return respuesta.json()

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# BUSCAR ESTACIONES METEOROLÓGICAS
# =========================================================

def buscar_meteorologia():

    try:

        respuesta = requests.get(
            f"{BASE_URL}/search",
            params={
                "q": "Meteorologica",
                "type": "dataset",
                "per_page": 100
            },
            timeout=15
        )

        respuesta.raise_for_status()

        return respuesta.json()

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# OBTENER ARCHIVOS DE UNA ESTACIÓN SIATA
# =========================================================

def obtener_archivos_estacion(doi):
    """
    Obtiene la lista de archivos disponibles
    de una estación meteorológica SIATA.
    """

    try:

        respuesta = requests.get(
            f"{BASE_URL}/datasets/:persistentId",
            params={
                "persistentId": doi
            },
            timeout=15
        )

        respuesta.raise_for_status()

        datos = respuesta.json()

        archivos = []

        for archivo in datos["data"]["latestVersion"]["files"]:

            archivos.append({
                "id": archivo["dataFile"]["id"],
                "nombre": archivo["label"],
                "tamano": archivo["dataFile"]["filesize"]
            })

        return archivos

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# OBTENER EL ÚLTIMO ARCHIVO DE UNA ESTACIÓN
# =========================================================

def obtener_ultimo_archivo(doi):
    """
    Obtiene el ID del archivo más reciente
    de una estación SIATA.
    """

    try:

        archivos = obtener_archivos_estacion(doi)

        if "error" in archivos:
            return archivos

        ultimo = archivos[-1]

        return ultimo["id"]

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# DESCARGAR ARCHIVO DE UNA ESTACIÓN SIATA
# =========================================================

def descargar_archivo(id_archivo):
    """
    Descarga un archivo histórico de una estación SIATA
    usando el ID del archivo.
    """

    try:

        url = (
            f"https://datos.siata.gov.co/api/access/datafile/{id_archivo}"
        )

        respuesta = requests.get(
            url,
            timeout=30
        )

        respuesta.raise_for_status()

        return respuesta.text

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# LEER DATOS METEOROLÓGICOS EN PANDAS
# =========================================================

def leer_datos_estacion(id_archivo):
    """
    Descarga un archivo SIATA y lo convierte
    en un DataFrame de Pandas correctamente.
    """

    try:

        contenido = descargar_archivo(id_archivo)

        columnas = [
            "codigo",
            "fecha",
            "hora",
            "h",
            "t",
            "pr",
            "vv",
            "vv_max",
            "dv",
            "dv_max",
            "p",
            "calidad"
        ]

        df = pd.read_csv(
            io.StringIO(contenido),
            sep=r"\s+",
            skiprows=1,
            names=columnas
        )

        # Unir fecha y hora
        df["fecha_hora"] = pd.to_datetime(
            df["fecha"] + " " + df["hora"]
        )

        # Eliminar columnas temporales
        df.drop(
            columns=[
                "fecha",
                "hora"
            ],
            inplace=True
        )

        return df

    except Exception as e:

        return {
            "error": str(e)
        }
    # =========================================================
# OBTENER LA ÚLTIMA TEMPERATURA DE UNA ESTACIÓN
# =========================================================

def obtener_ultima_temperatura(doi):
    """
    Obtiene la medición más reciente de una estación SIATA.
    """

    try:

        id_archivo = obtener_ultimo_archivo(doi)

        if isinstance(id_archivo, dict):
            return id_archivo

        df = leer_datos_estacion(id_archivo)

        if isinstance(df, dict):
            return df

        ultima = df.iloc[-1]

        return {
            "codigo": int(ultima["codigo"]),
            "fecha_hora": str(ultima["fecha_hora"]),
            "temperatura": float(ultima["t"]),
            "humedad": float(ultima["h"]),
            "presion": float(ultima["pr"])
        }

    except Exception as e:

        return {
            "error": str(e)
        }
      # =========================================================
# OBTENER DATOS SIATA
# =========================================================

def obtener_datos_siata():

    datos = buscar_meteorologia()

    if "error" in datos:
        return datos

    return datos


# =========================================================
# OBTENER TEMPERATURA ACTUAL DE UNA ESTACIÓN
# =========================================================

def obtener_temperatura_estacion(doi):

    try:

        id_archivo = obtener_ultimo_archivo(doi)

        if isinstance(id_archivo, dict):
            return id_archivo

        df = leer_datos_estacion(id_archivo)

        if isinstance(df, dict):
            return df

        ultima = df.iloc[-1]

        return {
            "codigo": int(ultima["codigo"]),
            "fecha_hora": str(ultima["fecha_hora"]),
            "temperatura": float(ultima["t"])
        }

    except Exception as e:

        return {
            "error": str(e)
        }