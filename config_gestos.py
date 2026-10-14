"""Constantes e configurações dos gestos."""

from dataclasses import dataclass, field


PULSO = 0
PONTA_POLEGAR = 4
BASE_INDICADOR = 5
PONTA_INDICADOR = 8
BASE_MEDIO = 9
PONTA_MEDIO = 12
PONTA_ANELAR = 16
PONTA_MINDINHO = 20

TEXTO_PADRAO = "Aguardando gestos..."


@dataclass(frozen=True)
class ConfigJanela:
    """Pinça com as duas mãos (maximizar / restaurar janela)."""

    limite_pinca_ativar: float = 0.35
    limite_pinca_desativar: float = 0.48
    limite_maos_juntas: float = 0.6
    limite_maos_afastadas: float = 2.2
    cooldown: float = 1.2
    frames_confirmacao: int = 5
    alpha_suavizacao: float = 0.25


@dataclass(frozen=True)
class ConfigSwipe:
    """Motor de swipe (trocar de janela com Alt+Tab)."""

    limite_dist: float = 0.16
    tempo_max: float = 0.35
    cooldown: float = 0.8
    janela_historico: float = 0.45
    min_amostras: int = 3
    razao_vertical_max: float = 0.55


@dataclass(frozen=True)
class ConfigGestosSimples:
    """Scroll, volume e play/pause."""

    cooldown_play_pause: float = 1.5
    tempo_confirmacao_punho: float = 1.5
    threshold_scroll_y: float = 0.012
    threshold_volume_delta: float = 0.05
    passo_scroll: int = 150
    tempo_reset_sem_mao: float = 0.15


@dataclass(frozen=True)
class Config:
    janela: ConfigJanela = field(default_factory=ConfigJanela)
    swipe: ConfigSwipe = field(default_factory=ConfigSwipe)
    simples: ConfigGestosSimples = field(default_factory=ConfigGestosSimples)
