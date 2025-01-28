
#%%
import pandas as pd
import matplotlib.pyplot as plt


#%%
#abir archivo csv
df = pd.read_csv('../data/db_landslides/bd_eventos_dagrd_materializados.csv')

# %%
#hacer un filtro por la columnas 'origen' solo desde los "Natural" y 'Socionatural'
df = df[(df['origen'] == 'Natural') | (df['origen'] == 'Socionatural') | (df['origen'] == 'Antrópico')]

# %%
# Convertir la columna 'fecha_ocurrencia' a formato datetime
df['fecha_ocurrencia'] = pd.to_datetime(df['fecha_ocurrencia'], errors='coerce')

# Filtrar filas válidas
df_valid = df.dropna(subset=['fecha_ocurrencia'])

# Extraer el mes de la fecha de ocurrencia
df_valid['mes'] = df_valid['fecha_ocurrencia'].dt.month

# Agrupar por mes
monthly_landslides = df_valid.groupby('mes').size()

# Crear etiquetas de los meses
meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Reordenar datos según los meses del año
monthly_landslides = monthly_landslides.reindex(range(1, 13), fill_value=0)
#%%
# Graficar
plt.figure(figsize=(10, 6))
plt.bar(meses, monthly_landslides, color='skyblue', edgecolor='black')
plt.title('Número de deslizamientos por mes', fontsize=14)
plt.xlabel('Mes', fontsize=12)
plt.ylabel('Número de deslizamientos', fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
# %%
df_geo = pd.read_csv('../data/db_landslides/inventory_GEOHAZARDS_20240824.csv')
# %%
#hacer un filtro por la columnas 'origen' solo desde los "Natural" y 'Socionatural'
#df_geo = df_geo[(df_geo['origen'] == 'Natural') | (df_geo['origen'] == 'Socionatural') | (df_geo['origen'] == 'Antrópico')]

#hacer filtro de la columna Municipio solo para Medellin
df_geo = df_geo[(df_geo['Municipio'] == 'Medellín') | (df_geo['Municipio'] == 'Medellin')]

# %%
# Convertir la columna 'fecha_ocurrencia' a formato datetime
df_geo['Fecha'] = pd.to_datetime(df_geo['Fecha'], errors='coerce')

#recortar las Fechas desde el 2012
df_geo = df_geo[(df_geo['Fecha'] > '2012-01-01')]


# Filtrar filas válidas
df_valid = df_geo.dropna(subset=['Fecha'])

# Extraer el mes de la fecha de ocurrencia
df_valid['mes'] = df_valid['Fecha'].dt.month

# Agrupar por mes
monthly_landslides = df_valid.groupby('mes').size()

# Crear etiquetas de los meses
meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Reordenar datos según los meses del año
monthly_landslides = monthly_landslides.reindex(range(1, 13), fill_value=0)
#%%
# Graficar
plt.figure(figsize=(10, 6))
plt.bar(meses, monthly_landslides, color='skyblue', edgecolor='black')
plt.title('Número de deslizamientos por mes', fontsize=14)
plt.xlabel('Mes', fontsize=12)
plt.ylabel('Número de deslizamientos', fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
# %%
#%%

# Extraer día, mes y año para realizar comparaciones más precisas
df['fecha_simple'] = df['fecha_ocurrencia'].dt.date
df = df.drop_duplicates(subset=['fecha_simple'])
df_geo['fecha_simple'] = df_geo['Fecha'].dt.date

# Buscar intersección de fechas
fechas_comunes = pd.merge(df, df_geo, left_on='fecha_simple', right_on='fecha_simple', how='inner')

# Seleccionar columnas relevantes para mostrar
fechas_comunes_seleccionadas = fechas_comunes[[
    'fecha_simple',  # Fecha en común
    #'origen',  # Origen del deslizamiento
]]
# %%
