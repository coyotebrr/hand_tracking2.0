import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Carregar dados
df = pd.read_csv("dados_gestos.csv")
X = df.drop("label", axis=1) # As coordenadas
y = df["label"]              # O nome do gesto

# 2. Treinar o modelo
modelo = RandomForestClassifier(n_estimators=100)
modelo.fit(X, y)

# 3. Salvar o "cérebro"
joblib.dump(modelo, "modelo_gestos.pkl")
print("Modelo treinado e salvo como modelo_gestos.pkl!")