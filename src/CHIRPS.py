#==============================================================================
# Descargar datos de precipitación de CHIRPS
#==============================================================================
# Importar módulo para descargar archivos

import urllib.request
# %%
# base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/"
# años = range(2023, 2025)  # Desde 2000 hasta 2024

# for año in años:
#     url = f"{base_url}chirps-v2.0.{año}.days_p05.nc"
#     archivo_salida = f"chirps-v2.0.{año}.days_p05.nc"
    
#     print(f"Descargando {archivo_salida}...")
    
#     urllib.request.urlretrieve(url, archivo_salida)
    
#     print(f"Descarga de {archivo_salida} completada.")

# %%
#==============================================================================
# SACAR EL PROMEDIO DE PRECIPITACIÓN ANUAL PARA MEDELLIN
#==============================================================================
import xarray as xr
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import geopandas as gpd
#%%
ruta_chirps = "../data/variables/statics/CHIRPS/"  # Ajusta con la ubicación de tus archivos
# Leer el shapefile de la zona de estudio y reproyectarlo a EPSG:4326
zona = gpd.read_file("../data/variables/statics/med.shp")
zona = zona.to_crs("EPSG:4326")

# %%
# Listar y ordenar los archivos
archivos_chirps = sorted(glob.glob(os.path.join(ruta_chirps, "chirps-v2.0.*.days_p05.nc")))

# Definir la zona de estudio (bounding box)
xmin, ymin, xmax, ymax = -75.807533 , 5.997960, -75.183943, 6.518359

# Diccionario para almacenar el acumulado anual en la zona de estudio
precipitacion_anual = {}

#%%
for archivo in archivos_chirps:
    print(f"Procesando {archivo}...")
    ds = xr.open_dataset(archivo)
    anio = int(os.path.basename(archivo).split(".")[2])
    # Seleccionar la zona de estudio usando los valores de lon y lat
    lluvia = ds["precip"].sel(longitude=slice(xmin, xmax), latitude=slice(ymin, ymax))
    # Sumar la precipitación de todos los días del año
    acumulado_anual = lluvia.sum(dim="time")
    precipitacion_anual[anio] = acumulado_anual
    ds.close()

# Concatenar los acumulados anuales a lo largo de un nuevo eje 'year' y calcular el promedio
precipitacion_media_anual = xr.concat(list(precipitacion_anual.values()), dim="year").mean(dim="year")


#%%
# Crear un Dataset final conservando las coordenadas del DataArray resultante
ds_media_anual = xr.Dataset({"PrecipMediaAnual": precipitacion_media_anual})
#%%
# Guardar el resultado en un archivo netCDF
ds_media_anual.to_netcdf("../data/variables/statics/pre_media_anual_2000_2024_2.nc")
#%%
#graficar la precipitación media anual
plt.figure(figsize=(10,6))
plt.imshow(precipitacion_media_anual, cmap="Blues", origin="lower")
plt.colorbar(label="Precipitación Media Anual (mm)")
plt.title("Precipitación Media Anual 2000-2024 - CHIRPS")
plt.show()

#%%
import xarray as xr
import rioxarray



ds = xr.open_dataset("../data/variables/statics/pre_media_anual_2000_2024_2.nc")
#%%
da = ds["PrecipMediaAnual"]

da = da.rename({"longitude": "x", "latitude": "y"})
da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
da = da.rio.write_crs("EPSG:4326")

#%%
#reproyectar a MAGNAS_TRANSVERSE_MERCATOR
da = da.rio.reproject("EPSG:3116")

da.rio.to_raster("../data/variables/statics/pre_media_anual_2000_2024_2.tif")

#%%
#recortar la precipitación media anual a la zona de estudio
import geopandas as gpd
from shapely.geometry import box

# Cargar el shapefile de la zona de estudio
zona = gpd.read_file("../data/variables/statics/med.shp")

#%%
# Extraer los límites de la zona de estudio
xmin, ymin, xmax, ymax = zona.total_bounds

# Crear un objeto de tipo box con los límites de la zona de estudio
study_area = box(xmin, ymin, xmax, ymax)

# Recortar la precipitación media anual a la zona de estudio
da_clip = da.rio.clip([study_area], crs="EPSG:3116", drop=True, all_touched=True)

# Guardar el resultado en un archivo GeoTIFF
da_clip.rio.to_raster("../data/variables/statics/pre_media_anual_2000_2024_2_clip.tif")

#%%

#%%

# %%
#==============================================================================
# ASIGNAR PRECIPTIACIÓN MEDIA ANUAL A CADA POLIGONO DE SLOPE UNITS
#==============================================================================
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

#%%

# Cargar los polígonos de Slope Units
slope_units = gpd.read_file("../data/variables/statics/su_med.shp")  # Reemplaza con tu archivo

# Ruta del ráster CHIRPS
raster_path = "../data/variables/statics/pre_media_anual_2000_2024_2_clip.tif"  # Reemplaza con tu archivo

#%%
# Calcular la media de precipitación dentro de cada polígono

stats = zonal_stats(slope_units, raster_path, stats=["mean"])

#%%
# Agregar la columna de precipitación media anual al GeoDataFrame
slope_units["map"] = [s["mean"] for s in stats]


#%%
# Guardar el nuevo shapefile con la columna agregada
slope_units.to_file("su_med.shp.shp")

print("Proceso terminado, archivo guardado con valores de precipitación")

#%%
#==============================================================================
# SACAR LA PRECIPITACIÓN PROMEDIO MENSUAL PARA MEDELLÍN
#==============================================================================

import xarray as xr
import rioxarray
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import geopandas as gpd

# %%
# Ruta donde se encuentran los archivos CHIRPS
ruta_chirps = "../data/variables/statics/CHIRPS/"

# Leer el shapefile (opcional si deseas usar un bounding box derivado)
zona = gpd.read_file("../data/variables/statics/med.shp")
zona = zona.to_crs("EPSG:4326")

# Definir la zona de estudio (bounding box)
xmin, ymin, xmax, ymax = -75.807533, 5.997960, -75.183943, 6.518359

# %%
# Listar y ordenar los archivos CHIRPS
archivos_chirps = sorted(glob.glob(os.path.join(ruta_chirps, "chirps-v2.0.*.days_p05.nc")))

# Abrir todos los archivos en un solo Dataset
# Ten en cuenta que esto puede requerir bastante memoria si los archivos son muy grandes
ds = xr.open_mfdataset(archivos_chirps, combine='by_coords')

# Recortar el Dataset a la zona de interés
# Utilizamos .sel con slice() en longitud (x) y latitud (y)
ds = ds.sel(longitude=slice(xmin, xmax), latitude=slice(ymin, ymax))

# Extraer la variable de precipitación
lluvia = ds["precip"]

# %%

# 3. CALCULAR LAS SERIES MENSUALES: SUMAR LA LLUVIA DIARIA DE CADA MES
# -----------------------------------------------------------------------------
# 'resample(time="1M").sum(dim="time")' va a generar el acumulado mensual para cada pixel
lluvia_mensual = lluvia.resample(time="1M").sum(dim="time")

# Ahora lluvia_mensual es un DataArray con valores mensuales (un valor por mes).
# Sus coordenadas de tiempo se encuentran al último día del mes (por convención xarray).

#%%
# 4. AGRUPAR POR MES PARA CREAR LA CLIMATOLOGÍA (PROMEDIO DE CADA MES A TRAVÉS DE LOS AÑOS)
# -----------------------------------------------------------------------------
# Ejemplo: todos los eneros de 1990-2024 se promedian -> month=1
#          todos los febreros de 1990-2024 -> month=2, etc.
lluvia_climatologia_mensual = lluvia_mensual.groupby("time.month").mean(dim="time")

# Resultado: DataArray con dimensión 'month' (1..12),
# donde cada 'month' es la precipitación promedio (acumulada) para ese mes.


# %%
# 5. REPROYECTAR Y GUARDAR CADA MES (ENE-DIC) COMO GeoTIFF
# -----------------------------------------------------------------------------
for mes in range(1, 13):
    # Seleccionar el DataArray para este mes
    data_mes = lluvia_climatologia_mensual.sel(month=mes)
    
    # Renombrar coords para que rioxarray entienda x e y
    data_mes = data_mes.rename({"longitude": "x", "latitude": "y"})
    
    # Asignar la proyección original WGS84
    data_mes = data_mes.rio.set_spatial_dims(x_dim="x", y_dim="y")
    data_mes = data_mes.rio.write_crs("EPSG:4326")
    
    # Reproyectar a MAGNAS_TRANSVERSE_MERCATOR (EPSG:3116)
    data_mes_3116 = data_mes.rio.reproject("EPSG:3116")
    
    # Generar el nombre de salida
    nombre_salida = f"../data/variables/statics/pre_media_mensual_{mes:02d}.tif"
    
    # Guardar en formato GeoTIFF
    data_mes_3116.rio.to_raster(nombre_salida)
    print(f"GeoTIFF del mes {mes} guardado en: {nombre_salida}")

# %%
# 6. OPCIONAL: VISUALIZAR UN MES DE EJEMPLO
# -----------------------------------------------------------------------------
mes_ejemplo = 4  # Abril
data_mes_abril = lluvia_climatologia_mensual.sel(month=mes_ejemplo)

plt.figure(figsize=(8,6))
data_mes_abril.plot(cmap="Blues")
plt.title(f"Precipitación Media Mensual (Acumulada) - Mes {mes_ejemplo}")
plt.show()

# Cerrar dataset
ds.close()
# %%
