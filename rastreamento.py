"""Câmera, rastreamento de mãos com MediaPipe e desenho da interface."""

from dataclasses import dataclass

import cv2
import mediapipe as mp

from config_gestos import PONTA_INDICADOR


@dataclass
class MaoDetectada:
    pontos: object
    lado: str


class Camera:
    def __init__(self, indice=0):
        self._captura = cv2.VideoCapture(indice)

    def esta_aberta(self):
        return self._captura.isOpened()

    def ler_espelhado(self):
        """Retorna o frame espelhado ou None se a leitura falhar."""
        ok, frame = self._captura.read()
        return cv2.flip(frame, 1) if ok else None

    def liberar(self):
        self._captura.release()


class RastreadorMaos:
    """Envolve MediaPipe Hands e fecha os recursos com o gerenciador de contexto."""

    def __init__(self, max_maos=2, confianca_deteccao=0.5, confianca_rastreio=0.5):
        self._maos = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_maos,
            min_detection_confidence=confianca_deteccao,
            min_tracking_confidence=confianca_rastreio,
        )

    def detectar(self, frame_bgr):
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        resultado = self._maos.process(rgb)
        if not getattr(resultado, "multi_hand_landmarks", None):
            return []

        handedness = getattr(resultado, "multi_handedness", []) or []
        maos = []
        for indice, pontos in enumerate(resultado.multi_hand_landmarks):
            lado = "Unknown"
            if indice < len(handedness) and handedness[indice].classification:
                lado = handedness[indice].classification[0].label
            maos.append(MaoDetectada(pontos=pontos, lado=lado))
        return maos

    def fechar(self):
        self._maos.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()


class Renderizador:
    NOME_JANELA = "Rastreamento de Mao"
    COR_VERDE = (0, 255, 0)
    COR_TEXTO = (0, 165, 255)

    def __init__(self):
        self._desenho = mp.solutions.drawing_utils
        self._estilos = mp.solutions.drawing_styles
        self._conexoes = mp.solutions.hands.HAND_CONNECTIONS

    def criar_janela(self):
        cv2.namedWindow(self.NOME_JANELA, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.NOME_JANELA, cv2.WND_PROP_TOPMOST, 1)

    def desenhar_mao(self, frame, pontos_mao):
        altura, largura, _ = frame.shape
        self._desenho.draw_landmarks(
            frame,
            pontos_mao,
            self._conexoes,
            self._estilos.get_default_hand_landmarks_style(),
            self._estilos.get_default_hand_connections_style(),
        )
        ponta = pontos_mao.landmark[PONTA_INDICADOR]
        cv2.circle(
            frame,
            (int(ponta.x * largura), int(ponta.y * altura)),
            10,
            self.COR_VERDE,
            -1,
        )

    def desenhar_linha_pinca(self, frame, linha):
        if linha is None:
            return
        altura, largura, _ = frame.shape
        (xa, ya), (xb, yb) = linha
        cv2.line(
            frame,
            (int(xa * largura), int(ya * altura)),
            (int(xb * largura), int(yb * altura)),
            self.COR_VERDE,
            2,
        )

    def desenhar_feedback(self, frame, texto):
        cv2.putText(
            frame, texto, (20, 90), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, self.COR_TEXTO, 2,
        )

    def mostrar(self, frame):
        cv2.imshow(self.NOME_JANELA, frame)

    def fechar(self):
        cv2.destroyAllWindows()
