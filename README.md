# Sign2Talk

El proyecto Sign2Talk busca desarrollar un sistema de traducción de voz a lenguaje de señas
mediante la integración de un asistente virtual (Alexa) y una mano robótica. Este prototipo
permite que las personas con discapacidad auditiva puedan interpretar mensajes hablados a
través de movimientos de una prótesis robótica, fomentando una comunicación más
inclusiva.

## Scripts

`mqtt_subscriber.py` — Gestiona la conexión con el broker
MQTT de AWS IoT Core, interpretando los mensajes enviados
desde la función AWS Lambda.

`sign2talk.py` — Recibe señas, palabras, o letras específicas
y utiliza las librerías nativas de uHandPi para reproducirlas
en las manos robóticas.

`amazon/lambda.py` — Función Lambda invocada por la Skill de
Alexa, recibe los _intents_ y publica los mensajes MQTT
correspondientes a las manos robóticas.

`amazon/skill_alexa.json` — Skill de Alexa que interpreta la voz
del usuario para producir los _intents_ necesarios para iniciar
y terminar la traducción de voz a señas.

`detection/record_data.py` ­— Graba muestras de señas, para cada letra,
en un archivo CSV para entrenar el modelo de clasificación.

`detection/train_model.py` — Entrena el modelo Random Forest usando
las señas grabadas previamente, produciendo un archivo con el modelo
entrenado.

`detection/predict_v3.py` — Ejecuta el modelo y clasifica señas
en tiempo real usando la cámara del dispositivo, permitiendo construir
frases y enviarlas a la Skill de Alexa vía MQTT.
