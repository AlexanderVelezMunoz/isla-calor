# Archivo views.py corregido para Railway + Base de datos + IDW + filtro por comuna

import matplotlib
matplotlib.use('Agg')

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from .utils import generar_excel
from matplotlib.colors import ListedColormap
from matplotlib_scalebar.scalebar import ScaleBar
from scipy.spatial import cKDTree
from django.shortcuts import render
from django.conf import settings

from .models import RegistroClimatico, Estacion
from .utils import generar_reporte_pdf
from django.http import FileResponse
from shapely.vectorized import contains
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import contextily as ctx
from matplotlib.patches import Polygon, Patch
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gridspec
plt.rcParams['font.family'] = 'DejaVu Sans'
from django.contrib.auth.decorators import login_required

@login_required
def generar_mapa(request):

    # === CARGA DE ARCHIVOS ===
    limite_path = os.path.join(
        settings.BASE_DIR,
        "medellin_comunas_corregimientos.geojson"
    )

    comunas_path = os.path.join(
        settings.BASE_DIR,
        "medellin_comunas_corregimientos.geojson"
    )

    vecinos_path = os.path.join(
        settings.BASE_DIR,
        "municipios_vecinos.geojson"
    )

    # === GEOJSON ===
    gdf_limite = gpd.read_file(limite_path).to_crs(epsg=4326)
    gdf_comunas = gpd.read_file(comunas_path).to_crs(epsg=4326)
    gdf_vecinos = gpd.read_file(vecinos_path).to_crs(epsg=4326)

    # === AÑOS DESDE BASE DE DATOS ===
    registros = RegistroClimatico.objects.all()

    anios = sorted(
        registros.dates('fecha', 'year')
    )

    anios = [a.year for a in anios]

    meses = [
        {"numero": i + 1, "nombre": n}
        for i, n in enumerate([
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
        ])
    ]

    # === COMUNAS ===
    comunas = sorted(
        Estacion.objects.values_list(
            'comuna',
            flat=True
        ).distinct()
    )

    anio = request.GET.get("anio")
    mes = request.GET.get("mes")
    comuna = request.GET.get("comuna")

    # === MOSTRAR SELECTOR ===
    if not anio or not mes:

        return render(request, "selector.html", {
            "anios": anios,
            "meses": meses,
            "comunas": comunas
        })

    anio = int(anio)
    mes = int(mes)

    # === CONSULTA BASE DE DATOS ===
    registros_mes = RegistroClimatico.objects.filter(
        fecha__year=anio,
        fecha__month=mes
    )

    # === FILTRO POR COMUNA ===
    if comuna and comuna != "Todas":

        registros_mes = registros_mes.filter(
            estacion__comuna=comuna
        )

    # === CONVERTIR A DATAFRAME ===
    datos = []

    for r in registros_mes:

        datos.append({
            "Estacion": r.estacion.nombre,
            "Long": r.estacion.longitud,
            "Lat": r.estacion.latitud,
            "Valor": r.temperatura
        })

    df_mes = pd.DataFrame(datos)

    # === VALIDAR DATOS ===
    if df_mes.empty:

        return render(request, "selector.html", {
            "anios": anios,
            "meses": meses,
            "comunas": comunas,
            "anio_seleccionado": anio,
            "mes_seleccionado": mes,
            "comuna_seleccionada": comuna,
            "error": f"No hay datos para {mes}/{anio}"
        })

    # === INTERPOLACIÓN ===
    xmin, ymin, xmax, ymax = gdf_limite.total_bounds

    res = 100

    xi, yi = np.meshgrid(
        np.linspace(xmin, xmax, res),
        np.linspace(ymin, ymax, res)
    )

    # Coordenadas estaciones
    puntos = df_mes[["Long", "Lat"]].values

    # Temperaturas
    valores = df_mes["Valor"].values

    # Grid para interpolación
    grid_points = np.vstack(
        (xi.flatten(), yi.flatten())
    ).T

    # Árbol espacial
    tree = cKDTree(puntos)

    # Buscar vecinos
    k = min(6, len(puntos))

    # Evitar error si hay pocos puntos
    if k < 2:
        k = 1

    distancias, indices = tree.query(
        grid_points,
        k=k
    )

    # Evitar división por cero
    distancias[distancias == 0] = 0.0001

    # Potencia IDW
    p = 2

    # Pesos
    pesos = 1 / (distancias ** p)

    # === INTERPOLACIÓN IDW ===

    # Si solo hay 1 vecino
    if k == 1:

        zi = valores[indices]

    # Si hay varios vecinos
    else:

        zi = np.sum(
            pesos * valores[indices],
            axis=1
        ) / np.sum(
            pesos,
            axis=1
        )

    # Volver matriz
    zi = zi.reshape(xi.shape)

    # Máscara Medellín
    mask = contains(
        gdf_limite.unary_union,
        xi,
        yi
    )

    zi_mask = np.where(mask, zi, np.nan)

    # === REPROYECCIÓN ===
    gdf_vecinos = gdf_vecinos.to_crs(epsg=3857)
    gdf_comunas = gdf_comunas.to_crs(epsg=3857)
    gdf_limite = gdf_limite.to_crs(epsg=3857)

    df_mes_proj = gpd.GeoDataFrame(
        df_mes,
        geometry=gpd.points_from_xy(
            df_mes.Long,
            df_mes.Lat
        ),
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    # === FIGURA ===
    fig = plt.figure(figsize=(12, 7))

    gs = gridspec.GridSpec(
        1,
        2,
        width_ratios=[3, 1],
        wspace=0.05
    )

    ax = fig.add_subplot(gs[0])

    extent = gdf_limite.total_bounds

    im = ax.imshow(
        zi_mask,
        extent=(extent[0], extent[2], extent[1], extent[3]),
        origin="lower",
        cmap=ListedColormap([
            "blue",
            "cyan",
            "yellow",
            "orange",
            "red"
        ]),
        alpha=0.8,
        zorder=1
    )

    geom = gdf_limite.geometry.unary_union

    if geom.geom_type == "MultiPolygon":

        for poly in geom.geoms:

            patch = Polygon(
                np.array(poly.exterior.coords),
                facecolor='none',
                transform=ax.transData
            )

            im.set_clip_path(patch)

    else:

        patch = Polygon(
            np.array(geom.exterior.coords),
            facecolor='none',
            transform=ax.transData
        )

        im.set_clip_path(patch)

    # === BASEMAP ===
    ctx.add_basemap(
        ax,
        crs="EPSG:3857",
        source=ctx.providers.OpenStreetMap.Mapnik,
        zorder=0
    )

    # === CAPAS ===
    gdf_vecinos.boundary.plot(
        ax=ax,
        edgecolor='gray',
        linestyle='--',
        linewidth=0.8,
        zorder=2
    )

    gdf_comunas.boundary.plot(
        ax=ax,
        edgecolor='black',
        linewidth=0.6,
        zorder=3
    )

    df_mes_proj.plot(
        ax=ax,
        facecolor='white',
        edgecolor='black',
        markersize=60,
        zorder=4
    )

    # === NOMBRES ESTACIONES ===
    for _, r in df_mes_proj.iterrows():

        ax.text(
            r.geometry.x,
            r.geometry.y,
            r.Estacion,
            fontsize=6,
            ha='right',
            va='bottom',
            zorder=5,
            bbox=dict(
                facecolor='white',
                alpha=0.6,
                edgecolor='none',
                boxstyle='round,pad=0.2'
            )
        )

    ax.grid(True, linestyle=':', alpha=0.5)

    # === FLECHA NORTE ===
    ax.annotate(
        'N',
        xy=(0.95, 0.2),
        xytext=(0.95, 0.1),
        arrowprops=dict(
            facecolor='black',
            width=5,
            headwidth=15
        ),
        xycoords='axes fraction',
        ha='center'
    )

    # === ESCALA ===
    ax.add_artist(
        ScaleBar(
            1,
            units="m",
            location='lower right'
        )
    )

    # === CRÉDITOS ===
    fig.text(
        0.02,
        0.02,
        "Elaborado por: Alexander Vélez Muñoz  – Proyecto de investigación - Tecnológico de Antioquia",
        ha='left',
        fontsize=6,
        style='italic'
    )

    # === PANEL DERECHO ===
    ax_leg = fig.add_subplot(gs[1])

    ax_leg.axis('off')

    legend_elements = [
        Patch(
            facecolor='white',
            edgecolor='black',
            label='Estaciones meteorológicas'
        ),

        Patch(
            facecolor='none',
            edgecolor='black',
            linewidth=0.6,
            label='Límites de comunas'
        ),

        Patch(
            facecolor='none',
            edgecolor='gray',
            linestyle='--',
            linewidth=0.8,
            label='Municipios vecinos'
        )
    ]

    ax_leg.legend(
        handles=legend_elements,
        loc='upper left',
        fontsize=8,
        frameon=False
    )

    # === COLORBAR ===
    cbar = fig.colorbar(
        im,
        ax=ax_leg,
        shrink=0.8,
        orientation='vertical',
        pad=0.05
    )

    cbar.set_label(
        "Temperatura promedio mensual (°C)",
        fontsize=9
    )

    cbar.ax.tick_params(labelsize=7)

    cbar.locator = MaxNLocator(nbins=6)

    cbar.update_ticks()

    # === LOGOS ===
    logo_rutas = [

        os.path.join(
            settings.BASE_DIR,
            "media",
            "static",
            "logos",
            "logo_instituto.png"
        ),

        os.path.join(
            settings.BASE_DIR,
            "media",
            "static",
            "logos",
            "logo_universidad.png"
        ),

        os.path.join(
            settings.BASE_DIR,
            "static",
            "logos",
            "logo_instituto.png"
        ),

        os.path.join(
            settings.BASE_DIR,
            "static",
            "logos",
            "logo_universidad.png"
        ),
    ]

    ypos = 0.1

    for logo_path in logo_rutas:

        if os.path.exists(logo_path):

            try:

                logo_img = plt.imread(logo_path)

                imagebox = OffsetImage(
                    logo_img,
                    zoom=0.15
                )

                ab = AnnotationBbox(
                    imagebox,
                    (0.5, ypos),
                    frameon=False,
                    xycoords='axes fraction'
                )

                ax_leg.add_artist(ab)

                ypos += 0.18

            except:
                pass

    # === TÍTULO ===
    meses_name = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    titulo = f"ISLA DE CALOR URBANA SUPERFICIAL\nMedellín – {meses_name[mes-1]} {anio}"

    if comuna and comuna != "Todas":
        titulo += f"\nComuna: {comuna}"

    fig.suptitle(
        titulo,
        fontsize=13,
        weight='bold'
    )

    # === GUARDAR MAPA ===
    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "mapa.png"
    )

    fig.tight_layout(rect=[0, 0.04, 1, 0.95])

    fig.savefig(
        output_path,
        dpi=300
    )

    plt.close(fig)

     # === GENERAR PDF ===
    generar_reporte_pdf(
        anio,
        mes,
        comuna,
        output_path
    )

    # === GENERAR EXCEL ===
    generar_excel(df_mes)

    return render(request, "mapa_idw.html", {

        "mapa_url": settings.MEDIA_URL + "mapa.png",

        "pdf_url":
            settings.MEDIA_URL +
            "reporte_temperatura.pdf",

        "excel_url":
            settings.MEDIA_URL +
            "reporte_temperatura.xlsx",

        "anio": anio,
        "mes": mes,

        "comuna": comuna,

        "comunas": comunas,

        "anios": anios,

        "meses": meses
    })  