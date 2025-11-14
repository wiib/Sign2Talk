import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Endpoint IoT Core
IOT_ENDPOINT = "abcdefg123456-ats.iot.us-east-1.amazonaws.com"  # Ejemplo de endpoint, reemplazar con el real
iot_client = boto3.client("iot-data", endpoint_url=f"https://{IOT_ENDPOINT}")

# Estado temporal de los usuarios (modo activado/desactivado)
modo_traductor = {}

# Diccionario de señas disponibles
SENIAS_COMPLETAS = {
    "hola": {"tipo": "seña"},
    "gracias": {"tipo": "seña"},
    "sí": {"tipo": "seña"},
    "no": {"tipo": "seña"},
    "te quiero": {"tipo": "seña"},
    "corazón": {"tipo": "seña"},
    "dedo": {"tipo": "seña"},
    "permiso": {"tipo": "seña"},
}


def lambda_handler(event, context):
    logger.info("Evento recibido: %s", json.dumps(event))
    response_text = "No entendí la palabra, intenta de nuevo."

    try:
        request = event.get("request", {})
        intent_name = request.get("intent", {}).get("name")
        user_id = event.get("session", {}).get("user", {}).get("userId", "anonimo")

        # Cuando el usuario abre la skill ("Alexa, modo traductor de señas")
        if request.get("type") == "LaunchRequest":
            modo_traductor[user_id] = True
            response_text = (
                "Modo traductor de señas activado. Dime una palabra para traducir."
            )
            return build_response(response_text, end_session=False)

        elif intent_name == "DesactivarModoIntent":
            modo_traductor[user_id] = False
            response_text = "Modo traductor desactivado. Hasta luego."
            return build_response(response_text, end_session=True)

        elif intent_name == "TraducirIntent":
            # Si no está en modo activo
            if not modo_traductor.get(user_id, False):
                response_text = "No estás en modo traductor. Di 'Alexa, modo traductor de señas' para activarlo."
                return build_response(response_text, end_session=False)

            frase = request["intent"]["slots"]["palabra"]["value"].lower()
            logger.info(f"Frase recibida: {frase}")

            palabras = frase.split()
            for palabra in palabras:
                if palabra in SENIAS_COMPLETAS:
                    enviar_senia_completa(palabra)
                    response_text = f"Mostrando seña de {palabra}."
                else:
                    enviar_palabra_para_deletrear(palabra)
                    response_text = f"Deletreando {palabra}."

            return build_response(response_text, end_session=False)

        else:
            response_text = (
                "No entendí el comando. Puedes decir una palabra para traducir."
            )
            return build_response(response_text, end_session=False)

    except Exception as e:
        logger.error("Error procesando la solicitud: %s", e)
        return build_response(
            "Hubo un error al procesar tu solicitud.", end_session=True
        )


def enviar_senia_completa(palabra):
    payload = {"modo": "seña", "palabra": palabra}
    for topic in ["traductor/mano_izquierda", "traductor/mano_derecha"]:
        iot_client.publish(topic=topic, qos=0, payload=json.dumps(payload))
    logger.info(f"Seña completa enviada: {palabra}")


def enviar_palabra_para_deletrear(palabra):
    payload = {"modo": "deletreo", "palabra": palabra}
    topic = "traductor/deletrear"
    iot_client.publish(topic=topic, qos=0, payload=json.dumps(payload))
    logger.info(f"Palabra enviada para deletrear: {palabra}")


def build_response(output_text, end_session=True):
    """Construye la respuesta estándar para Alexa"""
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": output_text},
            "shouldEndSession": end_session,
        },
    }
