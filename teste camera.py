import cv2

for camera in range(5):
    print(f"Testando câmera {camera}...")

    captura = cv2.VideoCapture(camera)

    if captura.isOpened():
        print(f"CAMERA {camera} FUNCIONOU!")

        ok, frame = captura.read()

        if ok:
            print("Imagem capturada com sucesso!")

            cv2.imshow(f"Camera {camera}", frame)
            cv2.waitKey(3000)

        captura.release()
        cv2.destroyAllWindows()

    else:
        print(f"Camera {camera} não funcionou.")