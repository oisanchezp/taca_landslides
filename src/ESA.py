
#%%
import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
from shapely.geometry import Point
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import MultiLineString, LineString

from scipy.spatial import cKDTree

import statsmodels.api as sm

from rasterio.mask import mask
from rasterio import transform
from rasterio.transform import from_origin
#%%
#==============================================================================
#📌 Paso 1: Cargar los Datos
#==============================================================================
ruta_var = '../data/variables/statics/'
# Cargar el inventario de deslizamientos
df_deslizamientos = pd.read_csv(f"{ruta_var}bd_dagrd_lluvia.csv")

# Convertir a GeoDataFrame
gdf_deslizamientos = gpd.GeoDataFrame(
    df_deslizamientos, 
    geometry=gpd.points_from_xy(df_deslizamientos["longitud"], df_deslizamientos["latitud"]),
    crs="EPSG:4326"  # Asegurar el CRS correcto
)

# Cargar la malla vial (vías como polilíneas)
gdf_vias = gpd.read_file(f"{ruta_var}vias.shp")

# Cargar las edificaciones (polígonos)
gdf_edificaciones = gpd.read_file(f"{ruta_var}edi_urbano_rural.shp")

# Cargar el DEM
# with rasterio.open(f"{ruta_var}dem_5_med.tif") as dem:
#     dem_data = dem.read(1)  # Leer banda 1
#     dem_transform = dem.transform
#     dem_crs = dem.crs

# %%


fig, ax = plt.subplots(figsize=(10, 8))
gdf_deslizamientos.plot(ax=ax, color='red', markersize=5, label="Deslizamientos")
gdf_vias.plot(ax=ax, color='black', linewidth=0.5, label="Vías")
gdf_edificaciones.plot(ax=ax, color='blue', alpha=0.5, label="Edificaciones")
ax.legend()
plt.title("Datos de Entrada para la ESA")
plt.show()
# %%
#==============================================================================
#📌 Paso 2: Calcular Distancias a Infraestructura
#==============================================================================

#Extraer coordenadas de los puntos de deslizamientos
desliz_coords = np.array([(p.x, p.y) for p in gdf_deslizamientos.geometry])

# Extraer coordenadas de las vías (polilíneas)
# Extraer coordenadas de las vías (incluyendo MultiLineString)
vias_coords = []

for geom in gdf_vias.geometry:
    if geom is not None:
        if isinstance(geom, LineString):  # Caso 1: Si es LineString, extraer coordenadas directamente
            vias_coords.extend(geom.coords)
        elif isinstance(geom, MultiLineString):  # Caso 2: Si es MultiLineString, iterar sobre cada LineString interno
            for line in geom.geoms:
                vias_coords.extend(line.coords)

# Convertir a array de NumPy
vias_coords = np.array(vias_coords)
# Extraer coordenadas de las edificaciones (centroides)
edif_coords = np.array([(poly.centroid.x, poly.centroid.y) for poly in gdf_edificaciones.geometry if poly is not None])
#%%
# Función para calcular distancia mínima
def calcular_distancia(puntos, ref_points):
    tree = cKDTree(ref_points)
    distancias, _ = tree.query(puntos, k=1)
    return distancias

#%%
# Calcular distancias mínimas
gdf_deslizamientos["dist_vias"] = calcular_distancia(desliz_coords, vias_coords)
gdf_deslizamientos["dist_edif"] = calcular_distancia(desliz_coords, edif_coords)
# %%
#==============================================================================
#📌 Paso 3: Ajustar el Modelo de Probabilidad de Registro
#==============================================================================
#Usamos Regresión Logística para modelar la probabilidad de que un deslizamiento
#  sea registrado en función de la distancia a infraestructura y la altitud.


#%%

# Variables predictoras
X = gdf_deslizamientos[["dist_vias", "dist_edif"]]
X = sm.add_constant(X)

# Variable objetivo (1 = registrado, asumimos presencia)
y = np.ones(len(gdf_deslizamientos)) 

# Ajustar modelo logístico
modelo = sm.Logit(y, X).fit()

# Resumen del modelo
print(modelo.summary())
# %%
#==============================================================================
#📌 Paso 4: Aplicar el Modelo a Todo el Área de Estudio
#==============================================================================
#Ahora aplicamos el modelo a una malla de puntos en toda la zona de estudio
#  para estimar la probabilidad de registro.

# Crear una cuadrícula de 100x100m en toda la zona de estudio
res_x, res_y = 100, 100
# Conversión de metros a grados geográficos (aprox. a latitud 6.26°)
res_x_deg = res_x / (111320 * np.cos(np.radians(6.26)))  # Convertir 100 m a grados de longitud
res_y_deg = res_y / 111320  # Convertir 100 m a grados de latitud

xmin, ymin, xmax, ymax = gdf_deslizamientos.total_bounds
x_vals = np.arange(xmin, xmax, res_x_deg)
y_vals = np.arange(ymin, ymax, res_y_deg)
xx, yy = np.meshgrid(x_vals, y_vals)
grid_coords = np.column_stack([xx.ravel(), yy.ravel()])

#%%
def calcular_distancia(puntos, ref_points):
    """
    Calcula la distancia mínima entre cada punto en `puntos` y el conjunto de puntos `ref_points`.
    
    - `puntos`: array de coordenadas [(x1, y1), (x2, y2), ...]
    - `ref_points`: array de coordenadas de referencia [(xr1, yr1), (xr2, yr2), ...]
    
    Retorna: array con la distancia mínima de cada punto en `puntos` al punto más cercano en `ref_points`.
    """
    if len(ref_points) == 0:  # Si no hay puntos de referencia, devolver NaN
        return np.full(len(puntos), np.nan)
    
    # Construir un árbol KD con los puntos de referencia
    tree = cKDTree(ref_points)
    
    # Calcular la distancia mínima para cada punto en `puntos`
    distancias, _ = tree.query(puntos, k=1)  # k=1 -> Solo buscamos el punto más cercano
    
    return distancias

#%%

# Calcular distancia a infraestructura para cada celda
grid_dist_vias = calcular_distancia(grid_coords, vias_coords)
grid_dist_edif = calcular_distancia(grid_coords, edif_coords)

#%%
import rasterio

# Abrir el DEM y verificar su CRS (sistema de referencia de coordenadas)
with rasterio.open(f"{ruta_var}dem_5_med.tif") as dem:
    print("CRS del DEM:", dem.crs)  # Esto mostrará algo como 'EPSG:32618' (UTM) o similar

#%%
from pyproj import Transformer
from shapely.geometry import Point

# Definir el transformador de coordenadas
transformer = Transformer.from_crs("EPSG:4326", dem_crs, always_xy=True)

# Convertir las coordenadas de la cuadrícula a UTM o la proyección del DEM
grid_coords_utm = np.array([transformer.transform(x, y) for x, y in grid_coords])

# Usamos las coordenadas proyectadas para definir la cuadrícula en metros
xmin, ymin, xmax, ymax = gdf_deslizamientos.to_crs(dem_crs).total_bounds  # Convertimos al CRS del DEM

# Tamaño de celda en metros (100m x 100m)
res_x, res_y = 100, 100  

# Generar los valores de la cuadrícula en el CRS del DEM
x_vals = np.arange(xmin, xmax, res_x)
y_vals = np.arange(ymin, ymax, res_y)

# Verificar que tenemos más de un punto
print("Número de puntos en x_vals:", len(x_vals))
print("Número de puntos en y_vals:", len(y_vals))

# Crear la malla de puntos en coordenadas proyectadas
xx, yy = np.meshgrid(x_vals, y_vals)
grid_coords = np.column_stack([xx.ravel(), yy.ravel()])
#%%
# Obtener altitud desde el DEM para cada celda de la malla
# Obtener altitud para cada celda de la malla usando las coordenadas transformadas
grid_altitud = obtener_altitud([Point(x, y) for x, y in grid_coords_utm], dem_data, dem_transform)
# Calcular distancias a infraestructura en la proyección correcta
grid_dist_vias = calcular_distancia(grid_coords, vias_coords)
grid_dist_edif = calcular_distancia(grid_coords, edif_coords)
# Verificar si ahora hay valores en lugar de NaN
print("Valores de altitud (primeros 10):", grid_altitud[:10])
#%%
#mostrar los valores de grid_altitud diferentes a -999.
print("Valores de altitud diferentes a -999:", grid_altitud[grid_altitud != -999])

#%%

# Construir la matriz de predicción con todas las variables
grid_X = np.column_stack([grid_dist_vias, grid_dist_edif, grid_altitud])
grid_X = sm.add_constant(grid_X)  # Agregar la constante

# Aplicar el modelo para predecir probabilidad de registro de deslizamientos
grid_probs = modelo.predict(grid_X).reshape(xx.shape)
#%%





# Crear matriz de predicción asegurando que todas las variables coincidan con el modelo
grid_X = np.column_stack([grid_dist_vias, grid_dist_edif, grid_altitud])

# Agregar la constante (intercepto) como en el entrenamiento
grid_X = sm.add_constant(grid_X)

# Aplicar el modelo corregido
grid_probs = modelo.predict(grid_X).reshape(xx.shape)
#%%
# Guardar raster de probabilidades
transform = from_origin(xmin, ymax, res_x, res_y)
with rasterio.open(f"{ruta_var}ESA_probabilidad.tif", "w", driver="GTiff",
                   height=grid_probs.shape[0], width=grid_probs.shape[1],
                   count=1, dtype=grid_probs.dtype, transform=transform) as dst:
    dst.write(grid_probs, 1)

# %%
#==============================================================================
#📌 Paso 5: Convertir a un Mapa Binario ESA / No-ESA
#==============================================================================
from sklearn.metrics import roc_curve


fpr, tpr, thresholds = roc_curve(y, modelo.predict(X))
youden_index = thresholds[np.argmax(tpr - fpr)]

# Generar mapa binario ESA
ESA_binario = (grid_probs >= youden_index).astype(int)

# Guardar como raster
with rasterio.open(f"{ruta_var}ESA_binario.tif", "w", driver="GTiff",
                   height=ESA_binario.shape[0], width=ESA_binario.shape[1],
                   count=1, dtype=ESA_binario.dtype, transform=transform) as dst:
    dst.write(ESA_binario, 1)

#%%
# Visualizar el mapa binario agragar el dem

fig, ax = plt.subplots(figsize=(10, 8))
ax.imshow(ESA_binario, extent=[xmin, xmax, ymin, ymax], cmap="viridis")
#gdf_deslizamientos.plot(ax=ax, color='red', markersize=5, label="Deslizamientos")
gdf_vias.plot(ax=ax, color='black', linewidth=0.5, label="Vías")
gdf_edificaciones.plot(ax=ax, color='blue', alpha=0.5, label="Edificaciones")
ax.legend()
plt.title("Mapa Binario de ESA")
plt.show()

# %%

