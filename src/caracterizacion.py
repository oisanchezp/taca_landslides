
#%%
import pandas as pd
import matplotlib.pyplot as plt


#%%
#abir archivo csv
# df = pd.read_csv('../data/db_landslides/bd_eventos_dagrd_materializados.csv')

# # %%
# #hacer un filtro por la columnas 'origen' solo desde los "Natural" y 'Socionatural'
# df =df[df['tipo_incidente'] == 'Movimiento en masa']

# df = df[(df['origen'] == 'Natural') | (df['origen'] == 'Socionatural') | (df['origen'] == 'Antrópico')]


# # %%
# # Convertir la columna 'fecha_ocurrencia' a formato datetime
# df['fecha_ocurrencia'] = pd.to_datetime(df['fecha_ocurrencia'], errors='coerce')

# # Filtrar filas válidas
# df_valid = df.dropna(subset=['fecha_ocurrencia'])

# # Extraer el mes de la fecha de ocurrencia
# df_valid['mes'] = df_valid['fecha_ocurrencia'].dt.month

# # Agrupar por mes
# monthly_landslides = df_valid.groupby('mes').size()

# # Crear etiquetas de los meses
# meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
#          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# # Reordenar datos según los meses del año
# monthly_landslides = monthly_landslides.reindex(range(1, 13), fill_value=0)
# #%%
# # Graficar
# plt.figure(figsize=(10, 6))
# plt.bar(meses, monthly_landslides, color='skyblue', edgecolor='black')
# plt.title('Número de deslizamientos por mes', fontsize=14)
# plt.xlabel('Mes', fontsize=12)
# plt.ylabel('Número de deslizamientos', fontsize=12)
# plt.xticks(rotation=45)
# plt.grid(axis='y', linestyle='--', alpha=0.7)
# plt.tight_layout()
# plt.show()
# # %%
# df_geo = pd.read_csv('../data/db_landslides/inventory_GEOHAZARDS_20240824.csv')
# # %%
# #hacer un filtro por la columnas 'origen' solo desde los "Natural" y 'Socionatural'
# #df_geo = df_geo[(df_geo['origen'] == 'Natural') | (df_geo['origen'] == 'Socionatural') | (df_geo['origen'] == 'Antrópico')]

# #hacer filtro de la columna Municipio solo para Medellin
# df_geo = df_geo[(df_geo['Municipio'] == 'Medellín') | (df_geo['Municipio'] == 'Medellin')]

# df_geo = df_geo[()]

# # %%
# # Convertir la columna 'fecha_ocurrencia' a formato datetime
# df_geo['Fecha'] = pd.to_datetime(df_geo['Fecha'], errors='coerce')

# #recortar las Fechas desde el 2012
# df_geo = df_geo[(df_geo['Fecha'] > '2012-01-01')]


# # Filtrar filas válidas
# df_valid = df_geo.dropna(subset=['Fecha'])

# # Extraer el mes de la fecha de ocurrencia
# df_valid['mes'] = df_valid['Fecha'].dt.month

# # Agrupar por mes
# monthly_landslides = df_valid.groupby('mes').size()

# # Crear etiquetas de los meses
# meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
#          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# # Reordenar datos según los meses del año
# monthly_landslides = monthly_landslides.reindex(range(1, 13), fill_value=0)
# #%%
# # Graficar
# plt.figure(figsize=(10, 6))
# plt.bar(meses, monthly_landslides, color='skyblue', edgecolor='black')
# plt.title('Número de deslizamientos por mes', fontsize=14)
# plt.xlabel('Mes', fontsize=12)
# plt.ylabel('Número de deslizamientos', fontsize=12)
# plt.xticks(rotation=45)
# plt.grid(axis='y', linestyle='--', alpha=0.7)
# plt.tight_layout()
# plt.show()
# # %%
# #%%

# # Extraer día, mes y año para realizar comparaciones más precisas
# df['fecha_simple'] = df['fecha_ocurrencia'].dt.date
# df = df.drop_duplicates(subset=['fecha_simple'])
# df_geo['fecha_simple'] = df_geo['Fecha'].dt.date

# # Buscar intersección de fechas
# fechas_comunes = pd.merge(df, df_geo, left_on='fecha_simple', right_on='fecha_simple', how='inner')

# # Seleccionar columnas relevantes para mostrar
# fechas_comunes_seleccionadas = fechas_comunes[[
#     'fecha_simple',  # Fecha en común
#     #'origen',  # Origen del deslizamiento
# ]]
# %%


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

# Cargar la base de datos de deslizamientos
bd_dagrd = gpd.read_file('../data/variables/statics/inventario_dagrd_repro.shp')

#mirar las columnas de la base de datos
bd_dagrd.columns


ruta_mapas = '../data/variables/statics/'
#%%
#==============================================================================
# Reproyestamos mapa de coberuras de suelos
#==============================================================================

#abrimos mapa de coberturas de suelos para reproyectar a EPSG:3116
mapa_coberturas = rasterio.open('../data/variables/statics/cober_med.tif')
show(mapa_coberturas)

#%%
#reproyectar el mapa de coberturas de suelos a EPSG:3116
dst_crs = 'EPSG:3116'
transform, width, height = calculate_default_transform(mapa_coberturas.crs, dst_crs, mapa_coberturas.width, mapa_coberturas.height, *mapa_coberturas.bounds)
kwargs = mapa_coberturas.meta.copy()
kwargs.update({
    'crs': dst_crs,
    'transform': transform,
    'width': width,
    'height': height
})

with rasterio.open('../data/variables/statics/cober_med_3116.tif', 'w', **kwargs) as dst:
    for i in range(1, mapa_coberturas.count + 1):
        reproject(
            source=rasterio.band(mapa_coberturas, i),
            destination=rasterio.band(dst, i),
            src_transform=mapa_coberturas.transform,
            src_crs=mapa_coberturas.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )

#%%
#==============================================================================
# Creamos bufer de 10 m alrededor de los deslizamientos
#==============================================================================
deslizamientos_buffer = bd_dagrd.copy()
deslizamientos_buffer["geometry"] = deslizamientos_buffer.geometry.buffer(10)  # buffer de 10 m

#%%
#==============================================================================
# Extreamos los valores del DEM, pendiente, aspecto, indice relativo de altura normalizado
#================================================================


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

bd_dagrd["fecha"] = pd.to_datetime(bd_dagrd["fecha_ho_1"], errors="coerce")
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
#==============================================================================
#Guardar la base de datos en formato shapefile y csv
#==============================================================================
bd_dagrd.to_file('../data/variables/statics/inventario_dagrd_caract.shp')
bd_dagrd.drop(columns='geometry').to_csv('../data/variables/statics/inventario_dagrd_caract.csv')

#%%
#==============================================================================
# Hacer un analisis exploratorio de los datos
#==============================================================================
import matplotlib.pyplot as plt
# Cargar la base de datos de deslizamientos
bd_dagrd = gpd.read_file('../data/variables/statics/inventario_dagrd_caract.shp')

#%%
# Histograma de la precipitación anual
plt.figure(figsize=(8, 6))
plt.hist(bd_dagrd["pre_anual"], bins=20, color="skyblue", edgecolor="black")
plt.title("Histograma de precipitación anual", fontsize=16)
plt.xlabel("Precipitación anual (mm)", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()
# %%
# Histograma de la precipitación mensual
plt.figure(figsize=(8, 6))
plt.hist(bd_dagrd["pre_mensual"], bins=20, color="skyblue", edgecolor="black")
plt.title("Histograma de precipitación mensual", fontsize=16)
plt.xlabel("Precipitación mensual (mm)", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# %%
# Histograma de la pendiente
plt.figure(figsize=(8, 6))
plt.hist(bd_dagrd["slope_mean"], bins=20, color="skyblue", edgecolor="black")
plt.title("Histograma de pendiente", fontsize=16)
plt.xlabel("Pendiente (grados)", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# %%
# Histograma del aspecto
plt.figure(figsize=(8, 6))
plt.hist(bd_dagrd["aspect_mean"], bins=20, color="skyblue", edgecolor="black")
plt.title("Histograma de aspecto", fontsize=16)
plt.xlabel("Aspecto (grados)", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# %%
# Histograma del índice relativo de altura normalizado
plt.figure(figsize=(8, 6))
plt.hist(bd_dagrd["nhd_mean"], bins=20, color="skyblue", edgecolor="black")
plt.title("Histograma de NHD", fontsize=16)
plt.xlabel("NHD", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()


# %%
# Histograma de la geología
plt.figure(figsize=(8, 6))
bd_dagrd["geo"].value_counts().plot(kind="bar", color="skyblue", edgecolor="black")
plt.title("Histograma de geología", fontsize=16)
plt.xlabel("Geología", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# %%
# Histograma de la cobertura de suelos
plt.figure(figsize=(8, 6))
bd_dagrd["cober"].value_counts().plot(kind="bar", color="skyblue", edgecolor="black")
plt.title("Histograma de cobertura de suelos", fontsize=16)
plt.xlabel("Cobertura de suelos", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# %%
# Histograma del mes de ocurrencia
plt.figure(figsize=(8, 6))
bd_dagrd["mes"].value_counts().plot(kind="bar", color="skyblue", edgecolor="black")
plt.title("Histograma de mes de ocurrencia", fontsize=16)
plt.xlabel("Mes", fontsize=14)
plt.ylabel("Número de deslizamientos", fontsize=14)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()
#%%



# %%
