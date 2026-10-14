"""Controles acionados pelos gestos reconhecidos."""

import math
from enum import Enum, auto

from config_gestos import BASE_MEDIO, PONTA_INDICADOR
from geometria import (
    distancia_pinca_normalizada,
    ponto_pinca,
    tamanho_mao,
)
from reconhecimento_gestos import Gesto, ReconhecedorGestos


class Direcao(Enum):
    DIREITA = auto()
    ESQUERDA = auto()


class ControleSwipe:
    """V + deslizar para os lados -> Alt+Tab / Alt+Shift+Tab."""

    def __init__(self, config, acoes):
        self.config = config
        self.acoes = acoes
        self.historico = []
        self.ultima_acao = 0.0

    def resetar(self):
        self.historico.clear()

    def processar(self, pontos_mao, agora):
        centro = pontos_mao.landmark[BASE_MEDIO]
        self.historico.append((agora, centro.x, centro.y))
        self.historico = [
            amostra for amostra in self.historico
            if agora - amostra[0] <= self.config.janela_historico
        ]

        pode_detectar = (
            len(self.historico) >= self.config.min_amostras
            and (agora - self.ultima_acao) >= self.config.cooldown
        )
        direcao = self._detectar_direcao() if pode_detectar else None

        if direcao is Direcao.DIREITA:
            print("➡️ Swipe Direita -> Avançar Janela")
            self.acoes.proxima_janela()
            self._registrar_acao(agora)
        elif direcao is Direcao.ESQUERDA:
            print("⬅️ Swipe Esquerda -> Voltar Janela")
            self.acoes.janela_anterior()
            self._registrar_acao(agora)

        return "Swipe Ativo! Deslize lateralmente"

    def _detectar_direcao(self):
        """Procura deslocamento horizontal rápido o bastante."""
        cfg = self.config
        for i in range(len(self.historico)):
            for j in range(i + 1, len(self.historico)):
                t_ini, x_ini, y_ini = self.historico[i]
                t_fim, x_fim, y_fim = self.historico[j]
                if t_fim - t_ini > cfg.tempo_max:
                    continue
                dx = x_fim - x_ini
                dy = y_fim - y_ini
                if (abs(dx) >= cfg.limite_dist
                        and abs(dy) < abs(dx) * cfg.razao_vertical_max):
                    return Direcao.DIREITA if dx > 0 else Direcao.ESQUERDA
        return None

    def _registrar_acao(self, agora):
        self.ultima_acao = agora
        self.historico.clear()


class ControleScroll:
    """Indicador em pé subindo/descendo -> rola a página."""

    def __init__(self, config, acoes):
        self.config = config
        self.acoes = acoes
        self.ultimo_y = None

    def resetar(self):
        self.ultimo_y = None

    def processar(self, pontos_mao):
        y_atual = pontos_mao.landmark[PONTA_INDICADOR].y
        feedback = "Modo Scroll (mova o indicador)"

        if self.ultimo_y is not None:
            dy = y_atual - self.ultimo_y
            if dy < -self.config.threshold_scroll_y:
                self.acoes.rolar(self.config.passo_scroll)
                feedback = "📜 Rolando para cima"
            elif dy > self.config.threshold_scroll_y:
                self.acoes.rolar(-self.config.passo_scroll)
                feedback = "📜 Rolando para baixo"

        self.ultimo_y = y_atual
        return feedback


class ControleVolume:
    """Sinal de L: abrir/fechar polegar e indicador ajusta o volume."""

    def __init__(self, config, acoes):
        self.config = config
        self.acoes = acoes
        self.ultima_dist = None

    def resetar(self):
        self.ultima_dist = None

    def processar(self, pontos_mao):
        distancia = distancia_pinca_normalizada(pontos_mao)
        feedback = f"Modo Volume (Abertura: {distancia:.1f})"

        if self.ultima_dist is not None:
            delta = distancia - self.ultima_dist
            if delta > self.config.threshold_volume_delta:
                self.acoes.aumentar_volume()
                feedback = "🔊 Aumentando Volume"
            elif delta < -self.config.threshold_volume_delta:
                self.acoes.diminuir_volume()
                feedback = "🔉 Diminuindo Volume"

        self.ultima_dist = distancia
        return feedback


class ControlePlayPause:
    """Punho segurado pelo tempo configurado aciona play/pause."""

    def __init__(self, config, acoes):
        self.config = config
        self.acoes = acoes
        self.tempo_inicio = None
        self.ultimo_acionamento = 0.0

    def resetar(self):
        self.tempo_inicio = None

    def processar(self, agora):
        if self.tempo_inicio is None:
            self.tempo_inicio = agora

        decorrido = agora - self.tempo_inicio
        confirmacao = self.config.tempo_confirmacao_punho

        if decorrido >= confirmacao:
            if (agora - self.ultimo_acionamento) >= self.config.cooldown_play_pause:
                self.acoes.play_pause()
                print("✊ Play/Pause Executado (Confirmado!)")
                self.ultimo_acionamento = agora
            return "✊ Punho Confirmado! (Ação Executada)"

        progresso = (decorrido / confirmacao) * 100
        return f"✊ Segure para Pausar... {progresso:.0f}%"


class EstadoJanela(Enum):
    NEUTRO = auto()
    AFASTADO = auto()
    JUNTO = auto()


class ControleJanelaDuasMaos:
    """Duas mãos pinçando: afastar maximiza, aproximar restaura."""

    LADOS = ("Left", "Right")

    def __init__(self, config, acoes):
        self.config = config
        self.acoes = acoes
        self.pincando = {lado: False for lado in self.LADOS}
        self.estado = EstadoJanela.NEUTRO
        self.ultima_acao = 0.0
        self.frames_afastado = 0
        self.frames_junto = 0
        self.dist_suave = None

    def atualizar_pinca_individual(self, pontos_mao, lado):
        if lado not in self.LADOS:
            return

        distancia = distancia_pinca_normalizada(pontos_mao)
        limite = (
            self.config.limite_pinca_desativar
            if self.pincando[lado]
            else self.config.limite_pinca_ativar
        )
        self.pincando[lado] = distancia <= limite

    def limpar_lados_ausentes(self, lados_detectados):
        for lado in self.LADOS:
            if lado not in lados_detectados:
                self.pincando[lado] = False

    def processar(self, maos, agora):
        """Retorna o feedback e a linha que liga os pontos de pinça, se houver."""
        if not all(self.pincando.values()):
            self._resetar_medicao()
            return "Pinçe os dedos nas duas mãos para gerenciar janelas", None

        pontos_a, pontos_b = maos[0].pontos, maos[1].pontos
        p_a, p_b = ponto_pinca(pontos_a), ponto_pinca(pontos_b)
        escala_media = (tamanho_mao(pontos_a) + tamanho_mao(pontos_b)) / 2
        distancia = math.dist(p_a, p_b) / escala_media
        self._suavizar(distancia)

        cfg = self.config
        if self.dist_suave >= cfg.limite_maos_afastadas:
            self.frames_afastado += 1
            self.frames_junto = 0
            self._tentar_acionar(
                EstadoJanela.AFASTADO,
                self.frames_afastado,
                self.acoes.maximizar_janela,
                agora,
            )
            feedback = "🖐️↔️🖐️ Expandindo Janela"
        elif self.dist_suave <= cfg.limite_maos_juntas:
            self.frames_junto += 1
            self.frames_afastado = 0
            self._tentar_acionar(
                EstadoJanela.JUNTO,
                self.frames_junto,
                self.acoes.restaurar_janela,
                agora,
            )
            feedback = "🤏🤏 Encolhendo Janela"
        else:
            self.estado = EstadoJanela.NEUTRO
            self.frames_afastado = 0
            self.frames_junto = 0
            feedback = f"Ajuste Fino de Janela (dist={self.dist_suave:.2f})"

        return feedback, (p_a, p_b)

    def _suavizar(self, distancia):
        """Média móvel exponencial para reduzir tremor na medição."""
        alpha = self.config.alpha_suavizacao
        if self.dist_suave is None:
            self.dist_suave = distancia
        else:
            self.dist_suave = alpha * distancia + (1 - alpha) * self.dist_suave

    def _tentar_acionar(self, novo_estado, frames, acao, agora):
        pode_agir = (agora - self.ultima_acao) >= self.config.cooldown
        if (self.estado != novo_estado and pode_agir
                and frames >= self.config.frames_confirmacao):
            acao()
            self.estado = novo_estado
            self.ultima_acao = agora

    def _resetar_medicao(self):
        self.dist_suave = None
        self.estado = EstadoJanela.NEUTRO
        self.frames_afastado = 0
        self.frames_junto = 0


class ControladorUmaMao:
    """Reconhece o gesto e delega para o controle correspondente."""

    def __init__(self, config, acoes):
        self.config = config.simples
        self.reconhecedor = ReconhecedorGestos()
        self.swipe = ControleSwipe(config.swipe, acoes)
        self.scroll = ControleScroll(config.simples, acoes)
        self.volume = ControleVolume(config.simples, acoes)
        self.play_pause = ControlePlayPause(config.simples, acoes)
        self.ultima_vez_com_mao = 0.0

    def processar(self, pontos_mao, agora):
        self.ultima_vez_com_mao = agora
        gesto = self.reconhecedor.reconhecer(pontos_mao)

        if gesto is Gesto.V_SWIPE:
            self.play_pause.resetar()
            self.scroll.resetar()
            self.volume.resetar()
            return self.swipe.processar(pontos_mao, agora)

        if gesto is Gesto.INDICADOR_SCROLL:
            self.play_pause.resetar()
            self.swipe.resetar()
            self.volume.resetar()
            return self.scroll.processar(pontos_mao)

        if gesto is Gesto.L_VOLUME:
            self.play_pause.resetar()
            self.swipe.resetar()
            self.scroll.resetar()
            return self.volume.processar(pontos_mao)

        if gesto is Gesto.PUNHO:
            self.swipe.resetar()
            self.scroll.resetar()
            self.volume.resetar()
            return self.play_pause.processar(agora)

        self.play_pause.resetar()
        self.scroll.resetar()
        self.volume.resetar()
        return "Aguardando estabilização do gesto..."

    def verificar_perda_de_mao(self, agora):
        """Sem exatamente uma mão por um tempo, zera os temporizadores."""
        if agora - self.ultima_vez_com_mao > self.config.tempo_reset_sem_mao:
            self.resetar_tudo()

    def resetar_tudo(self):
        self.play_pause.resetar()
        self.swipe.resetar()
        self.scroll.resetar()
        self.volume.resetar()
