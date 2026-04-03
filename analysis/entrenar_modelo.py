import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
import pickle
import os

BASE_DIR = os.path.dirname(__file__)

df = pd.read_csv(os.path.join(BASE_DIR, "dataset_envios_ml.csv"))


def clasificar_prioridad(row):
    peso = row["peso_kg"]
    volumen = row["largo_cm"] * row["ancho_cm"] * row["alto_cm"]
    if pd.isna(volumen):
        volumen = 0
    if peso > 15 or volumen > 100_000:
        return "ALTA"
    if peso > 5 or volumen > 30_000:
        return "MEDIA"
    return "BAJA"


df["prioridad"] = df.apply(clasificar_prioridad, axis=1)

FEATURES = ["peso_kg", "largo_cm", "ancho_cm", "alto_cm"]
TARGET = "prioridad"

X = df[FEATURES]
y = df[TARGET]

imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(X)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_imputed, y)

with open(os.path.join(BASE_DIR, "modelo_prioridad.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(BASE_DIR, "imputer.pkl"), "wb") as f:
    pickle.dump(imputer, f)

print("Modelo e imputer exportados correctamente.")
print("Distribucion de clases:")
print(df[TARGET].value_counts())
