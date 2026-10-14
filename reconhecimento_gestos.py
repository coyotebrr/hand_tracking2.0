"""Reconhecimento das poses da mão a partir dos landmarks do MediaPipe."""

from dataclasses import dataclass
from enum import Enum, auto

from config_gestos import (
    BASE_INDICADOR,
    PONTA_ANELAR,
    PONTA_INDICADOR,
    PONTA_MEDIO,
    PONTA_MINDINHO,
    PONTA_POLEGAR,
    PULSO,
)
from geometria import distancia_normalizada


class Gesto(Enum):
    MAO_ABERTA = auto()
    V_SWIPE = auto()
    L_VOLUME = auto()
    INDICADOR_SCROLL = auto()
    PUNHO = auto()
    DESCONHECIDO = auto()


@dataclass(frozen=True)
class LimiarDedo:
    """Zona morta entre os estados esticado e dobrado."""

    esticado: float
    dobrado: float


class ReconhecedorGestos:
    LIMIAR_INDICADOR = LimiarDedo(esticado=1.55, dobrado=1.25)
    LIMIAR_MEDIO = LimiarDedo(esticado=1.60, dobrado=1.25)
    LIMIAR_ANELAR = LimiarDedo(esticado=1.50, dobrado=1.25)
    LIMIAR_MINDINHO = LimiarDedo(esticado=1.40, dobrado=1.15)
    LIMIAR_POLEGAR = LimiarDedo(esticado=1.30, dobrado=1.10)

    def reconhecer(self, pontos_mao):
        indicador_esticado, indicador_dobrado = self._estado_dedo(
            pontos_mao, PONTA_INDICADOR, self.LIMIAR_INDICADOR)
        medio_esticado, medio_dobrado = self._estado_dedo(
            pontos_mao, PONTA_MEDIO, self.LIMIAR_MEDIO)
        anelar_esticado, anelar_dobrado = self._estado_dedo(
            pontos_mao, PONTA_ANELAR, self.LIMIAR_ANELAR)
        mindinho_esticado, mindinho_dobrado = self._estado_dedo(
            pontos_mao, PONTA_MINDINHO, self.LIMIAR_MINDINHO)
        polegar_aberto, polegar_fechado = self._estado_polegar(pontos_mao)

        if indicador_esticado and medio_esticado and anelar_esticado and mindinho_esticado:
            return Gesto.MAO_ABERTA

        if (indicador_esticado and medio_esticado and anelar_dobrado
                and mindinho_dobrado and polegar_fechado):
            return Gesto.V_SWIPE

        if (indicador_esticado and polegar_aberto and medio_dobrado
                and anelar_dobrado and mindinho_dobrado):
            return Gesto.L_VOLUME

        if (indicador_esticado and medio_dobrado and anelar_dobrado
                and mindinho_dobrado and polegar_fechado):
            return Gesto.INDICADOR_SCROLL

        if (indicador_dobrado and medio_dobrado and anelar_dobrado
                and mindinho_dobrado and polegar_fechado):
            return Gesto.PUNHO

        return Gesto.DESCONHECIDO

    @staticmethod
    def _estado_dedo(pontos_mao, ponta, limiar):
        """Retorna (esticado, dobrado) usando a distância da ponta ao pulso."""
        try:
            distancia = distancia_normalizada(pontos_mao, ponta, PULSO)
        except (TypeError, IndexError, AttributeError):
            return False, False
        return distancia > limiar.esticado, distancia < limiar.dobrado

    def _estado_polegar(self, pontos_mao):
        """Verifica se o polegar está aberto ou fechado."""
        try:
            distancia = distancia_normalizada(
                pontos_mao, PONTA_POLEGAR, BASE_INDICADOR)
        except (TypeError, IndexError, AttributeError):
            return False, False
        return (
            distancia > self.LIMIAR_POLEGAR.esticado,
            distancia < self.LIMIAR_POLEGAR.dobrado,
        )
