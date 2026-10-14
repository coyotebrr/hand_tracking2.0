"""Ações de teclado e mídia executadas no computador."""

import time

import pyautogui


pyautogui.FAILSAFE = False


class AcoesSistema:
    """Encapsula o PyAutoGUI para facilitar testes e substituições."""

    def maximizar_janela(self):
        pyautogui.hotkey("win", "up")

    def restaurar_janela(self):
        pyautogui.hotkey("win", "down")

    def proxima_janela(self):
        pyautogui.keyDown("alt")
        try:
            pyautogui.press("tab")
            time.sleep(0.1)
        finally:
            pyautogui.keyUp("alt")

    def janela_anterior(self):
        pyautogui.keyDown("alt")
        try:
            pyautogui.keyDown("shift")
            try:
                pyautogui.press("tab")
                time.sleep(0.1)
            finally:
                pyautogui.keyUp("shift")
        finally:
            pyautogui.keyUp("alt")

    def rolar(self, quantidade):
        pyautogui.scroll(quantidade)

    def aumentar_volume(self):
        pyautogui.press("volumeup")

    def diminuir_volume(self):
        pyautogui.press("volumedown")

    def play_pause(self):
        pyautogui.press("playpause")
