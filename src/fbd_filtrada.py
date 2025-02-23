
#%%
import pandas as pd
import numpy as np

#%%

ruta_bd = '../data/variables/statics/'

# Cargar el inventario de deslizamientos
df_deslizamientos = pd.read_csv(f"{ruta_bd}bd_dagrd_lluvia.csv")


#%%
#filtrar donde las columnas 'cp1', 'cp3', 'cp5', 'cp7', 'cp10' los valores sean mayores a 15
df_deslizamientos_filtrada = df_deslizamientos[(df_deslizamientos['cp1'] > 5) & 
                                                (df_deslizamientos['cp3'] >= 10) & 
                                                (df_deslizamientos['cp5'] >= 10) & 
                                                (df_deslizamientos['cp7'] >= 10) & 
                                                (df_deslizamientos['cp10'] >= 15)]
#df_deslizamientos_filtrada = df_deslizamientos[df_deslizamientos['cp10'] > 15]

# %%
#luego filtrar donde 'slope_mean' sea mayor a 10
df_deslizamientos_filtrada = df_deslizamientos_filtrada[df_deslizamientos_filtrada['slope_mean'] >= 10]
df_deslizamientos_filtrada
# %%
#guardar el archivo filtrado
ruta_guardar = '../data/db_landslides/'
df_deslizamientos_filtrada.to_csv(f"{ruta_bd}bd_dagrd_lluvia_filtrada.csv", index=False)
# %%
#==============================================================================
# VAMOS A ESCOGER FECHAS Y LUGARES PARA LOS NO DESLIZAMIENTOS
#==============================================================================
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

#%%
#==============================================================================
#1. Lectura del inventario de deslizamientos
#==============================================================================
# Cargar el inventario de deslizamientos
ruta_guardar = '../data/db_landslides/'
df_landslides = pd.read_csv(f"{ruta_guardar}bd_dagrd_lluvia_filtrada.csv")

#%%
# Convertir lat/lon a objetos geométricos Point
geometry = [Point(xy) for xy in zip(df_landslides['longitud'], df_landslides['latitud'])]

# Crear un GeoDataFrame con sistema de referencia conocido (EPSG:3116, por ejemplo)
gdf_landslides = gpd.GeoDataFrame(
    df_landslides,
    geometry=gpd.points_from_xy(df_landslides['longitud'], df_landslides['latitud']),
    crs="EPSG:4326"  # <<--- clave: decir que está en lat/lon
)
#%%

gdf_landslides = gdf_landslides.to_crs("EPSG:3116")

# %%
num_deslizamientos = len(gdf_landslides)
print("Número total de deslizamientos:", num_deslizamientos)

# %%
#==============================================================================
#2. Lectura de la zona de estudio (raster .tif)
#==============================================================================
import rasterio

ruta_esa = '../data/variables/statics/zonas_ESA.tif'

#%%
with rasterio.open(ruta_esa) as src:
    transform = src.transform
    crs = src.crs
    # Leer banda 1
    zona_data = src.read(1)
    # Crear máscara booleana (True donde hay datos)
    mask = zona_data != src.nodata
    # Bounding box
    bounds = src.bounds


#%%
#==============================================================================
#3. Función para generar puntos aleatorios dentro del raster y filtrar por zona válida
#==============================================================================
# Podemos hacer una función auxiliar que:

# Genere puntos aleatorios dentro de los límites del raster.
# Convierta esos puntos a índices de fila/columna en la matriz.
# Verifique en la máscara si es un píxel válido o no.
# Convierta a coordenadas reales (x, y en CRS EPSG:3116) para quedarnos 
# solo con puntos en la zona.

import numpy as np

def generar_puntos_aleatorios_en_raster(src, mask, num_puntos):
    """
    Genera num_puntos aleatorios dentro de los bounds del raster src
    y retorna solamente aquellos que caen en píxeles válidos de la máscara.
    """
    # Obtenemos las dimensiones del raster
    rows, cols = mask.shape
    
    # Bounding box
    left, bottom, right, top = src.bounds
    # Transform
    transform = src.transform

    puntos_generados = []
    contador = 0
    
    while len(puntos_generados) < num_puntos:
        # Generar fila y columna aleatoria
        rand_row = np.random.randint(0, rows)
        rand_col = np.random.randint(0, cols)
        
        # Verificar si es un píxel válido
        if mask[rand_row, rand_col]:
            # Convertir (row, col) a coordenadas (x, y)
            # La ecuación general es: 
            # x = left + (col + 0.5)*res_x
            # y = top + (row + 0.5)*res_y
            # (Cuidar el signo de la resolución en Y)
            
            x, y = rasterio.transform.xy(transform, rand_row, rand_col)
            puntos_generados.append((x, y))
        
        contador += 1
        if contador > num_puntos*100:
            # Evitar loop infinito, en caso de máscara muy pequeña
            break
    
    return puntos_generados

#%%
#==============================================================================
#4. Filtrar puntos por distancia a deslizamientos (>= 100 m)
#==============================================================================
# Para verificar la distancia con geopandas, podemos:

# Convertir la lista de puntos generados en un GeoDataFrame.
# Hacer un buffer o usar la función gdf.distance(otra_geometría) con un 
# spatial index para optimizar.

def filtrar_por_distancia_minima(gdf_puntos, gdf_deslizamientos, distancia_min=100):
    """
    Devuelve un subconjunto de gdf_puntos que están a >= distancia_min (metros) de cualquier
    deslizamiento en gdf_deslizamientos.
    """
    # Construimos un sindex para los deslizamientos
    sindex = gdf_deslizamientos.sindex
    
    puntos_validos = []
    
    for idx, row in gdf_puntos.iterrows():
        # Buscamos deslizamientos cercanos en el bounding box de 100 m
        posible_matches = list(sindex.intersection(row.geometry.buffer(distancia_min).bounds))
        # posible_matches es una lista de índices de gdf_deslizamientos
        
        # Revisamos la distancia real
        geometria_punto = row.geometry
        es_valido = True
        for i_desliz in posible_matches:
            dist = geometria_punto.distance(gdf_deslizamientos.loc[i_desliz, 'geometry'])
            if dist < distancia_min:
                es_valido = False
                break
        
        if es_valido:
            puntos_validos.append(idx)
    
    return gdf_puntos.loc[puntos_validos].copy()

#%%
#==============================================================================
#5. Asignación de fechas aleatorias con restricción de 90 días
#==============================================================================
# Queremos que las fechas de los no–deslizamientos:

# Estén entre 2016 y 2024.
# Tengan al menos 90 días de diferencia de cualquier fecha de deslizamiento, 
# cuando la ubicación sea diferente (y se aplique la restricción).
# Podemos crear una función para generar una fecha aleatoria en un rango y 
# luego verificar la diferencia con todas las fechas de deslizamiento. 
# De nuevo, podemos optimizar, pero vamos paso a paso.

import datetime
import random

#%%
def generar_fecha_aleatoria(inicio, fin):
    """
    Genera una fecha aleatoria (datetime.date) entre las fechas inicio y fin.
    """
    # Convertir a ordinal
    start_ordinal = inicio.toordinal()
    end_ordinal = fin.toordinal()
    random_ordinal = random.randint(start_ordinal, end_ordinal)
    return datetime.date.fromordinal(random_ordinal)

def asignar_fechas_aleatorias(gdf_puntos, fechas_deslizamientos, dias_min=90, 
                              start_year=2016, end_year=2024):
    """
    Asigna fechas aleatorias a cada punto en gdf_puntos, garantizando
    una separación mínima de dias_min con las fechas en fechas_deslizamientos.
    """
    # Crear rango de fechas
    fecha_inicio = datetime.date(start_year, 1, 1)
    fecha_fin = datetime.date(end_year, 12, 31)
    
    fechas_resultantes = []
    
    for i in range(len(gdf_puntos)):
        while True:
            fecha_random = generar_fecha_aleatoria(fecha_inicio, fecha_fin)
            
            # Comprobar distancia en días con todas las fechas de deslizamientos
            es_valida = True
            for fd in fechas_deslizamientos:
                diff = abs((fecha_random - fd).days)
                if diff < dias_min:
                    es_valida = False
                    break
            
            if es_valida:
                fechas_resultantes.append(fecha_random)
                break
    
    gdf_puntos['fecha_no'] = fechas_resultantes
    return gdf_puntos

#%%
#==============================================================================
#6. Creación de los 3 paquetes
#==============================================================================
#Recordemos:

# Paquete A (misma ubicación, distinta fecha):

# Elegimos la misma geometría de cada deslizamiento.
# Asignamos una fecha aleatoria que cumpla la regla de estar a ≥90 días 
# de la fecha del evento original.
# Generamos 3 veces más muestras que deslizamientos 
# (así que repetiremos el proceso hasta llegar a 3× num_deslizamientos).
# Paquete B (misma fecha, distinta ubicación):

# Elegimos puntos aleatorios en la zona, filtramos a >=100 m 
# de cualquier deslizamiento.
# Asignamos la misma fecha que un deslizamiento real (por ejemplo,
#  elegimos aleatoriamente de la lista de fechas de deslizamiento).
# Hasta llegar a 3× num_deslizamientos.
# Paquete C (distinta fecha y distinta ubicación):

# Puntos aleatorios en la zona, >=100 m de cualquier deslizamiento.
# Fechas aleatorias en [2016, 2024], con separación de >=90 días de cualquier deslizamiento.
# 3× num_deslizamientos.
# Veamos cada uno en detalle.

#%%
#==============================================================================
#6.1. Paquete A: misma ubicación, distinta fecha 
# Asumamos que cada evento corresponde a un único registro. Para obtener 3× la cantidad total, podemos simplemente replicar cada ubicación 3 veces y asignar una fecha distinta.
#==============================================================================

import math

paquete_A = gdf_landslides[['geometry', 'fecha_ho_1']].copy()
print(gdf_landslides.crs)
print(gdf_landslides.total_bounds)
# "fecha_ho_1" = fecha y hora del deslizamiento original

# Replicar 3 veces cada fila
paquete_A = pd.concat([paquete_A]*3, ignore_index=True)
paquete_A = gpd.GeoDataFrame(paquete_A, geometry='geometry', crs=gdf_landslides.crs)

# Convertir "fecha_ho_1" a datetime.date si no lo está
paquete_A['fecha_ho_1'] = pd.to_datetime(paquete_A['fecha_ho_1']).dt.date

#%%
# Ahora asignamos una fecha nueva "fecha_no"
# La regla es: al menos 90 días de diferencia con la fecha original del mismo punto.
# Asumimos la misma regla (rango 2016-2024). Adaptar si tus datos reales difieren.

def asignar_fechas_paquete_A(row, dias_min=90):
    original_date = row['fecha_ho_1']
    # Genera fecha hasta encontrar una que difiera >= 90 días
    fecha_inicio = datetime.date(2016, 1, 1)
    fecha_fin = datetime.date(2024, 12, 31)
    while True:
        fecha_random = generar_fecha_aleatoria(fecha_inicio, fecha_fin)
        if abs((fecha_random - original_date).days) >= dias_min:
            return fecha_random

paquete_A['fecha_no'] = paquete_A.apply(asignar_fechas_paquete_A, axis=1)

# Listo. Paquete A tiene la misma ubicación que el deslizamiento y una fecha distinta
# Observa que aquí NO aplicamos la distancia espacial de 100m porque es la MISMA ubicación.

#%%
#==============================================================================
#6.2. Paquete B: misma fecha, distinta ubicación
#Seleccionamos puntos aleatorios en la zona.
# Filtramos por distancia >= 100m a los deslizamientos.
# Asignamos “fecha_no” = fecha de algún deslizamiento real,
#  escogida aleatoriamente. (Podemos simplemente “emparejar” al azar con una fecha de la lista de deslizamientos.)
#==============================================================================

with rasterio.open(ruta_esa) as src:
    puntos_candidatos = generar_puntos_aleatorios_en_raster(src, mask, num_puntos=3*num_deslizamientos*5)
    # Generamos más candidatos de los que necesitamos porque luego filtramos

gdf_candidatos = gpd.GeoDataFrame(geometry=[Point(p) for p in puntos_candidatos], crs="EPSG:3116")

# Filtrar por distancia >= 100 m
gdf_candidatos_filtrado = filtrar_por_distancia_minima(gdf_candidatos, gdf_landslides, distancia_min=100)

# Necesitamos 3 x num_deslizamientos puntos finales
gdf_candidatos_filtrado = gdf_candidatos_filtrado.sample(n=3*num_deslizamientos, random_state=42)

# Asignar la misma fecha que un deslizamiento
fechas_desliz = pd.to_datetime(gdf_landslides['fecha_ho_1']).dt.date.unique()
fechas_desliz = list(fechas_desliz)  # para poder hacer random.choice

import random

def asignar_fecha_desliz(row):
    return random.choice(fechas_desliz)

gdf_candidatos_filtrado['fecha_no'] = gdf_candidatos_filtrado.apply(asignar_fecha_desliz, axis=1)

paquete_B = gdf_candidatos_filtrado.copy()

#%%
#==============================================================================
# 6.3. Paquete C: distinta ubicación y distinta fecha
# Puntos aleatorios en la zona, >=100 m de un deslizamiento.
# Fechas aleatorias en [2016, 2024], a >=90 días de cualquier fecha de deslizamiento.
# El proceso es parecido a B, pero la asignación de fechas difiere:
#==============================================================================
with rasterio.open(ruta_esa) as src:
    puntos_candidatos = generar_puntos_aleatorios_en_raster(src, mask, num_puntos=3*num_deslizamientos*5)

gdf_candidatos = gpd.GeoDataFrame(geometry=[Point(p) for p in puntos_candidatos], crs="EPSG:3116")
gdf_candidatos_filtrado = filtrar_por_distancia_minima(gdf_candidatos, gdf_landslides, distancia_min=100)

# Seleccionamos 3 * num_deslizamientos puntos
gdf_candidatos_filtrado = gdf_candidatos_filtrado.sample(n=3*num_deslizamientos, random_state=42)

# Ahora asignamos fecha aleatoria en [2016, 2024] con >= 90 días de cualquier deslizamiento
# Creamos una lista de fechas de deslizamientos:
fechas_desliz = pd.to_datetime(gdf_landslides['fecha_ho_1']).dt.date

def asignar_fecha_distinta(row, fechas_desliz=fechas_desliz, dias_min=90):
    # Rango global
    fecha_inicio = datetime.date(2016, 1, 1)
    fecha_fin = datetime.date(2024, 12, 31)
    while True:
        fecha_random = generar_fecha_aleatoria(fecha_inicio, fecha_fin)
        # Verificar la distancia con TODAS las fechas de deslizamiento
        valido = True
        for fd in fechas_desliz:
            if abs((fecha_random - fd).days) < dias_min:
                valido = False
                break
        if valido:
            return fecha_random

gdf_candidatos_filtrado['fecha_no'] = gdf_candidatos_filtrado.apply(asignar_fecha_distinta, axis=1)

paquete_C = gdf_candidatos_filtrado.copy()

#%%
#==============================================================================
# 7. Guardar los paquetes
#==============================================================================
# Ahora tienes tres DataFrames (o GeoDataFrames):

# paquete_A: Misma ubicación, distinta fecha.
# paquete_B: Misma fecha, distinta ubicación (≥100 m).
# paquete_C: Distinta ubicación (≥100 m) y distinta fecha (≥90 días).
# Cada uno con un tamaño de 3 * num_deslizamientos (en total, cada paquete tendría 2700 muestras si había 900 deslizamientos). Es importante verificar que efectivamente llegaste a esa cantidad final, pues en la práctica puedes perder muestras en el filtrado de distancia o en la asignación de fechas.

# Podrías guardar los resultados en CSV para integrarlos en tu posterior modelado:

paquete_A.to_file(f"{ruta_guardar}paquete_A.geojson", driver="GeoJSON")
paquete_B.to_file(f"{ruta_guardar}paquete_B.geojson", driver="GeoJSON")
paquete_C.to_file(f"{ruta_guardar}paquete_C.geojson", driver="GeoJSON")

# O en CSV (pero perderás la geometría en formato WKT o similar):
# paquete_A.to_csv("paquete_A.csv", index=False)
# paquete_B.to_csv("paquete_B.csv", index=False)
# paquete_C.to_csv("paquete_C.csv", index=False)

#%%
#==============================================================================
# 8. Visualización de los paquetes
#==============================================================================
# Puedes visualizar los paquetes para verificar que todo está correcto. Por ejemplo, con GeoPandas y Matplotlib:

# 1. Reproyectar cada paquete a EPSG:4326
paquete_A_4326 = paquete_A.to_crs(epsg=4326)
paquete_B_4326 = paquete_B.to_crs(epsg=4326)
paquete_C_4326 = paquete_C.to_crs(epsg=4326)

# 2. Crear columnas de latitud y longitud a partir de la geometría
paquete_A_4326["latitud"] = paquete_A_4326.geometry.y
paquete_A_4326["longitud"] = paquete_A_4326.geometry.x

paquete_B_4326["latitud"] = paquete_B_4326.geometry.y
paquete_B_4326["longitud"] = paquete_B_4326.geometry.x

paquete_C_4326["latitud"] = paquete_C_4326.geometry.y
paquete_C_4326["longitud"] = paquete_C_4326.geometry.x

# 3. Guardar en formato GeoJSON
paquete_A_4326.to_file("paquete_A_4326.geojson", driver="GeoJSON")
paquete_B_4326.to_file("paquete_B_4326.geojson", driver="GeoJSON")
paquete_C_4326.to_file("paquete_C_4326.geojson", driver="GeoJSON")

print("¡Listo! Cada paquete se ha reproyectado a EPSG:4326, con columnas de lat/long y guardado en GeoJSON.")
# %%
#importar librerias
import geopandas as gpd

ruta_guardar = '../data/db_landslides/'
#abir los archivos guardados
paquete_A_4326 = gpd.read_file("paquete_A_4326.geojson")
paquete_B_4326 = gpd.read_file("paquete_B_4326.geojson")
paquete_C_4326 = gpd.read_file("paquete_C_4326.geojson")

#Pasar los archivos a formato csv
paquete_A_4326.to_csv(f"{ruta_guardar}paquete_A.csv", index=False)
paquete_B_4326.to_csv(f"{ruta_guardar}paquete_B.csv", index=False)
paquete_C_4326.to_csv(f"{ruta_guardar}paquete_C.csv", index=False)
# %%
