import os
import pandas as pd
import rasterio
import numpy as np
from django.conf import settings
from rasterio.transform import from_origin
from reportlab.lib.pagesizes import letter

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet


# ==========================================
# PDF
# ==========================================

def generar_reporte_pdf(
    anio,
    mes,
    comuna,
    mapa_path
):

    output_pdf = os.path.join(
        settings.MEDIA_ROOT,
        "reporte_temperatura.pdf"
    )

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elementos = []

    # Título
    titulo = Paragraph(
        "<b>Sistema de Isla de Calor Urbana Superficial</b>",
        styles['Title']
    )

    elementos.append(titulo)

    elementos.append(Spacer(1, 20))

    # Información
    texto = Paragraph(
        f"""
        <b>Año:</b> {anio}<br/>
        <b>Mes:</b> {mes}<br/>
        <b>Comuna:</b> {comuna if comuna else 'Todas'}<br/><br/>

        Reporte generado automáticamente mediante
        sistema SIG desarrollado en Django.
        """,
        styles['BodyText']
    )

    elementos.append(texto)

    elementos.append(Spacer(1, 20))

    # Imagen
    if os.path.exists(mapa_path):

        imagen = Image(
            mapa_path,
            width=500,
            height=300
        )

        elementos.append(imagen)

    elementos.append(Spacer(1, 20))

    # Footer
    footer = Paragraph(
        "Proyecto de investigación — Tecnológico de Antioquia",
        styles['Italic']
    )

    elementos.append(footer)

    # Construir PDF
    doc.build(elementos)

    return output_pdf


# ==========================================
# EXCEL
# ==========================================

def generar_excel(df_mes):

    output_excel = os.path.join(
        settings.MEDIA_ROOT,
        "reporte_temperatura.xlsx"
    )

    df_mes.to_excel(
        output_excel,
        index=False
    )

    return output_excel
# ==========================================
# Geotiff
# ==========================================

def generar_geotiff(array, path, xmin, ymax, pixel_size):

    transform = from_origin(
        xmin,
        ymax,
        pixel_size,
        pixel_size
    )

    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype='float32',
        crs='EPSG:3857',
        transform=transform,
        nodata=np.nan,
    ) as dst:

        dst.write(
            array.astype('float32'),
            1
        )

    return path