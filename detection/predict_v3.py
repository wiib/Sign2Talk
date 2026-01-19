import cv2
import mediapipe as mp
import pickle
import numpy as np
import paho.mqtt.client as mqtt
import ssl
import json
import time

# ==========================================
# ☁️ CONFIGURACIÓN AWS IOT
# ==========================================
# Tu endpoint (el mismo que usaste en el otro script)
IOT_ENDPOINT = "abcdefg123456-ats.iot.us-east-1.amazonaws.com" 
PORT = 8883
TOPIC_PUB = "robot/sign_detected"

# Rutas a tus certificados (Asegúrate de que estén en la carpeta)
CA_PATH = "AmazonRootCA1.pem"
CERT_PATH = "certificate.pem.crt"
KEY_PATH = "private.pem.key"

# ==========================================
# 🧠 CONFIGURACIÓN MQTT
# ==========================================
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado a AWS IoT. Listo para enviar a: {TOPIC_PUB}")
    else:
        print(f"❌ Error de conexión. Código: {rc}")

mqtt_client.on_connect = on_connect

# Configuración de seguridad (TLS 1.2)
mqtt_client.tls_set(
    ca_certs=CA_PATH,
    certfile=CERT_PATH,
    keyfile=KEY_PATH,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

# Conectar en segundo plano (Non-blocking)
print("🔄 Conectando a la nube...")
mqtt_client.connect(IOT_ENDPOINT, PORT)
mqtt_client.loop_start() 

# ==========================================
# 📷 CONFIGURACIÓN VISIÓN ARTIFICIAL
# ==========================================
try:
    with open('model.p', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("❌ Error: model.p no encontrado. ¡Entrena el modelo primero!")
    exit()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

# Variables para controlar el flujo de notificaciones (Debounce)
ultimo_envio_tiempo = 0
COOLDOWN_SEGUNDOS = 8  # Alexa solo hablará cada 8 segundos máximo

# Variables para el control de la frase
frase_actual = ""
ultimo_agregado_tiempo = 0
COOLDOWN_TECLA = 0.5  # Tiempo mínimo entre agregar letras (para evitar rebotes)

print("📷 Cámara iniciada.")
print("   [ESPACIO] -> Agregar letra detectada")
print("   [ENTER]   -> Enviar frase a Alexa")
print("   [BORRAR]  -> Eliminar última letra")
print("   [Q]       -> Salir")

while True:
    ret, frame = cap.read()
    if not ret: break

    # Espejo y conversión de color
    frame = cv2.flip(frame, 1) # Usualmente 1 es espejo horizontal
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Preprocesamiento de datos (Normalización)
            base_x = hand_landmarks.landmark[0].x
            base_y = hand_landmarks.landmark[0].y
            
            data_aux = []
            for lm in hand_landmarks.landmark:
                data_aux.extend([lm.x - base_x, lm.y - base_y])
            
            # Predicción
            try:
                prediction = model.predict([data_aux])
                predicted_character = prediction[0]
                
                # Confianza
                proba = model.predict_proba([data_aux])
                confidence = np.max(proba)
                
                # ==========================================
                # 📝 INTERFAZ VISUAL ACTUALIZADA
                # ==========================================
                
                # Dibujar rectángulo de fondo para la letra actual
                cv2.rectangle(frame, (0, 0), (300, 60), (0,0,0), -1)
                
                # Mostrar letra detectada en tiempo real (solo visual)
                color_texto = (255, 255, 255)
                if confidence > 0.85:
                    color_texto = (0, 255, 0) # Verde si es confiable
                    
                cv2.putText(frame, f"Detectado: {predicted_character} ({int(confidence*100)}%)", 
                           (10, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, color_texto, 1)

                # Mostrar la FRASE que estás construyendo en la parte inferior
                cv2.rectangle(frame, (0, 400), (640, 480), (50, 50, 50), -1)
                cv2.putText(frame, f"Frase: {frase_actual}", 
                           (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            except Exception as e:
                print(f"Error en predicción: {e}") 
    # ==========================================
    # ⌨️ CONTROL DE TECLADO (ESPACIO / ENTER)
    # ==========================================
    # Capturamos la tecla una sola vez por frame
    key = cv2.waitKey(1) & 0xFF

    # [ESPACIO]: Agregar letra a la frase
    if key == 32: 
        tiempo_actual = time.time()
        # Solo agregar si: 
        # 1. Hay detección activa (predicted_character existe)
        # 2. La confianza es buena
        # 3. Pasó el tiempo de cooldown para evitar duplicados rápidos
        if 'predicted_character' in locals() and confidence > 0.85:
            if (tiempo_actual - ultimo_agregado_tiempo) > COOLDOWN_TECLA:
                frase_actual += predicted_character
                ultimo_agregado_tiempo = tiempo_actual
                print(f"➕ Letra agregada: {predicted_character} | Frase: {frase_actual}")

    # [ENTER]: Enviar frase completa a MQTT (Código 13)
    elif key == 13: 
        if len(frase_actual) > 0:
            payload = {
                "palabra": frase_actual, # Ahora enviamos la frase completa
                "confianza": 1.0,        # Confianza manual del usuario
                "modo": "frase_completa"
            }
            mqtt_client.publish(TOPIC_PUB, json.dumps(payload), qos=1)
            print(f"📤 FRASE ENVIADA: {frase_actual}")
            frase_actual = "" # Limpiar buffer
        else:
            print("⚠️ Buffer vacío, nada que enviar.")

    # [BACKSPACE]: Borrar última letra (Código 8)
    elif key == 8:
        frase_actual = frase_actual[:-1]
        print(f"🔙 Borrado. Nueva frase: {frase_actual}")

    # [Q]: Salir
    elif key == ord('q'):
        break

    cv2.imshow('Sign Language Detector', frame)

cap.release()
cv2.destroyAllWindows()

mqtt_client.loop_stop()
mqtt_client.disconnect()
