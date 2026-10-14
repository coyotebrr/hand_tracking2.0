"""Ponto de entrada da aplicação de rastreamento e controle por gestos."""

import time

import cv2

from acoes_sistema import AcoesSistema
from config_gestos import Config, TEXTO_PADRAO
from controles_gestos import ControladorUmaMao, ControleJanelaDuasMaos
from rastreamento import Camera, RastreadorMaos, Renderizador


class AplicacaoGestos:
    def __init__(self, config=None):
        self.config = config or Config()
        acoes = AcoesSistema()

        self.camera = Camera()
        self.renderizador = Renderizador()
        self.uma_mao = ControladorUmaMao(self.config, acoes)
        self.duas_maos = ControleJanelaDuasMaos(self.config.janela, acoes)

    def executar(self):
        if not self.camera.esta_aberta():
            print("Erro: não foi possível acessar a câmera.")
            return

        try:
            with RastreadorMaos() as rastreador:
                self.renderizador.criar_janela()
                self._loop(rastreador)
        finally:
            self.camera.liberar()
            self.renderizador.fechar()

    def _loop(self, rastreador):
        while True:
            frame = self.camera.ler_espelhado()
            if frame is None:
                print("Erro ao capturar frame.")
                break

            maos = rastreador.detectar(frame)
            for mao in maos:
                self.renderizador.desenhar_mao(frame, mao.pontos)

            feedback = self._processar_maos(frame, maos, time.time())
            self.renderizador.desenhar_feedback(frame, feedback)
            self.renderizador.mostrar(frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    def _processar_maos(self, frame, maos, agora):
        """Processa os gestos conforme a quantidade de mãos detectadas."""
        for mao in maos:
            self.duas_maos.atualizar_pinca_individual(mao.pontos, mao.lado)
        self.duas_maos.limpar_lados_ausentes([mao.lado for mao in maos])

        if len(maos) == 1:
            return self.uma_mao.processar(maos[0].pontos, agora)

        self.uma_mao.verificar_perda_de_mao(agora)
        if len(maos) == 2:
            self.uma_mao.play_pause.resetar()
            feedback, linha = self.duas_maos.processar(maos, agora)
            self.renderizador.desenhar_linha_pinca(frame, linha)
            return feedback

        return TEXTO_PADRAO


def main():
    AplicacaoGestos().executar()


if __name__ == "__main__":
    main()
