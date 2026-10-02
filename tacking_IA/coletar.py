import os
# O nível 2 esconde mensagens de aviso (WARNINGS), mostrando apenas erros (ERRORS)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

import cv2
import mediapipe as mp

import cv2
import mediapipe as mp
import pandas as pd
import os

mp_maos = mp.solutions.hands
captura = cv2.VideoCapture(0)

# Estrutura do arquivo CSV
colunas = [f"x{i}" for i in range(21)] + [f"y{i}" for i in range(21)] + ["label"]
dados = []

print("Pressione 'p' para gravar PINCA, 'o' para OK, 'n' para NENHUM, 'q' para sair.")

with mp_maos.Hands(min_detection_confidence=0.7) as maos:
    while True:
        _, frame = captura.read()
        frame = cv2.flip(frame, 1)
        resultado = maos.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        label = "DESCONHECIDO"
        if cv2.waitKey(1) & 0xFF == ord('p'): label = "PINCA"
        elif cv2.waitKey(1) & 0xFF == ord('o'): label = "OK"
        elif cv2.waitKey(1) & 0xFF == ord('n'): label = "NENHUM"
        elif cv2.waitKey(1) & 0xFF == ord('q'): break

        if resultado.multi_hand_landmarks:
            pontos = resultado.multi_hand_landmarks[0]
            # Normalização (usando o pulso como referência 0,0)
            linha = [p.x - pontos.landmark[0].x for p in pontos.landmark] + \
                    [p.y - pontos.landmark[0].y for p in pontos.landmark]
            
            if label != "DESCONHECIDO":
                dados.append(linha + [label])
                print(f"Gravado: {label}")

        cv2.imshow("Coletor", frame)

captura.release()
cv2.destroyAllWindows()
pd.DataFrame(dados, columns=colunas).to_csv("dados_gestos.csv", index=False)
print("Dados salvos em dados_gestos.csv")