# 01_entrenar.py — clasificador de flores Iris (el "hola mundo" del ML)
# https://labex.io/es/tutorials/iris-flower-classification-with-scikit-learn-49166
#
#     python 01_entrenar.py
#
# Lo importante no es el modelo, es el PATRÓN: se entrena una vez, FUERA de la API,
# y el resultado se guarda en un fichero. Con una red neuronal enorme es idéntico.
from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

# Iris viene incluido en scikit-learn: 150 flores, 4 medidas, 3 especies.
#   X = las medidas (lo que se observa)   ->  150 filas x 4 columnas
#   y = la especie  (lo que se predice)   ->  0, 1 o 2
X, y = load_iris(return_X_y=True)

# max_iter=200: con el 100 por defecto no converge y salta un ConvergenceWarning.
modelo = LogisticRegression(max_iter=200).fit(X, y)

# NOTA HONESTA: entrenamos con los 150 ejemplos y no medimos nada. En un proyecto
# real se reserva una parte (train_test_split) para comprobar el acierto con flores
# no vistas; medir sobre los datos de entrenamiento siempre infla la nota.
# Se omite a propósito: este capítulo enseña a SERVIR modelos, no a construirlos.

# Serializar = convertir el modelo entrenado en bytes que se pueden guardar.
# Lo dejamos junto al script, para que dé igual desde dónde lo lancemos.
destino = Path(__file__).with_name("modelo_iris.joblib")
joblib.dump(modelo, destino)

print("Modelo guardado")
print(f"Entrenado con {X.shape[0]} flores y {X.shape[1]} medidas por flor")
print(f"Especies que distingue: {len(set(y))}")
