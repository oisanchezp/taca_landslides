
#%%
#==============================================================================
# SACAR LAS LLUVIAS ANTECEDENTES DE CORTO Y LARGO PLAZO PARA CARACTERIZAR LOS DESLIZAMIENTOS
#==============================================================================
import numpy as np
import glob
import os
import re
import numpy as np
import pandas as pd
from math import radians, cos, sin, asin, sqrt
from datetime import timedelta
#%%%
# Cargar la base de datos de deslizamientos en formato .csv
bd_dagrd = pd.read_csv('../data/variables/statics/inventario_dagrd_caract.csv')

short_windows = [1, 3, 5, 7, 10]    # días
long_windows = [15, 20, 30, 40, 50, 60, 90]  # días

# Directorio de los CSV del radar
csv_dir = "/mnt/investigacion/geotecnia/series_de_tiempo/"

#%%

def haversine(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos puntos (lat, lon)."""
    # Convertir a radianes
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radio promedio de la Tierra, en km
    return r * c

def cuatro_celdas_mas_cercanas(lat_ev, lon_ev):
    dist_list = []
    for (fpath, lat_celda, lon_celda) in coords_celdas:
        dist_km = haversine(lat_ev, lon_ev, lat_celda, lon_celda)
        dist_list.append((dist_km, fpath, lat_celda, lon_celda))
    dist_list.sort(key=lambda x: x[0])  # orden asc
    return dist_list[:4]
#%%
print('Sacando las coordenadas de las celdas del radar')
# B) Construir lista con (ruta_csv, lat, lon)
csv_files = sorted(glob.glob(os.path.join(csv_dir, "serie_tiempo_(*.csv")))
coords_celdas = []  # (fpath, lat, lon)

patron = r"serie_tiempo_\((-?\d+\.\d+),\s?(\d+\.\d+)\).csv"

for fpath in csv_files:
    fname = os.path.basename(fpath)
    match = re.search(patron, fname)
    if match:
        lon_celda = float(match.group(1))
        lat_celda = float(match.group(2))
        coords_celdas.append((fpath, lat_celda, lon_celda))

print('Fin celdas del radar')


#%%
cache_series = {}  # Diccionario global: { ruta_csv: df_pandas }

def get_serie_lluvia(fpath):
    """Retorna un DataFrame con índice datetime y la columna de precip,
       usando cache para no re-leer el archivo en disco.
    """
    if fpath not in cache_series:
        df = pd.read_csv(fpath, parse_dates=["datetime"], index_col="datetime")
        col_name = df.columns[0]
        df = df.rename(columns={col_name: "rain_mm"})
        cache_series[fpath] = df
    return cache_series[fpath]

#%%
def lluvia_corto_largo(df_lluvia, fecha_evento, short_days, long_days):
    """
    Retorna (acum_corto, acum_largo):
    - acum_corto: lluvia en [evento - short_days, evento)
    - acum_largo: lluvia en [evento - (short_days+long_days), evento - short_days)
    """
    inicio_corto = fecha_evento - timedelta(days=short_days)
    df_corto = df_lluvia.loc[inicio_corto:fecha_evento]
    acum_corto = df_corto["rain_mm"].sum()

    # Largo plazo se calcula hasta el inicio del corto plazo
    fin_largo = inicio_corto
    inicio_largo = fin_largo - timedelta(days=long_days)
    df_largo = df_lluvia.loc[inicio_largo:fin_largo]
    acum_largo = df_largo["rain_mm"].sum()
    return acum_corto, acum_largo

#%%
print('Iniciando el bucle de deslizamientos')
# Convertir la columna de fecha a datetime (si no lo estaba)
bd_dagrd["fecha_ho_1"] = pd.to_datetime(bd_dagrd["fecha_ho_1"], errors="coerce")

# --- Generar nombres de columnas en el GeoDataFrame para cada combinación

print('Calculo corto plazo')

# A) Crear las columnas en el GeoDataFrame
for s in short_windows:
    bd_dagrd[f"cp{s}"] = np.nan  # ejemplo: cp1, cp3, cp5, cp7, cp10

# B) Iterar sobre cada deslizamiento
for idx, row in bd_dagrd.iterrows():
    print(f"Calculando deslizamiento {idx} de {len(bd_dagrd)}")
    fecha_evento = row["fecha_ho_1"]
    if pd.isna(fecha_evento):
        continue  # Si no hay fecha, no podemos calcular
    
    lat_ev = row["latitud"]
    lon_ev = row["longitud"]
    celdas_cercanas = cuatro_celdas_mas_cercanas(lat_ev, lon_ev)

    # Para cada ventana de corto plazo
    for s in short_windows:
        max_corto_4cel = -9999
        # Revisar las 4 celdas y quedarnos con el máximo acumulado
        for dist, fpath, lat_celda, lon_celda in celdas_cercanas:
            df_lluvia = get_serie_lluvia(fpath)
            acum_corto, _ = lluvia_corto_largo(df_lluvia, fecha_evento, short_days=s, long_days=0)
            # (colocamos long_days=0 para "no calcular" nada adicional)
            
            if acum_corto > max_corto_4cel:
                max_corto_4cel = acum_corto
        
        bd_dagrd.loc[idx, f"cp{s}"] = max_corto_4cel
print('Fin de la creación de columnas corto plazo')

print('Calculo largo plazo')
# A) Crear las columnas de largo plazo
for s in short_windows:
    for l in long_windows:
        col_lp = f"lp{l}_cp{s}"  # ejemplo: lp15_cp1
        bd_dagrd[col_lp] = np.nan

# B) Iterar de nuevo
for idx, row in bd_dagrd.iterrows():
    print(f"Calculando deslizamiento {idx} de {len(bd_dagrd)}")
    fecha_evento = row["fecha_ho_1"]
    if pd.isna(fecha_evento):
        continue
    
    lat_ev = row["latitud"]
    lon_ev = row["longitud"]
    celdas_cercanas = cuatro_celdas_mas_cercanas(lat_ev, lon_ev)

    for s in short_windows:
        for l in long_windows:
            col_lp = f"lp{l}_cp{s}"
            max_largo_4cel = -9999
            
            for dist, fpath, lat_celda, lon_celda in celdas_cercanas:
                df_lluvia = get_serie_lluvia(fpath)
                _, acum_largo = lluvia_corto_largo(df_lluvia, fecha_evento, short_days=s, long_days=l)
                
                if acum_largo > max_largo_4cel:
                    max_largo_4cel = acum_largo
            
            bd_dagrd.loc[idx, col_lp] = max_largo_4cel


# FIN DEL BUCLE DE DESLIZAMIENTOS
print('Fin del bucle de deslizamientos, guardando el archivo')
# Guardar el resultado
bd_dagrd.to_csv("../data/variables/statics/bd_dagrd_lluvia.csv", index=False)
