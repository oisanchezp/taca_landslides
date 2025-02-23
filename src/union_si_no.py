#%%
import pandas as pd



ruta_bd = '../data/db_landslides/'

# Cargar el inventario de deslizamientos
df_deslizamientos = pd.read_csv(f"{ruta_bd}bd_dagrd_lluvia_filtrada.csv")

#quiero eliminar columnas que no me sirven y renombrar otras
df_deslizamientos.columns
# %%
#Quiero eliminar las columnas 'Unnamed: 0', 'id', 'fecha_hora', 'nombre_del', 'entidad', 'cargo'
#  'incertidum',  'incertid_1','tipo_movim', 'origen', 'municipio', 'corregimie', 'vereda_bar',
# 'sector', 'direccion', 'muertes', 'heridos', 'desapareci', 'otras_afec',
# 'fuente', 'observacio', 'validado'

df_deslizamientos = df_deslizamientos.drop(columns=['Unnamed: 0', 'id', 'fecha_hora', 'nombre_del', 'entidad', 'cargo',
                                                    'incertidum',  'incertid_1','tipo_movim', 'origen', 'municipio', 'corregimie', 'vereda_bar',
                                                    'sector', 'direccion', 'muertes', 'heridos', 'desapareci', 'otras_afec',
                                                    'fuente', 'observacio', 'validado'])

#renombrar la columnas 'fecha_ho_1' por 'fecha_hora'
df_deslizamientos = df_deslizamientos.rename(columns={'fecha_ho_1': 'fecha_hora'})

#agregar una columnas al final que se llame 'si_no' y que tenga valores de 1
df_deslizamientos['si_no'] = 1
#%%
#==============================================================================
# Cargar la base de datos de no deslizamientos paquete A
#==============================================================================
# Cargar los eventos que no son deslizamientos
df_no_deslizamientos_a = pd.read_csv(f"{ruta_bd}paquete_A_caracte.csv")

#%%
#eliminar columnas que no me sirven 'Unnamed: 0', 'fecha_ho_1', 'geometry'
df_no_deslizamientos_a = df_no_deslizamientos_a.drop(columns=['Unnamed: 0', 'fecha_ho_1', 'geometry'])

#renombrar la columna 'fecha_no' por 'fecha_hora'
df_no_deslizamientos_a = df_no_deslizamientos_a.rename(columns={'fecha_no': 'fecha_hora'})

#Reorganizar las columnas para que coincidan con el inventario de deslizamientos
#poner las columnas DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 'geo',
# #'cober', 'pre_anual', 'fecha', 'mes', 'pre_mensual' antes que 'cp1', 'cp2', 'cp3', 'cp4', 'cp5', 'cp6', 'cp7', 'cp8', 'cp9', 'cp10'
df_no_deslizamientos_a = df_no_deslizamientos_a[['fecha_hora', 'latitud', 'longitud', 'DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 'geo',
    'cober', 'pre_anual', 'fecha', 'mes', 'pre_mensual', 'cp1', 'cp3', 'cp5', 'cp7', 'cp10',
       'lp15_cp1', 'lp20_cp1', 'lp30_cp1', 'lp40_cp1', 'lp50_cp1', 'lp60_cp1',
       'lp90_cp1', 'lp15_cp3', 'lp20_cp3', 'lp30_cp3', 'lp40_cp3', 'lp50_cp3',
       'lp60_cp3', 'lp90_cp3', 'lp15_cp5', 'lp20_cp5', 'lp30_cp5', 'lp40_cp5',
       'lp50_cp5', 'lp60_cp5', 'lp90_cp5', 'lp15_cp7', 'lp20_cp7', 'lp30_cp7',
       'lp40_cp7', 'lp50_cp7', 'lp60_cp7', 'lp90_cp7', 'lp15_cp10',
       'lp20_cp10', 'lp30_cp10', 'lp40_cp10', 'lp50_cp10', 'lp60_cp10',
       'lp90_cp10']]

#agregar una columnas al final que se llame 'si_no' y que tenga valores de 0
df_no_deslizamientos_a['si_no'] = 0

# %%
df_deslizamientos = df_deslizamientos.reset_index(drop=True)
df_no_deslizamientos_a = df_no_deslizamientos_a.reset_index(drop=True)
#Unier los dos dataframes
df_si_no_a = pd.concat([df_deslizamientos, df_no_deslizamientos_a], ignore_index=True)

# %%
#Guardar el dataframe
df_si_no_a.to_csv(f"{ruta_bd}si_no_a.csv", index=False)


# %%
#==============================================================================
# Cargar la base de datos de no deslizamientos paquete B
#==============================================================================

# Cargar los eventos que no son deslizamientos
df_no_deslizamientos_a = pd.read_csv(f"{ruta_bd}paquete_B_caracte.csv")

df_no_deslizamientos_a.columns
#%%
#eliminar columnas que no me sirven 'Unnamed: 0', 'fecha_ho_1', 'geometry'
df_no_deslizamientos_a = df_no_deslizamientos_a.drop(columns=['Unnamed: 0', 'geometry'])

#renombrar la columna 'fecha_no' por 'fecha_hora'
df_no_deslizamientos_a = df_no_deslizamientos_a.rename(columns={'fecha_no': 'fecha_hora'})

#Reorganizar las columnas para que coincidan con el inventario de deslizamientos
#poner las columnas DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 'geo',
# #'cober', 'pre_anual', 'fecha', 'mes', 'pre_mensual' antes que 'cp1', 'cp2', 'cp3', 'cp4', 'cp5', 'cp6', 'cp7', 'cp8', 'cp9', 'cp10'
df_no_deslizamientos_a = df_no_deslizamientos_a[['fecha_hora', 'latitud', 'longitud', 'DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 'geo',
    'cober', 'pre_anual', 'fecha', 'mes', 'pre_mensual', 'cp1', 'cp3', 'cp5', 'cp7', 'cp10',
       'lp15_cp1', 'lp20_cp1', 'lp30_cp1', 'lp40_cp1', 'lp50_cp1', 'lp60_cp1',
       'lp90_cp1', 'lp15_cp3', 'lp20_cp3', 'lp30_cp3', 'lp40_cp3', 'lp50_cp3',
       'lp60_cp3', 'lp90_cp3', 'lp15_cp5', 'lp20_cp5', 'lp30_cp5', 'lp40_cp5',
       'lp50_cp5', 'lp60_cp5', 'lp90_cp5', 'lp15_cp7', 'lp20_cp7', 'lp30_cp7',
       'lp40_cp7', 'lp50_cp7', 'lp60_cp7', 'lp90_cp7', 'lp15_cp10',
       'lp20_cp10', 'lp30_cp10', 'lp40_cp10', 'lp50_cp10', 'lp60_cp10',
       'lp90_cp10']]

#agregar una columnas al final que se llame 'si_no' y que tenga valores de 0
df_no_deslizamientos_a['si_no'] = 0

# %%
df_deslizamientos = df_deslizamientos.reset_index(drop=True)
df_no_deslizamientos_a = df_no_deslizamientos_a.reset_index(drop=True)
#Unier los dos dataframes
df_si_no_a = pd.concat([df_deslizamientos, df_no_deslizamientos_a], ignore_index=True)

# %%
#Guardar el dataframe
df_si_no_a.to_csv(f"{ruta_bd}si_no_b.csv", index=False)

#%%
#==============================================================================
# Cargar la base de datos de no deslizamientos paquete C
#==============================================================================

# Cargar los eventos que no son deslizamientos
df_no_deslizamientos_a = pd.read_csv(f"{ruta_bd}paquete_C_caracte.csv")

df_no_deslizamientos_a.columns
#%%
#eliminar columnas que no me sirven 'Unnamed: 0', 'fecha_ho_1', 'geometry'
df_no_deslizamientos_a = df_no_deslizamientos_a.drop(columns=['Unnamed: 0', 'geometry'])

#renombrar la columna 'fecha_no' por 'fecha_hora'
df_no_deslizamientos_a = df_no_deslizamientos_a.rename(columns={'fecha_no': 'fecha_hora'})

#Reorganizar las columnas para que coincidan con el inventario de deslizamientos
#poner las columnas DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 'geo',
# #'cober', 'pre_anual', 'fecha', 'mes', 'pre_mensual' antes que 'cp1', 'cp2', 'cp3', 'cp4', 'cp5', 'cp6', 'cp7', 'cp8', 'cp9', 'cp10'
df_no_deslizamientos_a = df_no_deslizamientos_a[['fecha_hora', 'latitud', 'longitud', 'DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 'geo',
    'cober', 'pre_anual', 'fecha', 'mes', 'pre_mensual', 'cp1', 'cp3', 'cp5', 'cp7', 'cp10',
       'lp15_cp1', 'lp20_cp1', 'lp30_cp1', 'lp40_cp1', 'lp50_cp1', 'lp60_cp1',
       'lp90_cp1', 'lp15_cp3', 'lp20_cp3', 'lp30_cp3', 'lp40_cp3', 'lp50_cp3',
       'lp60_cp3', 'lp90_cp3', 'lp15_cp5', 'lp20_cp5', 'lp30_cp5', 'lp40_cp5',
       'lp50_cp5', 'lp60_cp5', 'lp90_cp5', 'lp15_cp7', 'lp20_cp7', 'lp30_cp7',
       'lp40_cp7', 'lp50_cp7', 'lp60_cp7', 'lp90_cp7', 'lp15_cp10',
       'lp20_cp10', 'lp30_cp10', 'lp40_cp10', 'lp50_cp10', 'lp60_cp10',
       'lp90_cp10']]

#agregar una columnas al final que se llame 'si_no' y que tenga valores de 0
df_no_deslizamientos_a['si_no'] = 0

# %%
df_deslizamientos = df_deslizamientos.reset_index(drop=True)
df_no_deslizamientos_a = df_no_deslizamientos_a.reset_index(drop=True)
#Unier los dos dataframes
df_si_no_a = pd.concat([df_deslizamientos, df_no_deslizamientos_a], ignore_index=True)

# %%
#Guardar el dataframe
df_si_no_a.to_csv(f"{ruta_bd}si_no_c.csv", index=False)


# %%
