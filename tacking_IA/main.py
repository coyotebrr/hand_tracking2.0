import cv2
import mediapipe as mp
import joblib
import numpy as np

# Carrega a IA treinada
modelo = joblib.load("modelo_gestos.pkl")
mp_maos = mp.solutions.hands

captura = cv2.VideoCapture(0)

with mp_maos.Hands(min_detection_confidence=0.7) as maos:
    while True:
        _, frame = captura.read()
        frame = cv2.flip(frame, 1)
        resultado = maos.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if resultado.multi_hand_landmarks:
            pontos = resultado.multi_hand_landmarks[0]
            # Mesma lógica de normalização do coletor
            features = [p.x - pontos.landmark[0].x for p in pontos.landmark] + \
                       [p.y - pontos.landmark[0].y for p in pontos.landmark]
            
            # IA decide o gesto
            predicao = modelo.predict([features])[0]
            
            # Executar ações baseadas na IA
            if predicao == "PINCA":
                # Aqui você chama sua função de maximizar/restaurar
                pass 
            
            cv2.putText(frame, predicao, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.imshow("IA de Gestos", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

captura.release()
cv2.destroyAllWindows()