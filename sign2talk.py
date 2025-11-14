import os
import time
import string

# LeArm es una librería incluída en el dispositivo uHandPi
from LeArm import runActionGroup, initLeArm

# Directorio donde están los archivos .d6a
SIGN_PATH = "/home/pi/uHand_Pi/ActionGroups/Letters"

initLeArm([0, 0, 0, 0, 0, 0])


# Función para limpiar y normalizar texto
def normalize_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.strip()


# Cargar archivos disponibles
def load_signs(path):
    return {
        os.path.splitext(f)[0]: os.path.join(path, f)
        for f in os.listdir(path)
        if f.endswith(".d6a")
    }


# Función para mapear frase a archivos
def phrase_to_signs(phrase, signs):
    sequence = []
    words = normalize_text(phrase).split()

    for word in words:
        # Si existe un archivo completo para la palabra (por ejemplo "sign_si")
        full_key = f"sign_{word}"
        if full_key in signs:
            sequence.append(signs[full_key])
        else:
            # Si no hay palabra completa, deletreamos con los archivos de letras
            for letter in word:
                letter_key = f"letter_{letter}"
                if letter_key in signs:
                    sequence.append(signs[letter_key])
    return sequence


# Ejecuta la seña usando la librería nativa de uHandPi
def play_sign(file_path):
    print(f"Ejecutando seña: {file_path}")
    runActionGroup(file_path, 1)
    time.sleep(1)
