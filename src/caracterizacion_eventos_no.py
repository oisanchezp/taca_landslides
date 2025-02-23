#%%
#==============================================================================
# CARACTERIZACIÓN DE BASE DE DATOS DEL DAGRD
#==============================================================================

#Abrir las base de datos deslizamientos se encuentra en formato shapefile
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.plot import show
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterstats import zonal_stats
import os

#%%
#==============================================================================
# Cargar la base de datos de deslizamientos
#==============================================================================
print('Cargando base de datos de deslizamientos...')
ruta_eventos_no = '../data/db_landslides/'

#Cargamos bases de datos eventos que no son deslizamientos estan en formato .csv y
# en sistema de coordenadas EPSG:4326, abrir y pasar a EPSG:3116
# Paquete A
#ruta_a = f'{ruta_eventos_no}paquete_A_lluvia.csv'
#ruta_a = f'{ruta_eventos_no}paquete_B_lluvia.csv'
ruta_a = f'{ruta_eventos_no}paquete_C_lluvia.csv'
# Paquete A
bd_dagrd = pd.read_csv(ruta_a)
#%%
bd_dagrd = gpd.GeoDataFrame(bd_dagrd, geometry=gpd.points_from_xy(bd_dagrd.longitud, bd_dagrd.latitud))
bd_dagrd.crs = 'EPSG:4326'
bd_dagrd = bd_dagrd.to_crs('EPSG:3116')


ruta_mapas = '../data/variables/statics/'
#%%

#%%
#==============================================================================
# Reproyestamos mapa de coberuras de suelos
#==============================================================================

#abrimos mapa de coberturas de suelos para reproyectar a EPSG:3116
# mapa_coberturas = rasterio.open('../data/variables/statics/cober_med.tif')
# show(mapa_coberturas)

# #%%
# #reproyectar el mapa de coberturas de suelos a EPSG:3116
# dst_crs = 'EPSG:3116'
# transform, width, height = calculate_default_transform(mapa_coberturas.crs, dst_crs, mapa_coberturas.width, mapa_coberturas.height, *mapa_coberturas.bounds)
# kwargs = mapa_coberturas.meta.copy()
# kwargs.update({
#     'crs': dst_crs,
#     'transform': transform,
#     'width': width,
#     'height': height
# })

# with rasterio.open('../data/variables/statics/cober_med_3116.tif', 'w', **kwargs) as dst:
#     for i in range(1, mapa_coberturas.count + 1):
#         reproject(
#             source=rasterio.band(mapa_coberturas, i),
#             destination=rasterio.band(dst, i),
#             src_transform=mapa_coberturas.transform,
#             src_crs=mapa_coberturas.crs,
#             dst_transform=transform,
#             dst_crs=dst_crs,
#             resampling=Resampling.nearest
#         )

#%%
#==============================================================================
# Creamos bufer de 10 m alrededor de los deslizamientos
#==============================================================================
print('Creando buffer de 10 m alrededor de los deslizamientos...')
deslizamientos_buffer = bd_dagrd.copy()
deslizamientos_buffer["geometry"] = deslizamientos_buffer.geometry.buffer(10)  # buffer de 10 m

#%%
#==============================================================================
# Extreamos los valores del DEM, pendiente, aspecto, indice relativo de altura normalizado
#================================================================
print('Extrayendo valores de variables continuas...')

# 1. Extraer valores del DEM
stats_dem = zonal_stats(
    deslizamientos_buffer,         # Polígonos (buffer alrededor del punto)
    f'{ruta_mapas}dem_5_med.tif',                  # Ruta al DEM
    stats=["mean"],                # Queremos el promedio
    geojson_out=True
)

gdf_dem_stats = gpd.GeoDataFrame.from_features(stats_dem)
bd_dagrd["DEM_mean"] = [f["properties"]["mean"] for f in stats_dem]
#%%
# 2. Extraer valores de la pendiente
stats_slope = zonal_stats(
    deslizamientos_buffer,         # Polígonos (buffer alrededor del punto)
    f'{ruta_mapas}pendientes.tif',                  # Ruta a la pendiente
    stats=["mean"],                # Queremos el promedio
    geojson_out=True
)

gdf_slope_stats = gpd.GeoDataFrame.from_features(stats_slope)
bd_dagrd["slope_mean"] = [f["properties"]["mean"] for f in stats_slope]
#%%
# 3. Extraer valores del aspecto
stats_aspect = zonal_stats(
    deslizamientos_buffer,         # Polígonos (buffer alrededor del punto)
    f'{ruta_mapas}aspecto.tif',                  # Ruta al aspecto
    stats=["mean"],                # Queremos el promedio
    geojson_out=True
)

gdf_aspect_stats = gpd.GeoDataFrame.from_features(stats_aspect)
bd_dagrd["aspect_mean"] = [f["properties"]["mean"] for f in stats_aspect]
#%%
# 4. Extraer valores del índice relativo de altura normalizado
stats_nhd = zonal_stats(
    deslizamientos_buffer,         # Polígonos (buffer alrededor del punto)
    f'{ruta_mapas}nhi.tif',                  # Ruta al nhd
    stats=["mean"],                # Queremos el promedio
    geojson_out=True
)

gdf_nhd_stats = gpd.GeoDataFrame.from_features(stats_nhd)
bd_dagrd["nhd_mean"] = [f["properties"]["mean"] for f in stats_nhd]
#%%
#==============================================================================
# Extreamos los valores de variables categoricas: geología y cobertura de suelos
#================================================================
print('Extrayendo valores de variables categóricas...')

stats_geol = zonal_stats(
    bd_dagrd, 
    f'{ruta_mapas}geology.tif', 
    stats=["majority"],
    geojson_out=True
)
bd_dagrd["geo"] = [f["properties"]["majority"] for f in stats_geol]


#%%

#eliminar la columna Cobertura
#%%
stats_cobert = zonal_stats(
    bd_dagrd, 
    f'{ruta_mapas}cober_med_3116.tif', 
    stats=["majority"],
    geojson_out=True
)
bd_dagrd["cober"] = [f["properties"]["majority"] for f in stats_cobert]

#%%
#==============================================================================
# Extraemos valores de precipitación promedio anual de CHIRPS
#==============================================================================
print('Extrayendo valores de precipitación...')
import numpy as np
with rasterio.open(f'{ruta_mapas}pre_media_anual_2000_2024_2_clip.tif') as src:
    coords = [(geom.x, geom.y) for geom in bd_dagrd.geometry]
    vals = list(src.sample(coords))

# Cada elemento de vals es un array, p.ej. vals[i] = [valor_en_el_punto_i]
bd_dagrd["pre_anual"] = [v[0] for v in vals]

#%%

#==============================================================================
# Extracción de precipitación promedio mensual según el mes de ocurrencia
#==============================================================================

bd_dagrd["fecha"] = pd.to_datetime(bd_dagrd["fecha_no"], errors="coerce")
bd_dagrd["mes"] = bd_dagrd["fecha"].dt.month  # valores 1 a 12


# 1) Crear un diccionario mes -> ruta del tif
month_paths = {
    m: os.path.join(ruta_mapas, f"pre_media_mensual_{m:02d}.tif")
    for m in range(1, 13)
}
#%%

# 2) Iterar sobre cada deslizamiento, abrir el raster adecuado y extraer el valor
valores_mensuales = []
for idx, row in bd_dagrd.iterrows():
    mes_desliz = row['mes']  # columna con el número de mes
    # Si el mes es nulo o no está entre 1 y 12, asigna NaN
    if pd.isna(mes_desliz) or mes_desliz not in month_paths:
        valores_mensuales.append(np.nan)
        continue
    
    raster_path = month_paths[mes_desliz]
    
    with rasterio.open(raster_path) as src:
        # sample() devuelve un generador; cada item es un array con el valor(es)
        val_array = list(src.sample([(row.geometry.x, row.geometry.y)]))
        # El valor puntual está en la posición [0][0]
        # [0]: primer (y único) elemento devuelto, [0] valor en ese raster band
        val = val_array[0][0]
    
    valores_mensuales.append(val)

# 3) Añadir la nueva columna con el valor de precipitación mensual
bd_dagrd['pre_mensual'] = valores_mensuales

#%%
bd_dagrd
#%%
#==============================================================================
# Guardar la base de datos en formato csv
#==============================================================================
print('Guardando base de datos...')

#bd_dagrd.to_csv('../data/db_landslides/paquete_A_caracte.csv')
#bd_dagrd.to_csv('../data/db_landslides/paquete_B_caracte.csv')
bd_dagrd.to_csv('../data/db_landslides/paquete_C_caracte.csv')
#%%
#==============================================================================
#Guardar la base de datos en formato shapefile y csv
#==============================================================================
#bd_dagrd.to_file('../data/variables/statics/inventario_dagrd_caract.shp')
#bd_dagrd.drop(columns='geometry').to_csv('../data/variables/statics/inventario_dagrd_caract.csv')