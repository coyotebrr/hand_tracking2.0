"""
Rastreamento de Mão com MediaPipe Hands - Controle com Dupla Checagem (V3)
-----------------------------------------------------------------------------------------
- Duas Mãos (Pinça): Aproximar/Afastar maximiza ou restaura a janela ativa.
- Uma Mão (Swipe): Deslizar a mão na pose de "V" muda de janela (Alt+Tab).
- Uma Mão (Indicador): Mover o dedo em pé para cima/baixo rola a página (Scroll).
- Uma Mão (L / Arma): Afastar ou aproximar o polegar do indicador ajusta o volume.
- Uma Mão (Punho): Fechar a mão e SEGURAR por 0.5s pausa ou dá play em mídias (Dupla Checagem).

Requisitos:
    pip install opencv-python mediapipe pyautogui
"""

import cv2
import mediapipe as mp
import time
import math
import pyautogui

# Desativa a falha segura do PyAutoGUI
pyautogui.FAILSAFE = False

# Inicialização do MediaPipe
mp_maos = mp.solutions.hands
mp_desenho = mp.solutions.drawing_utils
mp_estilos = mp.solutions.drawing_styles

# Constantes para os pontos das pontas dos dedos
PONTA_POLEGAR = 4
PONTA_INDICADOR = 8
PONTA_MEDIO = 12
PONTA_ANELAR = 16
PONTA_MINDINHO = 20

# Pontos usados como referência de tamanho/escala da mão
PULSO = 0
BASE_MEDIO = 9

# --- Parâmetros de Histerese (Pinça Dupla - Janelas) ---
LIMITE_PINCA_ATIVAR = 0.35     
LIMITE_PINCA_DESATIVAR = 0.48  
LIMITE_MAOS_JUNTAS = 0.6       
LIMITE_MAOS_AFASTADAS = 2.2    
COOLDOWN_JANELA = 1.2          
FRAMES_CONFIRMACAO = 5         
ALPHA_SUAVIZACAO = 0.25        

# --- Parâmetros para o Motor de Swipe ---
LIMITE_SWIPE_DIST = 0.16       
TEMPO_SWIPE_MAX = 0.35         
COOLDOWN_SWIPE = 0.8           

# --- Parâmetros de Ajustes dos Novos Gestos ---
COOLDOWN_PLAY_PAUSE = 1.5      
TEMPO_CONFIRMACAO_PUNHO = 1.5  # Tempo (em segundos) que você precisa manter o punho fechado para confirmar a ação
THRESHOLD_SCROLL_Y = 0.012     
THRESHOLD_VOLUME_DELTA = 0.05  


def tamanho_mao(pontos_mao):
    p_pulso = pontos_mao.landmark[PULSO]
    p_base_medio = pontos_mao.landmark[BASE_MEDIO]
    d = math.dist((p_pulso.x, p_pulso.y), (p_base_medio.x, p_base_medio.y))
    return d if d > 0 else 1e-6


def distancia_pinca_normalizada(pontos_mao):
    p_polegar = pontos_mao.landmark[PONTA_POLEGAR]
    p_indicador = pontos_mao.landmark[PONTA_INDICADOR]
    dist_dedos = math.dist(
        (p_polegar.x, p_polegar.y), (p_indicador.x, p_indicador.y)
    )
    return dist_dedos / tamanho_mao(pontos_mao)


def ponto_pinca(pontos_mao):
    p_polegar = pontos_mao.landmark[PONTA_POLEGAR]
    p_indicador = pontos_mao.landmark[PONTA_INDICADOR]
    return (
        (p_polegar.x + p_indicador.x) / 2,
        (p_polegar.y + p_indicador.y) / 2,
    )


# --- Reconhecedor de Gestos com Zona Morta Inteligente ---
def reconhecer_gesto_imune(pontos_mao):
    p_pulso = pontos_mao.landmark[PULSO]
    d_ref = tamanho_mao(pontos_mao)
    
    # Distâncias normatizadas ao pulso
    d_indicador = math.dist((pontos_mao.landmark[PONTA_INDICADOR].x, pontos_mao.landmark[PONTA_INDICADOR].y), (p_pulso.x, p_pulso.y)) / d_ref
    d_medio = math.dist((pontos_mao.landmark[PONTA_MEDIO].x, pontos_mao.landmark[PONTA_MEDIO].y), (p_pulso.x, p_pulso.y)) / d_ref
    d_anelar = math.dist((pontos_mao.landmark[PONTA_ANELAR].x, pontos_mao.landmark[PONTA_ANELAR].y), (p_pulso.x, p_pulso.y)) / d_ref
    d_mindinho = math.dist((pontos_mao.landmark[PONTA_MINDINHO].x, pontos_mao.landmark[PONTA_MINDINHO].y), (p_pulso.x, p_pulso.y)) / d_ref
    
    # Distância do dedão à base do indicador (ponto 5)
    p_base_indicador = pontos_mao.landmark[5]
    d_polegar = math.dist((pontos_mao.landmark[PONTA_POLEGAR].x, pontos_mao.landmark[PONTA_POLEGAR].y), (p_base_indicador.x, p_base_indicador.y)) / d_ref

    # Limiares de zona morta para evitar conflitos mecânicos
    indicador_esticado = d_indicador > 1.55
    indicador_dobrado = d_indicador < 1.25

    medio_esticado = d_medio > 1.60
    medio_dobrado = d_medio < 1.25

    anelar_esticado = d_anelar > 1.50
    anelar_dobrado = d_anelar < 1.25

    mindinho_esticado = d_mindinho > 1.40
    mindinho_dobrado = d_mindinho < 1.15

    polegar_aberto = d_polegar > 1.30
    polegar_fechado = d_polegar < 1.10

    # 1. MÃO ABERTA
    if indicador_esticado and medio_esticado and anelar_esticado and mindinho_esticado:
        return "MAO_ABERTA"
    
    # 2. V_SWIPE
    elif indicador_esticado and medio_esticado and anelar_dobrado and mindinho_dobrado and polegar_fechado:
        return "V_SWIPE"
    
    # 3. L_VOLUME
    elif indicador_esticado and polegar_aberto and medio_dobrado and anelar_dobrado and mindinho_dobrado:
        return "L_VOLUME"
    
    # 4. INDICADOR_SCROLL
    elif indicador_esticado and medio_dobrado and anelar_dobrado and mindinho_dobrado and polegar_fechado:
        return "INDICADOR_SCROLL"
    
    # 5. PUNHO (Todos completamente dobrados)
    elif indicador_dobrado and medio_dobrado and anelar_dobrado and mindinho_dobrado and polegar_fechado:
        return "PUNHO"
    
    return "DESCONHECIDO"


def main():
    captura = cv2.VideoCapture(0)

    if not captura.isOpened():
        print("Erro: não foi possível acessar a câmera.")
        return

    with mp_maos.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as maos:

        estado_duas_maos = "neutro"
        ultima_acao_janela = 0.0
        frames_afastado = 0
        frames_junto = 0

        pincando_esquerda = False
        pincando_direita = False
        dist_normalizada_suave = None

        historico_swipe = []           
        ultima_acao_swipe = 0.0
        tempo_ultima_vez_com_mao = 0.0

        # Variáveis dos novos gestos
        ultimo_play_pause = 0.0
        ultimo_y_indicador = None
        ultima_dist_pinca_L = None
        
        # --- [NOVO] Variável de Controle para a Checagem Dupla do Punho ---
        tempo_inicio_punho = 0.0  # Guarda o exato momento em que o punho foi fechado

        cv2.namedWindow("Rastreamento de Mao", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Rastreamento de Mao", cv2.WND_PROP_TOPMOST, 1)

        while True:
            ok, frame = captura.read()
            if not ok:
                print("Erro ao capturar frame.")
                break

            frame = cv2.flip(frame, 1)
            altura, largura, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultado = maos.process(rgb)

            texto_feedback = "Aguardando gestos..."
            maos_detectadas = []
            lados_detectados = []

            agora_atual = time.time()

            if resultado.multi_hand_landmarks:
                for pontos_mao, info_mao in zip(
                    resultado.multi_hand_landmarks,
                    resultado.multi_handedness,
                ):
                    maos_detectadas.append(pontos_mao)
                    lado = info_mao.classification[0].label  
                    lados_detectados.append(lado)

                    mp_desenho.draw_landmarks(
                        frame,
                        pontos_mao,
                        mp_maos.HAND_CONNECTIONS,
                        mp_estilos.get_default_hand_landmarks_style(),
                        mp_estilos.get_default_hand_connections_style(),
                    )

                    p_ponta = pontos_mao.landmark[PONTA_INDICADOR]
                    cv2.circle(frame, (int(p_ponta.x * largura), int(p_ponta.y * altura)), 10, (0, 255, 0), -1)

                    dist_pinca = distancia_pinca_normalizada(pontos_mao)
                    if lado == "Left":
                        pincando_esquerda = dist_pinca <= LIMITE_PINCA_ATIVAR if not pincando_esquerda else dist_pinca <= LIMITE_PINCA_DESATIVAR
                    else:
                        pincando_direita = dist_pinca <= LIMITE_PINCA_ATIVAR if not pincando_direita else dist_pinca <= LIMITE_PINCA_DESATIVAR

            if "Left" not in lados_detectados:
                pincando_esquerda = False
            if "Right" not in lados_detectados:
                pincando_direita = False

            # --- PROCESSAMENTO COM UMA ÚNICA MÃO ---
            if len(maos_detectadas) == 1:
                tempo_ultima_vez_com_mao = agora_atual
                pontos_mao = maos_detectadas[0]
                gesto_ativo = reconhecer_gesto_imune(pontos_mao)

                # --- 1. GESTO DO SWIPE ---
                if gesto_ativo == "V_SWIPE":
                    tempo_inicio_punho = 0.0  # Reseta cronômetro do punho
                    
                    p_centro = pontos_mao.landmark[BASE_MEDIO]
                    historico_swipe.append((agora_atual, p_centro.x, p_centro.y, True))
                    historico_swipe = [p for p in historico_swipe if agora_atual - p[0] <= 0.45]

                    swipe_detectado = None
                    if len(historico_swipe) >= 3 and (agora_atual - ultima_acao_swipe) >= COOLDOWN_SWIPE:
                        for i in range(len(historico_swipe)):
                            for j in range(i + 1, len(historico_swipe)):
                                p_ini, p_fim = historico_swipe[i], historico_swipe[j]
                                dt = p_fim[0] - p_ini[0]
                                if dt <= TEMPO_SWIPE_MAX:
                                    dx = p_fim[1] - p_ini[1]
                                    dy = p_fim[2] - p_ini[2]
                                    if abs(dx) >= LIMITE_SWIPE_DIST and abs(dy) < abs(dx) * 0.55:
                                        swipe_detectado = "DIREITA" if dx > 0 else "ESQUERDA"
                                        break
                            if swipe_detectado:
                                break

                    if swipe_detectado == "DIREITA":
                        print("➡️ Swipe Direita -> Avançar Janela")
                        pyautogui.keyDown('alt')
                        pyautogui.press('tab')
                        time.sleep(0.1)
                        pyautogui.keyUp('alt')
                        ultima_acao_swipe = agora_atual
                        historico_swipe.clear()
                    elif swipe_detectado == "ESQUERDA":
                        print("⬅️ Swipe Esquerda -> Voltar Janela")
                        pyautogui.keyDown('alt')
                        pyautogui.keyDown('shift')
                        pyautogui.press('tab')
                        time.sleep(0.1)
                        pyautogui.keyUp('shift')
                        pyautogui.keyUp('alt')
                        ultima_acao_swipe = agora_atual
                        historico_swipe.clear()

                    texto_feedback = "Swipe Ativo! Deslize lateralmente"
                    ultimo_y_indicador = None
                    ultima_dist_pinca_L = None

                # --- 2. GESTO DE SCROLL (SÓ INDICADOR) ---
                elif gesto_ativo == "INDICADOR_SCROLL":
                    tempo_inicio_punho = 0.0  # Reseta cronômetro do punho
                    
                    y_atual = pontos_mao.landmark[PONTA_INDICADOR].y
                    if ultimo_y_indicador is not None:
                        dy = y_atual - ultimo_y_indicador
                        if dy < -THRESHOLD_SCROLL_Y:
                            pyautogui.scroll(150)
                            texto_feedback = "📜 Rolando para cima"
                        elif dy > THRESHOLD_SCROLL_Y:
                            pyautogui.scroll(-150)
                            texto_feedback = "📜 Rolando para baixo"
                        else:
                            texto_feedback = "Modo Scroll (mova o indicador)"
                    ultimo_y_indicador = y_atual
                    historico_swipe.clear()
                    ultima_dist_pinca_L = None

                # --- 3. GESTO DE VOLUME (SINAL DO "L") ---
                elif gesto_ativo == "L_VOLUME":
                    tempo_inicio_punho = 0.0  # Reseta cronômetro do punho
                    
                    p_polegar = pontos_mao.landmark[PONTA_POLEGAR]
                    p_indicador = pontos_mao.landmark[PONTA_INDICADOR]
                    dist_L = math.dist((p_polegar.x, p_polegar.y), (p_indicador.x, p_indicador.y)) / tamanho_mao(pontos_mao)

                    if ultima_dist_pinca_L is not None:
                        delta_dist = dist_L - ultima_dist_pinca_L
                        if delta_dist > THRESHOLD_VOLUME_DELTA:
                            pyautogui.press('volumeup')
                            texto_feedback = "🔊 Aumentando Volume"
                        elif delta_dist < -THRESHOLD_VOLUME_DELTA:
                            pyautogui.press('volumedown')
                            texto_feedback = "🔉 Diminuindo Volume"
                        else:
                            texto_feedback = f"Modo Volume (Abertura: {dist_L:.1f})"
                    
                    ultima_dist_pinca_L = dist_L
                    historico_swipe.clear()
                    ultimo_y_indicador = None

                # --- 4. GESTO PLAY / PAUSE (PUNHO COM DUPLA CHECAGEM TEMPORAL) ---
                elif gesto_ativo == "PUNHO":
                    # Inicia a contagem temporal se for o primeiro frame detectado como punho
                    if tempo_inicio_punho == 0.0:
                        tempo_inicio_punho = agora_atual
                    
                    tempo_decorrido_punho = agora_atual - tempo_inicio_punho
                    
                    # Só executa o comando se mantiver o punho fechado continuamente por 0.5 segundos
                    if tempo_decorrido_punho >= TEMPO_CONFIRMACAO_PUNHO:
                        if (agora_atual - ultimo_play_pause) >= COOLDOWN_PLAY_PAUSE:
                            pyautogui.press('playpause')
                            print("✊ Play/Pause Executado (Confirmado!)")
                            ultimo_play_pause = agora_atual
                        texto_feedback = "✊ Punho Confirmado! (Ação Executada)"
                    else:
                        # Feedback visual mostrando o progresso da confirmação
                        progresso = (tempo_decorrido_punho / TEMPO_CONFIRMACAO_PUNHO) * 100
                        texto_feedback = f"✊ Segure para Pausar... {progresso:.0f}%"

                    historico_swipe.clear()
                    ultimo_y_indicador = None
                    ultima_dist_pinca_L = None

                # --- ESTADO DE TRANSIÇÃO / DESCONHECIDO ---
                else:
                    tempo_inicio_punho = 0.0  # Reseta o cronômetro do punho na transição
                    ultimo_y_indicador = None
                    ultima_dist_pinca_L = None
                    texto_feedback = "Aguardando estabilização do gesto..."

            else:
                # Se perder a mão da câmera por mais de 0.15s, reseta todos os temporizadores
                if agora_atual - tempo_ultima_vez_com_mao > 0.15:
                    tempo_inicio_punho = 0.0
                    historico_swipe.clear()
                    ultimo_y_indicador = None
                    ultima_dist_pinca_L = None

            # --- PROCESSAMENTO COM DUAS MÃOS (Sempre reseta cronômetro de punho de mão única) ---
            if len(maos_detectadas) == 2:
                tempo_inicio_punho = 0.0
                
                if pincando_esquerda and pincando_direita:
                    mao_a, mao_b = maos_detectadas[0], maos_detectadas[1]
                    p_a, p_b = ponto_pinca(mao_a), ponto_pinca(mao_b)
                    dist_maos = math.dist(p_a, p_b)

                    escala_media = (tamanho_mao(mao_a) + tamanho_mao(mao_b)) / 2
                    dist_normalizada = dist_maos / escala_media

                    if dist_normalizada_suave is None:
                        dist_normalizada_suave = dist_normalizada
                    else:
                        dist_normalizada_suave = (ALPHA_SUAVIZACAO * dist_normalizada) + ((1 - ALPHA_SUAVIZACAO) * dist_normalizada_suave)

                    pa_px = (int(p_a[0] * largura), int(p_a[1] * altura))
                    pb_px = (int(p_b[0] * largura), int(p_b[1] * altura))
                    cv2.line(frame, pa_px, pb_px, (0, 255, 0), 2)  

                    pode_agir_janela = (agora_atual - ultima_acao_janela) >= COOLDOWN_JANELA

                    if dist_normalizada_suave >= LIMITE_MAOS_AFASTADAS:
                        frames_afastado += 1
                        frames_junto = 0
                        if estado_duas_maos != "afastado" and pode_agir_janela and frames_afastado >= FRAMES_CONFIRMACAO:
                            pyautogui.hotkey("win", "up")  
                            estado_duas_maos = "afastado"
                            ultima_acao_janela = agora_atual
                        texto_feedback = "🖐️↔️🖐️ Expandindo Janela"

                    elif dist_normalizada_suave <= LIMITE_MAOS_JUNTAS:
                        frames_junto += 1
                        frames_afastado = 0
                        if estado_duas_maos != "junto" and pode_agir_janela and frames_junto >= FRAMES_CONFIRMACAO:
                            pyautogui.hotkey("win", "down")  
                            estado_duas_maos = "junto"
                            ultima_acao_janela = agora_atual
                        texto_feedback = "🤏🤏 Encolhendo Janela"
                    else:
                        estado_duas_maos = "neutro"
                        frames_afastado = 0
                        frames_junto = 0
                        texto_feedback = f"Ajuste Fino de Janela (dist={dist_normalizada_suave:.2f})"
                else:
                    dist_normalizada_suave = None
                    estado_duas_maos = "neutro"
                    frames_afastado = 0
                    frames_junto = 0
                    texto_feedback = "Pinçe os dedos nas duas mãos para gerenciar janelas"

            # Renderiza o feedback textual na tela
            cv2.putText(
                frame,
                texto_feedback,
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 165, 255),
                2,
            )

            cv2.imshow("Rastreamento de Mao", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    captura.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()