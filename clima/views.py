import pandas as pd
import folium
from django.shortcuts import render
import os
from rest_framework.decorators import api_view
from rest_framework.response import Response

def mapa_calor(request):
    ruta_archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(ruta_archivo)

    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)

    mapa = folium.Map(location=[6.25, -75.58], zoom_start=11)

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=row['Promedio_Temp'] / 2,
            popup=f"{round(row['Promedio_Temp'], 2)} °C",
            color="red",
            fill=True,
            fill_opacity=0.6
        ).add_to(mapa)

    mapa.save('templates/mapa.html')
    return render(request, 'mapa.html')

@api_view(['GET'])
def api_datos_clima(request):
    ruta_archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(ruta_archivo)

    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)

    # CAMBIO AQUÍ: usa 'ano' sin tilde
    ano = request.GET.get('ano')
    estacion = request.GET.get('estacion')
    temp_min = request.GET.get('min')
    temp_max = request.GET.get('max')

    if ano:
        df = df[df['AÑO'] == int(ano)]  # Aquí sí se puede dejar 'AÑO' con tilde si la columna lo tiene
    if estacion:
        df = df[df['Estacion'].str.lower() == estacion.lower()]
    if temp_min:
        df = df[df['Promedio_Temp'] >= float(temp_min)]
    if temp_max:
        df = df[df['Promedio_Temp'] <= float(temp_max)]

    return Response(df.to_dict(orient='records'))
