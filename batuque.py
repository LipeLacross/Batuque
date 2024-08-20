import sys
import numpy as np
import cv2
import time
from pygame import mixer

# Configurações de cor para detecção
h_low, h_high = 146, 172
s_low, s_high = 116, 255
v_low, v_high = 123, 255
pinkLower = (h_low, s_low, v_low)
pinkUpper = (h_high, s_high, v_high)

def run_batuque():
    # Configurações de dimensão da janela da câmera
    width = 1920
    height = 1080

    # Variáveis de tempo para controlar o tempo entre toques
    last_played_time = [0, 0, 0, 0, 0]
    cooldown = 0.5  # Tempo em segundos entre toques

    # Inicializar o mixer do pygame
    mixer.init()
    drum_sounds = [
        mixer.Sound('src/sounds/Chimbal/Chimbal.mp3'),
        mixer.Sound('src/sounds/Caixa/Caixa.mp3'),
        mixer.Sound('src/sounds/Bumbo/Bumbo.wav'),
        mixer.Sound('src/sounds/Crash/Crash.mp3'),
        mixer.Sound('src/sounds/Caixa2/Caixa2.mp3')
    ]

    def state_machine(sound_index):
        current_time = time.time()
        if current_time - last_played_time[sound_index] >= cooldown:
            drum_sounds[sound_index].play()
            last_played_time[sound_index] = current_time

    def calc_mask(frame, lower, upper):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, lower, upper)

    def ROI_analysis(roi, sound_index, lower, upper, min_value=30):
        mask = calc_mask(roi, lower, upper)
        summation = np.sum(mask)
        if summation >= min_value:
            state_machine(sound_index)
        return mask

    # Iniciar a câmera
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    instruments = ['Chimbal.png', 'Caixa.png', 'Bumbo.png', 'Crash.png', 'Caixa2.png']
    instrument_images = [cv2.imread(f'./src/Images/{img}', cv2.IMREAD_UNCHANGED) for img in instruments]
    instrument_images[1] = cv2.resize(instrument_images[1], (200, 150), interpolation=cv2.INTER_CUBIC)  # Redimensionar Caixa
    instrument_images[4] = cv2.resize(instrument_images[4], (200, 150), interpolation=cv2.INTER_CUBIC)  # Redimensionar Caixa espelhada

    # Definir as regiões de interesse (ROI) dos instrumentos
    H, W = 720, 1280
    centers = [
        (W * 1 // 8, H * 4 // 8),  # Chimbal
        (W * 6 // 8, H * 6 // 8),  # Caixa
        (W * 4 // 8, H * 7 // 8),  # Bumbo
        (W * 7 // 8, H * 4 // 8),  # Crash
        (W * 2 // 8, H * 6 // 8)   # Caixa espelhada
    ]
    sizes = [(200, 200), (200, 150), (200, 200), (200, 200), (200, 150)]

    ROIs = [(center[0] - size[0] // 2, center[1] - size[1] // 2, center[0] + size[0] // 2, center[1] + size[1] // 2) for center, size in zip(centers, sizes)]

    # Loop principal
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        cv2.putText(frame, 'Projeto: Batuque', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (20, 20, 20), 2)

        for i, (top_x, top_y, bottom_x, bottom_y) in enumerate(ROIs):
            roi = frame[top_y:bottom_y, top_x:bottom_x]
            mask = ROI_analysis(roi, i, pinkLower, pinkUpper)

            overlay = instrument_images[i]

            # Ajuste de dimensões para garantir que overlay e roi tenham o mesmo tamanho
            overlay_resized = cv2.resize(overlay, (roi.shape[1], roi.shape[0]))

            if overlay_resized.shape[2] == 4:  # Verificar se a imagem tem canal alfa
                # Separar os canais de cor e alfa
                b, g, r, a = cv2.split(overlay_resized)
                overlay_rgb = cv2.merge((b, g, r))

                alpha_mask = a / 255.0 * 0.5  # 50% de transparência
                alpha_inv = 1.0 - alpha_mask

                for c in range(0, 3):
                    frame[top_y:bottom_y, top_x:bottom_x, c] = (alpha_mask * overlay_rgb[:, :, c] +
                                                                alpha_inv * frame[top_y:bottom_y, top_x:bottom_x, c])
            else:
                frame[top_y:bottom_y, top_x:bottom_x] = cv2.addWeighted(overlay_resized, 0.5, roi, 0.5, 0)

        cv2.imshow('Batuque Project', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
    sys.exit()
