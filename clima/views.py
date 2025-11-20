import matplotlib
matplotlib.use('Agg')  
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib_scalebar.scalebar import ScaleBar
from scipy.interpolate import griddata
from django.shortcuts import render
from django.conf import settings
from shapely.vectorized import contains
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import contextily as ctx
from matplotlib.patches import Polygon, Patch
from matplotlib.ticker import MaxNLocator

# Fuente más limpia y científica
plt.rcParams['font.family'] = 'DejaVu Sans'

# ... [imports idénticos a los tuyos, sin cambios] ...

def generar_mapa(request):
    # === CARGA DE DATOS ===
    excel_path   = settings.BASE_DIR / "temperaturas_rellenas_promedio.xlsx"
    limite_path  = settings.BASE_DIR / "limite.geojson"
    comunas_path = settings.BASE_DIR / "medellin_comunas_corregimientos.geojson"
    vecinos_path = settings.BASE_DIR / "municipios_vecinos.geojson"

    df = pd.read_excel(excel_path)
    gdf_limite = gpd.read_file(limite_path).to_crs(epsg=4326)
    gdf_comunas = gpd.read_file(comunas_path).to_crs(epsg=4326)
    gdf_vecinos = gpd.read_file(vecinos_path).to_crs(epsg=4326)

    df.columns = df.columns.map(str)
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")

    anios = sorted(df["Año"].dropna().unique())
    meses = [{"numero": i+1, "nombre": n} for i, n in enumerate(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"])]

    anio = request.GET.get("anio")
    mes = request.GET.get("mes")

    if not anio or not mes:
        return render(request, "selector.html", {"anios": anios, "meses": meses})

    anio = int(anio)
    mes = int(mes)
    col = str(mes)

    df_mes = df[df["Año"] == anio][["Estacion", "Longitud", "Latitud", col]].dropna()
    if df_mes.empty:
        return render(request, "selector.html", {
            "anios": anios, "meses": meses,
            "anio_seleccionado": anio,
            "mes_seleccionado": mes,
            "error": f"No hay datos para {mes}/{anio}"
        })

    df_mes.columns = ["Estacion", "Long", "Lat", "Valor"]

    xmin, ymin, xmax, ymax = gdf_limite.total_bounds
    res = 100
    xi, yi = np.meshgrid(np.linspace(xmin, xmax, res), np.linspace(ymin, ymax, res))
    puntos = df_mes[["Long", "Lat"]].values
    valores = df_mes["Valor"].values
    zi = griddata(puntos, valores, (xi, yi), method="linear")
    mask = contains(gdf_limite.unary_union, xi, yi)
    zi_mask = np.where(mask, zi, np.nan)

    # Reproyección
    gdf_vecinos = gdf_vecinos.to_crs(epsg=3857)
    gdf_comunas = gdf_comunas.to_crs(epsg=3857)
    gdf_limite = gdf_limite.to_crs(epsg=3857)
    df_mes_proj = gpd.GeoDataFrame(df_mes, geometry=gpd.points_from_xy(df_mes.Long, df_mes.Lat), crs="EPSG:4326").to_crs(epsg=3857)

    # === FIGURA CON GRIDSPEC ===
    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=(12, 7))
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], wspace=0.05)

    # Mapa principal
    ax = fig.add_subplot(gs[0])
    extent = gdf_limite.total_bounds

    im = ax.imshow(
        zi_mask,
        extent=(extent[0], extent[2], extent[1], extent[3]),
        origin="lower",
        cmap=ListedColormap(["blue", "cyan", "yellow", "orange", "red"]),
        alpha=0.8,
        zorder=1
    )

    geom = gdf_limite.geometry.unary_union
    if geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            patch = Polygon(np.array(poly.exterior.coords), facecolor='none', transform=ax.transData)
            im.set_clip_path(patch)
    else:
        patch = Polygon(np.array(geom.exterior.coords), facecolor='none', transform=ax.transData)
        im.set_clip_path(patch)

    ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik, zorder=0)
    gdf_vecinos.boundary.plot(ax=ax, edgecolor='gray', linestyle='--', linewidth=0.8, zorder=2)
    gdf_comunas.boundary.plot(ax=ax, edgecolor='black', linewidth=0.6, zorder=3)
    df_mes_proj.plot(ax=ax, facecolor='white', edgecolor='black', markersize=60, zorder=4)

    for _, r in df_mes_proj.iterrows():
        ax.text(r.geometry.x, r.geometry.y, r.Estacion, fontsize=6, ha='right', va='bottom', zorder=5,
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.2'))

    ax.set_xticks(np.linspace(extent[0], extent[2], 6))
    ax.set_yticks(np.linspace(extent[1], extent[3], 6))
    ax.tick_params(axis='both', labelsize=7)
    ax.set_xlabel("Longitud", fontsize=8)
    ax.set_ylabel("Latitud", fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.5)

    # Flecha Norte
    ax.annotate('N', xy=(0.95, 0.2), xytext=(0.95, 0.1),
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                xycoords='axes fraction', ha='center')

    # Escala
    scalebar = ScaleBar(1, units="m", location='lower right')
    ax.add_artist(scalebar)

    # Créditos
    fig.text(0.02, 0.02, "Elaborado por: Alexander Vélez Muñoz y Kevin Montoya – Proyecto de investigación - Tecnológico de Antioquia",
             ha='left', fontsize=6, style='italic')

    # === PANEL DERECHO: LEYENDA + COLORBAR + LOGOS ===
    ax_leg = fig.add_subplot(gs[1])
    ax_leg.axis('off')

    legend_elements = [
        Patch(facecolor='white', edgecolor='black', label='Estaciones meteorológicas'),
        Patch(facecolor='none', edgecolor='black', linewidth=0.6, label='Límites de comunas'),
        Patch(facecolor='none', edgecolor='gray', linestyle='--', linewidth=0.8, label='Municipios vecinos')
    ]
    ax_leg.legend(handles=legend_elements, loc='upper left', fontsize=8, frameon=False)

    cbar = fig.colorbar(im, ax=ax_leg, shrink=0.8, orientation='vertical', pad=0.05)
    cbar.set_label("Temperatura promedio mensual (°C)", fontsize=9)
    cbar.ax.tick_params(labelsize=7)
    cbar.locator = MaxNLocator(nbins=6)
    cbar.update_ticks()

    # Logotipos
    logos = [
        'media/static/logos/logo_instituto.png',
        'media/static/logos/logo_universidad.png'
    ]
    ypos = 0.1
    for logo_path in logos:
        try:
            logo_img = plt.imread(logo_path)
            imagebox = OffsetImage(logo_img, zoom=0.15)
            ab = AnnotationBbox(imagebox, (0.5, ypos), frameon=False, xycoords='axes fraction')
            ax_leg.add_artist(ab)
            ypos += 0.18
        except FileNotFoundError:
            print(f"⚠️ Logo no encontrado: {logo_path}")

    # Título del mapa
    meses_name = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    titulo = f"ISLA DE CALOR URBANA SUPERFICIAL\nMedellín – {meses_name[mes-1]} {anio}"
    fig.suptitle(titulo, fontsize=13, weight='bold')

    # Guardar imagen
    output_path = os.path.join(settings.MEDIA_ROOT, "mapa.png")
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

    return render(request, "mapa_idw.html", {
        "mapa_url": settings.MEDIA_URL + "mapa.png",
        "anio": anio,
        "mes": mes
    })
