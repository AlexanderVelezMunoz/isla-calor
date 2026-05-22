# =========================================================
# INTERPOLACIÓN IDW MEJORADA - NIVEL TESIS
# =========================================================

import matplotlib
matplotlib.use('Agg')

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from scipy.spatial import cKDTree
from shapely.vectorized import contains

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login

from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

import contextily as ctx

from .models import RegistroClimatico, Estacion
from .utils import generar_reporte_pdf, generar_excel

plt.rcParams['font.family'] = 'DejaVu Sans'


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect('login')


# =========================================================
# MAPA PRINCIPAL
# =========================================================

@login_required(login_url='login')
def generar_mapa(request):

    # =========================================================
    # ARCHIVOS
    # =========================================================

    limite_path = os.path.join(
        settings.BASE_DIR,
        "medellin_comunas_corregimientos.geojson"
    )

    vecinos_path = os.path.join(
        settings.BASE_DIR,
        "municipios_vecinos.geojson"
    )

    # =========================================================
    # GEOJSON
    # =========================================================

    gdf_limite = gpd.read_file(limite_path).to_crs(epsg=4326)

    gdf_comunas = gdf_limite.copy()

    gdf_vecinos = gpd.read_file(
        vecinos_path
    ).to_crs(epsg=4326)

    # =========================================================
    # AÑOS
    # =========================================================

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

    # =========================================================
    # COMUNAS
    # =========================================================

    comunas = sorted(
        Estacion.objects.values_list(
            'comuna',
            flat=True
        ).distinct()
    )

    anio = request.GET.get("anio")
    mes = request.GET.get("mes")
    comuna = request.GET.get("comuna")

    # =========================================================
    # SELECTOR
    # =========================================================

    if not anio or not mes:

        return render(request, "selector.html", {
            "anios": anios,
            "meses": meses,
            "comunas": comunas
        })

    anio = int(anio)
    mes = int(mes)

    # =========================================================
    # CONSULTA
    # =========================================================

    registros_mes = RegistroClimatico.objects.filter(
        fecha__year=anio,
        fecha__month=mes
    )

    # =========================================================
    # FILTRO COMUNA
    # =========================================================

    if comuna and comuna != "Todas":

        registros_mes = registros_mes.filter(
            estacion__comuna=comuna
        )

    # =========================================================
    # DATAFRAME
    # =========================================================

    datos = []

    for r in registros_mes:

        datos.append({
            "Estacion": r.estacion.nombre,
            "Long": r.estacion.longitud,
            "Lat": r.estacion.latitud,
            "Valor": r.temperatura
        })

    df_mes = pd.DataFrame(datos)

    # =========================================================
    # VALIDAR
    # =========================================================

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

    # =========================================================
    # VALIDACIÓN DE TEMPERATURAS
    # =========================================================

    df_mes = df_mes[
        (df_mes["Valor"] > 5) &
        (df_mes["Valor"] < 45)
    ]

    # =========================================================
    # ESTADÍSTICAS
    # =========================================================

    temp_max = round(df_mes["Valor"].max(), 1)
    temp_min = round(df_mes["Valor"].min(), 1)
    temp_prom = round(df_mes["Valor"].mean(), 1)

    # =========================================================
    # VALIDAR ESTACIONES
    # =========================================================

    cantidad_estaciones = len(df_mes)

    hacer_interpolacion = cantidad_estaciones >= 5

    # =========================================================
    # CLASIFICACIÓN DE CONFIABILIDAD
    # =========================================================

    if cantidad_estaciones >= 10:

        nivel_confianza = "Alta"

    elif cantidad_estaciones >= 7:

        nivel_confianza = "Moderada"

    else:

        nivel_confianza = "Básica"

    # =========================================================
    # OBSERVACIÓN METODOLÓGICA
    # =========================================================

    if cantidad_estaciones == 5:

        observacion = (
            "La interpolación fue generada con el mínimo "
            "de estaciones requerido metodológicamente (5)."
        )

    elif cantidad_estaciones < 7:

        observacion = (
            "La interpolación presenta una cobertura espacial limitada."
        )

    else:

        observacion = (
            "La interpolación presenta una distribución espacial adecuada."
        )

    # =========================================================
    # REPROYECCIÓN
    # =========================================================

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

    # =========================================================
    # FIGURA
    # =========================================================

    fig = plt.figure(figsize=(16, 9))

    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[4.5, 1],
        wspace=0.02
    )

    ax = fig.add_subplot(gs[0])

    xmin, ymin, xmax, ymax = gdf_limite.total_bounds

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_facecolor('#edf2f7')

    # =========================================================
    # BASEMAP
    # =========================================================

    try:

        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.Positron,
            zoom=11
        )

    except:
        pass

    # =========================================================
    # INTERPOLACIÓN
    # =========================================================

    if hacer_interpolacion:

        res = 600

        xi, yi = np.meshgrid(
            np.linspace(xmin, xmax, res),
            np.linspace(ymin, ymax, res)
        )

        puntos = np.array([
            (geom.x, geom.y)
            for geom in df_mes_proj.geometry
        ])

        valores = df_mes_proj["Valor"].values

        grid_points = np.vstack(
            (xi.flatten(), yi.flatten())
        ).T

        tree = cKDTree(puntos)

        k = min(5, len(puntos))

        distancias, indices = tree.query(
            grid_points,
            k=k
        )

        distancias[distancias == 0] = 0.0001

        p = 2

        pesos = 1 / (distancias ** p)

        zi = np.sum(
            pesos * valores[indices],
            axis=1
        ) / np.sum(
            pesos,
            axis=1
        )

        zi = zi.reshape(xi.shape)

        mask = contains(
            gdf_limite.unary_union,
            xi,
            yi
        )

        zi_mask = np.where(mask, zi, np.nan)

        im = ax.imshow(
            zi_mask,
            extent=(xmin, xmax, ymin, ymax),
            origin="lower",
            interpolation='bicubic',
            cmap='RdYlBu_r',
            alpha=0.82,
            zorder=1
        )

        contornos = ax.contour(
            xi,
            yi,
            zi_mask,
            levels=10,
            colors='black',
            linewidths=0.4,
            alpha=0.18,
            zorder=2
        )

        ax.clabel(
            contornos,
            inline=True,
            fontsize=6,
            fmt="%.1f°C"
        )

    else:

        ax.text(
            0.5,
            0.95,
            "Muestra insuficiente para interpolación IDW",
            transform=ax.transAxes,
            ha='center',
            fontsize=10,
            fontweight='bold',
            color='darkred',
            bbox=dict(
                facecolor='white',
                alpha=0.9,
                edgecolor='darkred'
            )
        )

    # =========================================================
    # MUNICIPIOS VECINOS
    # =========================================================

    gdf_vecinos.boundary.plot(
        ax=ax,
        edgecolor='gray',
        linestyle='--',
        linewidth=0.7,
        alpha=0.6,
        zorder=3
    )

    # =========================================================
    # COMUNAS
    # =========================================================

    gdf_comunas.plot(
        ax=ax,
        facecolor='none',
        edgecolor='black',
        linewidth=0.7,
        alpha=0.75,
        zorder=4
    )

    # =========================================================
    # ESTACIONES
    # =========================================================

    ax.scatter(
        df_mes_proj.geometry.x,
        df_mes_proj.geometry.y,
        c='#b91c1c',
        edgecolor='white',
        linewidth=1.2,
        s=85,
        alpha=0.95,
        zorder=5
    )

    # =========================================================
    # ETIQUETAS
    # =========================================================

    for i, r in enumerate(df_mes_proj.itertuples()):

        nombre_corto = r.Estacion[:8]

        offset_x = 80 if i % 2 == 0 else -80
        offset_y = 80 if i % 3 == 0 else 140

        ax.text(
            r.geometry.x + offset_x,
            r.geometry.y + offset_y,
            f"{nombre_corto}\n{round(r.Valor,1)}°C",
            fontsize=6,
            fontweight='bold',
            color='#111827',
            ha='center',
            va='center',
            bbox=dict(
                facecolor='white',
                alpha=0.78,
                edgecolor='#cbd5e1',
                boxstyle='round,pad=0.25'
            ),
            zorder=6
        )

    # =========================================================
    # GRID
    # =========================================================

    ax.grid(
        True,
        linestyle=':',
        alpha=0.15
    )

    # =========================================================
    # NORTE
    # =========================================================

    ax.annotate(
        'N',
        xy=(0.95, 0.14),
        xytext=(0.95, 0.05),
        arrowprops=dict(
            facecolor='black',
            width=3,
            headwidth=10
        ),
        xycoords='axes fraction',
        ha='center',
        fontsize=12,
        fontweight='bold'
    )

    # =========================================================
    # ESCALA
    # =========================================================

    ax.add_artist(
        ScaleBar(
            1,
            units="m",
            location='lower left',
            box_alpha=0.7
        )
    )

    # =========================================================
    # PANEL DERECHO
    # =========================================================

    ax_leg = fig.add_subplot(gs[1])

    ax_leg.axis('off')

    legend_elements = [

        Patch(
            facecolor='darkred',
            edgecolor='black',
            label='Estaciones meteorológicas'
        ),

        Patch(
            facecolor='none',
            edgecolor='black',
            label='Límites comunales'
        ),

        Patch(
            facecolor='none',
            edgecolor='gray',
            label='Municipios vecinos'
        )
    ]

    ax_leg.legend(
        handles=legend_elements,
        loc='upper left',
        fontsize=9,
        frameon=False
    )

    # =========================================================
    # INFORMACIÓN TÉCNICA
    # =========================================================

    info = f"""
ANÁLISIS TÉRMICO

Temperatura máxima:
{temp_max} °C

Temperatura mínima:
{temp_min} °C

Temperatura promedio:
{temp_prom} °C

Estaciones utilizadas:
{cantidad_estaciones}

Confiabilidad espacial:
{nivel_confianza}

Método:
IDW

Potencia IDW:
{p if hacer_interpolacion else 'N/A'}

Resolución:
{res if hacer_interpolacion else 'N/A'} x {res if hacer_interpolacion else 'N/A'}

Observación:
{observacion}
"""

    ax_leg.text(
        0.02,
        0.65,
        info,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(
            facecolor='white',
            alpha=0.92,
            edgecolor='#cbd5e1',
            boxstyle='round,pad=0.6'
        )
    )

    # =========================================================
    # COLORBAR
    # =========================================================

    if hacer_interpolacion:

        cbar = fig.colorbar(
            im,
            ax=ax_leg,
            shrink=0.52,
            pad=0.02
        )

        cbar.set_label(
            "Temperatura (°C)",
            fontsize=9
        )

        cbar.ax.tick_params(labelsize=8)

        cbar.locator = MaxNLocator(nbins=6)

        cbar.update_ticks()

    # =========================================================
    # LOGO
    # =========================================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "logos",
        "logo_tdea.png"
    )

    if os.path.exists(logo_path):

        try:

            logo_img = plt.imread(logo_path)

            imagebox = OffsetImage(
                logo_img,
                zoom=0.10
            )

            ab = AnnotationBbox(
                imagebox,
                (0.5, 0.08),
                frameon=False,
                xycoords='axes fraction'
            )

            ax_leg.add_artist(ab)

        except:
            pass

    # =========================================================
    # TÍTULO
    # =========================================================

    meses_name = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    titulo = (
        f"Interpolación IDW de Temperatura Superficial Urbana\n"
        f"Medellín - {meses_name[mes-1]} {anio}"
    )

    if comuna and comuna != "Todas":

        titulo += f"\nComuna: {comuna}"

    fig.suptitle(
        titulo,
        fontsize=18,
        weight='bold'
    )

    # =========================================================
    # CRÉDITOS
    # =========================================================

    fig.text(
        0.01,
        0.01,
        "Alexander Vélez Muñoz - Tecnológico de Antioquia",
        fontsize=7,
        style='italic'
    )

    # =========================================================
    # LIMPIAR EJES
    # =========================================================

    ax.set_xticks([])
    ax.set_yticks([])

    # =========================================================
    # AJUSTE FINAL
    # =========================================================

    fig.subplots_adjust(
        left=0.02,
        right=0.97,
        top=0.90,
        bottom=0.03
    )

    # =========================================================
    # GUARDAR
    # =========================================================

    output_path = os.path.join(
        settings.MEDIA_ROOT,
        "mapa.png"
    )

    fig.savefig(
        output_path,
        dpi=180,
        bbox_inches='tight',
        facecolor='white'
    )

    plt.close(fig)

    # =========================================================
    # PDF Y EXCEL
    # =========================================================

    generar_reporte_pdf(
        anio,
        mes,
        comuna,
        output_path
    )

    generar_excel(df_mes)

    return render(request, "mapa_idw.html", {

        "mapa_url":
            settings.MEDIA_URL + "mapa.png",

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


# =========================================================
# REGISTRO
# =========================================================

def registro(request):

    if request.method == 'POST':

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect('generar_mapa')

    else:

        form = UserCreationForm()

    return render(
        request,
        'registration/registro.html',
        {'form': form}
    )