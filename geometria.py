"""Cálculos geométricos usados no rastreamento e reconhecimento."""

import math

from config_gestos import BASE_MEDIO, PONTA_INDICADOR, PONTA_POLEGAR, PULSO


def _marco_mao(pontos_mao, indice):
    """Retorna o landmark solicitado ou None se ele não estiver disponível."""
    if pontos_mao is None or not hasattr(pontos_mao, "landmark"):
        return None

    marcos = getattr(pontos_mao, "landmark", [])
    if indice < 0 or indice >= len(marcos):
        return None
    return marcos[indice]


def distancia_2d(ponto_a, ponto_b):
    """Distância euclidiana (x, y) entre dois landmarks."""
    if ponto_a is None or ponto_b is None:
        return 0.0
    return math.dist((ponto_a.x, ponto_a.y), (ponto_b.x, ponto_b.y))


def tamanho_mao(pontos_mao):
    """Distância pulso -> base do dedo médio, usada como escala da mão."""
    pulso = _marco_mao(pontos_mao, PULSO)
    base_medio = _marco_mao(pontos_mao, BASE_MEDIO)
    distancia = distancia_2d(pulso, base_medio)
    return distancia if distancia > 0 else 1e-6


def distancia_normalizada(pontos_mao, indice_a, indice_b):
    """Distância entre dois pontos da mão, dividida pelo tamanho da mão."""
    marco_a = _marco_mao(pontos_mao, indice_a)
    marco_b = _marco_mao(pontos_mao, indice_b)
    if marco_a is None or marco_b is None:
        return 0.0
    return distancia_2d(marco_a, marco_b) / tamanho_mao(pontos_mao)


def distancia_pinca_normalizada(pontos_mao):
    """Distância polegar <-> indicador normalizada."""
    return distancia_normalizada(pontos_mao, PONTA_POLEGAR, PONTA_INDICADOR)


def ponto_pinca(pontos_mao):
    """Ponto médio entre a ponta do polegar e a do indicador."""
    polegar = _marco_mao(pontos_mao, PONTA_POLEGAR)
    indicador = _marco_mao(pontos_mao, PONTA_INDICADOR)
    if polegar is None or indicador is None:
        return (0.0, 0.0)
    return ((polegar.x + indicador.x) / 2, (polegar.y + indicador.y) / 2)
