import os
import pandas as pd
import folium
import numpy as np
from folium.plugins import HeatMap
from django.shortcuts import render
from django.http import JsonResponse

def mapa_idw(request):
    archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(archivo)

    # Obtener años únicos para el dropdown
    anos_disponibles = sorted(df['Año'].dropna().unique())

    ano = request.GET.get('ano')
    if ano and int(ano) in anos_disponibles:
        ano = int(ano)
        df = df[df['Año'] == ano]
    else:
        ano = anos_disponibles[0]  # Por defecto el primero

    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)

    mapa = folium.Map(location=[6.25, -75.58], zoom_start=11)

    # Marcadores estaciones
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=4,
            color='black',
            fill=True,
            fill_opacity=0.9,
            popup=f"{row['Estacion']}<br>{round(row['Promedio_Temp'], 2)} °C"
        ).add_to(mapa)

    # IDW interpolación
    puntos = df[['Latitud', 'Longitud', 'Promedio_Temp']].values
    latitudes = np.linspace(df['Latitud'].min(), df['Latitud'].max(), 50)
    longitudes = np.linspace(df['Longitud'].min(), df['Longitud'].max(), 50)
    grid = np.array([[lat, lon] for lat in latitudes for lon in longitudes])

    def idw(x, y, z, xi, yi, power=2):
        dist = np.sqrt((x - xi)**2 + (y - yi)**2)
        weights = 1 / (dist**power)
        weights[dist == 0] = 0
        return np.sum(weights * z) / np.sum(weights)

    heat_data = []
    for lat, lon in grid:
        temp = idw(puntos[:, 0], puntos[:, 1], puntos[:, 2], lat, lon)
        heat_data.append([lat, lon, temp])

    HeatMap(heat_data, radius=15, blur=10, max_zoom=13).add_to(mapa)

    return render(request, 'mapa_idw.html', {
        'mapa': mapa._repr_html_(),
        'ano': ano,
        'range_anos': anos_disponibles
    })
