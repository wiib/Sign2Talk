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
