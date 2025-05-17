import pandas as pd
import folium
from django.shortcuts import render
import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
import numpy as np
from django.http import JsonResponse
from .models import Estacion, RegistroClimatico

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
@api_view(['GET'])
def api_resumen_estaciones(request):
    ruta_archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(ruta_archivo)

    # Calcular el promedio anual de temperatura
    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)

    # Para simular el AÑO si no está explícito, puedes asumir un valor fijo o inferirlo desde otro campo si lo tienes
    # Aquí asumimos que todos los datos son de un solo año (por ejemplo 2023), puedes cambiarlo si tienes más años
    np.random.seed(0)
    df['AÑO'] = np.random.choice(range(2013, 2024), size=len(df))  # Asignar años aleatorios

    total_registros = len(df)
    numero_estaciones = df['Estacion'].nunique()
    rango_anios = [int(df['AÑO'].min()), int(df['AÑO'].max())]

    resumen_estaciones = []
    for estacion, grupo in df.groupby('Estacion'):
        cantidad = len(grupo)
        temperatura_prom = grupo['Promedio_Temp'].mean()
        temperatura_max = grupo['Promedio_Temp'].max()
        anio_caluroso = grupo.loc[grupo['Promedio_Temp'].idxmax()]['AÑO']

        resumen_estaciones.append({
            'estacion': estacion,
            'cantidad_datos': cantidad,
            'temperatura_promedio': round(temperatura_prom, 2),
            'temperatura_maxima': round(temperatura_max, 2),
            'anio_mas_caluroso': int(anio_caluroso)
        })

    return Response({
        'total_registros': total_registros,
        'numero_estaciones': numero_estaciones,
        'rango_anios': rango_anios,
        'estaciones': resumen_estaciones
    })
@api_view(['GET'])
def resumen_clima(request):
    ruta_archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(ruta_archivo)

    # Calcular promedio anual por estación
    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)
    df['AÑO'] = df['AÑO'].astype(int)

    total_registros = len(df)
    numero_estaciones = df['Estacion'].nunique()
    rango_anios = [int(df['AÑO'].min()), int(df['AÑO'].max())]

    resumen_estaciones = []
    for estacion, grupo in df.groupby('Estacion'):
        cantidad = len(grupo)
        temp_prom = grupo['Promedio_Temp'].mean()
        temp_max = grupo['Promedio_Temp'].max()
        anio_caluroso = grupo.loc[grupo['Promedio_Temp'].idxmax()]['AÑO']

        resumen_estaciones.append({
            'estacion': estacion,
            'cantidad_datos': cantidad,
            'temperatura_promedio': round(temp_prom, 2),
            'temperatura_maxima': round(temp_max, 2),
            'anio_mas_caluroso': int(anio_caluroso),
        })

    data = {
        'total_registros': total_registros,
        'numero_estaciones': numero_estaciones,
        'rango_anios': rango_anios,
        'estaciones': resumen_estaciones
    }
    return Response(data)
@api_view(['GET'])
def resumen_api(request):
    ruta_archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(ruta_archivo)

    # Asegurarse de tener una columna de promedio
    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)

    # Asegurarse de tener una columna de año
    if 'AÑO' in df.columns:
        df['anio'] = df['AÑO']
    elif 'anio' not in df.columns:
        return Response({'error': 'No se encontró columna de año'}, status=400)

    total_registros = len(df)
    estaciones = df['Estacion'].nunique()
    rango_anios = (int(df['anio'].min()), int(df['anio'].max()))

    resumen_estaciones = []
    for estacion, group in df.groupby('Estacion'):
        cantidad = len(group)
        temp_prom = group['Promedio_Temp'].mean()
        temp_max = group.loc[:, list(range(1, 13))].max().max()
        fila_max = group.loc[group.loc[:, list(range(1, 13))].max(axis=1).idxmax()]
        anio_caluroso = fila_max['anio']

        resumen_estaciones.append({
            'estacion': estacion,
            'cantidad_datos': cantidad,
            'temperatura_promedio': round(temp_prom, 2),
            'temperatura_maxima': round(temp_max, 2),
            'anio_mas_caluroso': int(anio_caluroso),
        })

    data = {
        'total_registros': total_registros,
        'numero_estaciones': estaciones,
        'rango_anios': rango_anios,
        'estaciones': resumen_estaciones,
    }

    return Response(data)
    
    ruta_archivo = os.path.join(os.getcwd(), 'temperaturas_rellenas_promedio.xlsx')
    df = pd.read_excel(ruta_archivo)

    # Asegúrate que estos nombres coincidan con tu Excel
    df['Promedio_Temp'] = df.loc[:, list(range(1, 13))].mean(axis=1)
    df['AÑO'] = df['AÑO'].astype(int)
    df['Estacion'] = df['Estacion'].astype(str)

    total_registros = len(df)
    numero_estaciones = df['Estacion'].nunique()
    rango_anios = (int(df['AÑO'].min()), int(df['AÑO'].max()))

    resumen_estaciones = []
    for estacion, grupo in df.groupby('Estacion'):
        resumen_estaciones.append({
            'estacion': estacion,
            'cantidad_datos': len(grupo),
            'temperatura_promedio': round(grupo['Promedio_Temp'].mean(), 2),
            'temperatura_maxima': grupo['Promedio_Temp'].max(),
            'anio_mas_caluroso': int(grupo.loc[grupo['Promedio_Temp'].idxmax()]['AÑO']),
        })

    return Response({
        'total_registros': total_registros,
        'numero_estaciones': numero_estaciones,
        'rango_anios': rango_anios,
        'estaciones': resumen_estaciones,
    })

def resumen_climatico_view(request):
    resumen = RegistroClimatico.objects.values('estacion__nombre').annotate(
        promedio_temp=Avg('temperatura'),
        max_temp=Max('temperatura'),
        min_temp=Min('temperatura')
    )
    return JsonResponse(list(resumen), safe=False)
import folium
from django.http import HttpResponse
from .models import Estacion

def mapa_estaciones(request):
    # Centra el mapa en Medellín
    m = folium.Map(location=[6.2442, -75.5812], zoom_start=11)

    # Cargar estaciones desde la base de datos
    estaciones = Estacion.objects.all()

    for estacion in estaciones:
        # Agrega marcador con nombre visible como etiqueta permanente
        folium.Marker(
            location=[estacion.latitud, estacion.longitud],
            tooltip=estacion.nombre,
            icon=folium.Icon(color='blue')
        ).add_to(m)

    # Devuelve el HTML del mapa directamente
    return HttpResponse(m._repr_html_())
