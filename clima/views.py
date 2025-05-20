import os
import pandas as pd
import folium
import numpy as np
from folium.plugins import HeatMap
from django.shortcuts import render

def mapa(request):
    archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(archivo)

    anos_disponibles = sorted(df['Año'].dropna().unique().tolist())
    ano = request.GET.get('ano')
    if ano:
        ano = int(ano)
        if ano not in anos_disponibles:
            ano = anos_disponibles[0]  # fallback si no está el año
    else:
        ano = anos_disponibles[0]  # año inicial si no hay parámetro

    df = df[df['Año'] == ano]
    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)

    # Construcción del mapa (igual que antes)...
    mapa = folium.Map(location=[6.25, -75.58], zoom_start=11)

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=4,
            color='black',
            fill=True,
            fill_opacity=0.9,
            popup=f"{row['Estacion']}<br>{round(row['Promedio_Temp'], 2)} °C"
        ).add_to(mapa)

    # IDW y HeatMap code aquí (igual)

    return render(request, 'mapa_idw.html', {
        'mapa': mapa._repr_html_(),
        'ano': ano,
        'anos_disponibles': anos_disponibles,
    })
