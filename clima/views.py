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

def add_logo(ax, img_path, xy, zoom=0.2):
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        oi = OffsetImage(img, zoom=zoom)
        ab = AnnotationBbox(oi, xy, frameon=False, xycoords='axes fraction')
        ax.add_artist(ab)

def generar_mapa(request):
    excel_path   = settings.BASE_DIR / "temperaturas_rellenas_promedio.xlsx"
    limite_path  = settings.BASE_DIR / "limite.geojson"
    comunas_path = settings.BASE_DIR / "medellin_comunas_corregimientos.geojson"
    vecinos_path = settings.BASE_DIR / "municipios_vecinos.geojson"

    print("===> Cargando datos del Excel...")
    df = pd.read_excel(excel_path)
    gdf_limite = gpd.read_file(limite_path).to_crs(epsg=4326)
    gdf_comunas= gpd.read_file(comunas_path).to_crs(epsg=4326)
    gdf_vecinos= gpd.read_file(vecinos_path).to_crs(epsg=4326)

    df.columns = df.columns.map(str)
    df["Año"]  = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")

    anios = sorted(df["Año"].dropna().unique())
    meses = [{"numero": i+1, "nombre": n} for i, n in enumerate(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"])]
    
    anio = request.GET.get("anio")
    mes = request.GET.get("mes")

    if not anio or not mes:
        return render(request, "selector.html", {"anios": anios, "meses": meses})

    anio = int(anio)
    mes = int(mes)
    col = str(mes)

    print("===> Filtrando datos del año y mes...")
    df_mes = df[df["Año"] == anio][["Estacion", "Longitud", "Latitud", col]].dropna()
    print("Datos cargados:", df_mes.shape)
    if df_mes.empty:
        return render(request, "selector.html", {
            "anios": anios, "meses": meses,
            "anio_seleccionado": anio,
            "mes_seleccionado": mes,
            "error": f"No hay datos para {mes}/{anio}"
        })

    df_mes.columns = ["Estacion", "Long", "Lat", "Valor"]

    # Interpolación
    xmin, ymin, xmax, ymax = gdf_limite.total_bounds
    res = 50
    xi, yi = np.meshgrid(np.linspace(xmin, xmax, res), np.linspace(ymin, ymax, res))

    puntos = df_mes[["Long", "Lat"]].values
    valores = df_mes["Valor"].values
    print("===> Ejecutando griddata...")
    zi = griddata(puntos, valores, (xi, yi), method="linear")
    print("Interpolación terminada.")

    mask = contains(gdf_limite.unary_union, xi, yi)
    zi_mask = np.where(mask, zi, np.nan)

    # Proyección
    gdf_vecinos = gdf_vecinos.to_crs(epsg=3857)
    gdf_comunas = gdf_comunas.to_crs(epsg=3857)
    gdf_limite  = gdf_limite.to_crs(epsg=3857)
    df_mes_proj = gpd.GeoDataFrame(df_mes, geometry=gpd.points_from_xy(df_mes.Long, df_mes.Lat), crs="EPSG:4326").to_crs(epsg=3857)

    # Crear figura y eje
    fig, ax = plt.subplots(figsize=(10, 10))
    extent = gdf_limite.total_bounds

    im = ax.imshow(zi_mask, extent=(extent[0], extent[2], extent[1], extent[3]),
                   origin="lower", cmap=ListedColormap(["blue", "cyan", "yellow", "orange", "red"]), alpha=0.7)

    ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik)
    gdf_vecinos.boundary.plot(ax=ax, edgecolor='gray', linestyle='--', linewidth=0.8)
    gdf_comunas.boundary.plot(ax=ax, edgecolor='black', linewidth=0.6)
    df_mes_proj.plot(ax=ax, color='white', edgecolor='black', markersize=70, label="Estaciones", zorder=5)

    for _, r in df_mes_proj.iterrows():
        ax.text(r.geometry.x, r.geometry.y, r.Estacion, fontsize=6, ha='right', va='bottom', zorder=6)

    scalebar = ScaleBar(1, units="m", location='lower right')
    ax.add_artist(scalebar)

    ax.annotate('N', xy=(0.95, 0.2), xytext=(0.95, 0.1),
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                xycoords='axes fraction', ha='center')

    # Logos
    logo1 = os.path.join(settings.MEDIA_ROOT, "logos", "logo_universidad.png")
    logo2 = os.path.join(settings.MEDIA_ROOT, "logos", "logo_instituto.png")
    add_logo(ax, logo1, (0.75, 0.05), zoom=0.2)
    add_logo(ax, logo2, (0.88, 0.05), zoom=0.2)

    cbar = fig.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label("Temperatura (°C)")

    meses_name = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    ax.set_title(f"ISLA DE CALOR URBANA SUPERFICIAL - Medellín - {meses_name[mes-1]} {anio}", fontsize=14, weight='bold')
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.legend(loc='upper left')

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    filename = f"mapa_idw_{anio}_{mes}.png"
    output_path = os.path.join(settings.MEDIA_ROOT, filename)
    print("Guardando en:", output_path)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return render(request, "selector.html", {
        "anios": anios,
        "meses": meses,
        "anio_seleccionado": anio,
        "mes_seleccionado": mes,
        "imagen_url": settings.MEDIA_URL + filename
    })
