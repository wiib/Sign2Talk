import paho.mqtt.client as mqtt
import ssl
import json
import time
from unidecode import unidecode

# LeArm es una librería incluída en el dispositivo uHandPi
from LeArm import initLeArm

from sign2talk import load_signs, phrase_to_signs, play_sign

# Variables de configuración
ENDPOINT = "abcdefg123456-ats.iot.us-east-1.amazonaws.com"
PORT = 8883
TOPICS = ["traductor/mano_izquierda", "traductor/mano_derecha", "traductor/deletrear"]

CA_PATH = "AmazonRootCA1.pem"
CERT_PATH = "certificate.pem.crt"
KEY_PATH = "private.pem.key"

# Ruta donde están ubicadas las señas disponibles
SIGN_PATH = "/home/pi/uHand_Pi/ActionGroups/Letters"
signs = load_signs(SIGN_PATH)

# Inicializar el brazo en la posición 0
initLeArm([0, 0, 0, 0, 0, 0])

# Tiempos de espera para las señas del brazo opuesto
sleep_times = {
    "w": 0.5,
    "k": 0.5,
    "m": 0.5,
    "permiso": 3.5,
    "n": 0.5,
    "porfavor": 0.5,
    "corazon": 0.5,
    "x": 0.5,
    "ll": 1.5,
    "z": 2.0,
    "s": 0.5,
    "t": 0.5,
    "j": 1.5,
    "diff": 1.5,
    "p": 0.5,
    "r": 0.5,
    "i": 1.0,
    "v": 1.5,
    "q": 0.5,
    "no": 3.0,
    "l": 0.5,
    "permiso": 3.5,
    "gracias": 2.5,
    "y": 0.5,
    "o": 0.5,
    "si": 2.0,
    "ñ": 1.5,
    "u": 0.5,
    "rr": 1.5,
}


# Callback: Al conectarse al broker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Conectado correctamente al IoT Core")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"📡 Suscrito al topic: {topic}")
    else:
        print(f"❌ Error de conexión: {rc}")


# Callback: Al recibir un mensaje
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    modo = payload.get("modo")

    try:
        if modo == "seña":
            palabra = payload.get("palabra", "")
            print(f"🤟 Ejecutando seña completa: {palabra}")
            sequence = phrase_to_signs(unidecode(palabra), signs)
            for s in sequence:
                play_sign(s)
            if unidecode(palabra) in sleep_times:
                time.sleep(sleep_times[unidecode(palabra)])
                time.sleep(1)
            time.sleep(0.7)
            print(f"✅ Seña {palabra} completada.\n")

        elif modo == "deletreo":
            palabra = payload.get("palabra", "")
            print(f"🔠 Deletreando palabra: {palabra}")
            for letra in palabra:
                sequence = phrase_to_signs(unidecode(letra), signs)
                print(f"➡️ Mostrando letra: {letra}")
                for s in sequence:
                    play_sign(s)
                if unidecode(letra) in sleep_times:
                    time.sleep(sleep_times[letra])
                    time.sleep(1)
                time.sleep(0.7)
            print(f"✅ Deletreo completo de '{palabra}'\n")

        else:
            print(f"⚠️ Modo no reconocido: {modo}")
    except Exception as e:
        print(f"{e}")


# Cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Configuración de seguridad (TLS)
client.tls_set(
    ca_certs=CA_PATH,
    certfile=CERT_PATH,
    keyfile=KEY_PATH,
    tls_version=ssl.PROTOCOL_TLSv1_2,
)

print("🔄 Conectando al AWS IoT Core...")
client.connect(ENDPOINT, PORT)
client.loop_forever()
