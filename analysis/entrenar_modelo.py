import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
import pickle
import os

BASE_DIR = os.path.dirname(__file__)
ML_DIR = os.path.join(BASE_DIR, "..", "src", "ml")

df = pd.read_csv(os.path.join(BASE_DIR, "dataset_envios_ml.csv"))

FEATURES = ["peso_kg", "largo_cm", "ancho_cm", "alto_cm"]
TARGET = "prioridadManual"

X = df[FEATURES]
y = df[TARGET]

imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(X)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_imputed, y)

with open(os.path.join(ML_DIR, "modelo_prioridad.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(ML_DIR, "imputer.pkl"), "wb") as f:
    pickle.dump(imputer, f)

print("Modelo e imputer exportados correctamente.")
