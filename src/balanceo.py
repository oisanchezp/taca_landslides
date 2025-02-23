
#%%
import pandas as pd

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import TomekLinks
from collections import Counter

#%%

ruta_bd = '../data/db_landslides/'

# Cargar el inventario con y sin deslizamientos
df = pd.read_csv(f"{ruta_bd}si_no_c.csv")

print(df.shape)
df.head()

# #escoger 1800 eventos alazar de 'si_no' = 0
# #pero sean 'si_no' = 0
# df = df[df['si_no'] == 0]
# #escoger 1800 eventos alazar
# #pero dejar los 'si_no' = 1
# df = df.sample(n=1800, random_state=42)
# df.shape

# %%
#==============================================================================
#Separar variables predictoras (X) y variable objetivo (y)
#==============================================================================

# Definir X y y
X = df.drop(columns=['si_no', 'fecha_hora', 'fecha', 'mes'])
y = df['si_no']

# Ver distribución de la variable objetivo
print('Distribución de la variable objetivo (antes de SMOTE):', Counter(y))

#mirar cuales variables tienen valores nan
nan_values = X.isna().sum()
nan_values = nan_values[nan_values > 0]
nan_values
#%%
#eliminar las filas con valores nan
X = X.dropna()
y = y[X.index]
#%%
import matplotlib.pyplot as plt

df_balanced = X
df_balanced['si_no'] = y


variables = [
    'DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 
    'geo', 'cober', 'pre_anual', 'pre_mensual', 'cp1', 'lp90_cp1'
]

numeric_vars = ['DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 
                'pre_anual', 'pre_mensual', 'cp1', 'lp90_cp1', 'cp3', 'cp5', 'cp7', 'cp10', 
                'lp15_cp1', 'lp20_cp1', 'lp30_cp1', 'lp40_cp1', 'lp50_cp1', 'lp60_cp1', 'lp90_cp1',]

cat_vars = ['geo', 'cober']


# %%
import matplotlib.pyplot as plt
import seaborn as sns

for var in numeric_vars:
    plt.figure(figsize=(7, 5))
    sns.histplot(data=df_balanced, x=var, hue='si_no', kde=False,  # kde=True si quieres curva de densidad
                 stat='count', multiple='stack', alpha=0.7)
    
    plt.title(f"Histograma de {var} con si_no (0 vs 1)")
    plt.xlabel(var)
    plt.ylabel("Frecuencia")
    plt.legend(title='si_no', labels=['1 (con deslizamiento)','0 (sin deslizamiento)'])
    plt.show()
#%%
#================================================================
#Aplicar SMOTE (Over-sampling de la clase minoritaria)
#================================================================
# Crear instancia de SMOTE. En caso necesario, puedes ajustar parámetros como sampling_strategy.
# sampling_strategy = 0.5, por ejemplo, crearía la clase minoritaria hasta tener la mitad
# del número de la clase mayoritaria. Por defecto, sampling_strategy='auto' la iguala.
sm = SMOTE(random_state=42, sampling_strategy=0.8)

# Ajustar y hacer el resample
X_smote, y_smote = sm.fit_resample(X, y)

print('Distribución de la variable objetivo (después de SMOTE):', Counter(y_smote))
#cuantos vecinos k esta usando SMOTE
sm.k_neighbors


# %%
#================================================================
#Aplicar Tomek Links (Under-sampling de la clase mayoritaria)
#================================================================
# Crear la instancia de TomekLinks
tl = TomekLinks(sampling_strategy='all')

# Ajustar y hacer el resample
X_final, y_final = tl.fit_resample(X_smote, y_smote)

print('Distribución de la variable objetivo (después de Tomek Links):', Counter(y_final))

#%%

print("Antes de SMOTE (original):", Counter(y))
print("Después de SMOTE:", Counter(y_smote))
print("Después de SMOTE + Tomek Links:", Counter(y_final))

# %%
#==============================================================================
# Hacer graficos exploratorios de las variables
#==============================================================================
import matplotlib.pyplot as plt

df_balanced = X_final.copy()
df_balanced['si_no'] = y_final


variables = [
    'DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 
    'geo', 'cober', 'pre_anual', 'pre_mensual', 'cp1', 'lp90_cp1'
]

numeric_vars = ['DEM_mean', 'slope_mean', 'aspect_mean', 'nhd_mean', 
                'pre_anual', 'pre_mensual', 'cp1', 'lp90_cp1', 'cp3', 'cp5', 'cp7', 'cp10', 
                'lp15_cp1', 'lp20_cp1', 'lp30_cp1', 'lp40_cp1', 'lp50_cp1', 'lp60_cp1', 'lp90_cp1',]

cat_vars = ['geo', 'cober']


# %%
import matplotlib.pyplot as plt
import seaborn as sns

for var in numeric_vars:
    plt.figure(figsize=(7, 5))
    sns.histplot(data=df_balanced, x=var, hue='si_no', kde=False,  # kde=True si quieres curva de densidad
                 stat='count', multiple='stack', alpha=0.7)
    
    plt.title(f"Histograma de {var} con si_no (0 vs 1)")
    plt.xlabel(var)
    plt.ylabel("Frecuencia")
    plt.legend(title='si_no', labels=['1 (con deslizamiento)', '0 (sin deslizamiento)',])
    plt.show()
# %%
# for var in cat_vars:
#     plt.figure(figsize=(7, 5))
#     sns.countplot(data=df_balanced, x=var, hue='si_no')
#     plt.title(f"Conteo de {var} segregado por si_no")
#     plt.xlabel(var)
#     plt.ylabel("Frecuencia")
#     plt.legend(title='si_no', labels=['0 (sin deslizamiento)', '1 (con deslizamiento)'])
#     plt.xticks(rotation=45)  # en caso de que las categorías sean muchas y se vea mejor en ángulo
#     plt.show()
# %%
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Dividir en train y test
X_train, X_test, y_train, y_test = train_test_split(X_final, y_final, 
                                                    test_size=0.2, 
                                                    random_state=42)

# Entrenar un modelo sencillo (ej. RandomForest)
rf = RandomForestClassifier(random_state=42)
rf.fit(X_train, y_train)

# Predicciones
y_pred = rf.predict(X_test)

# Métricas de evaluación
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))
# %%
