import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Endpoint IoT Core
IOT_ENDPOINT = "a17e8foipe6t3v-ats.iot.us-east-1.amazonaws.com"
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
    "adiós": {"tipo": "seña"}
}

def obtener_ultimo_mensaje_robot():
    """Lee el buzón (Shadow) del Robot"""
    try:
        response = iot_client.get_thing_shadow(thingName='Robot')
        payload = json.loads(response['payload'].read())
        # Leemos lo que guardó la otra Lambda
        palabra = payload['state']['reported'].get('ultima_seña', None)
        return palabra
    except Exception as e:
        logger.error(f"No pude leer el shadow: {e}")
        return None

def borrar_mensaje_robot():
    """Borra el mensaje del buzón para que no se repita"""
    try:
        # Enviamos 'null' para borrar el campo ultima_seña
        payload_borrar = {
            "state": {
                "reported": {
                    "ultima_seña": None 
                }
            }
        }
        iot_client.update_thing_shadow(
            thingName='Robot', 
            payload=json.dumps(payload_borrar)
        )
        logger.info("Mensaje marcado como leído (borrado del Shadow).")
    except Exception as e:
        logger.error(f"Error borrando mensaje: {e}")

def lambda_handler(event, context):
    logger.info("Evento recibido: %s", json.dumps(event))
    response_text = "No entendí la palabra, intenta de nuevo."

    try:
        request = event.get("request", {})
        intent_name = request.get("intent", {}).get("name")
        user_id = event.get("session", {}).get("user", {}).get("userId", "anonimo")

        # 1. LAUNCH REQUEST
        if request.get("type") == "LaunchRequest":    
            ultima_palabra = obtener_ultimo_mensaje_robot()
            if ultima_palabra:
                texto = f"El robot dice: {ultima_palabra}. ¿Quieres responder?"
                borrar_mensaje_robot()
            else:
                texto = "Modo traductor activado. Dime una palabra."
            
            modo_traductor[user_id] = True 
            return build_response(texto, end_session=False)

        # 2. MANEJO DE "SÍ"
        elif intent_name == "AMAZON.YesIntent":
            # Si el usuario dice "Sí", le decimos que hable y NO cerramos la sesión
            response_text = "Te escucho. Dime qué quieres traducir."
            modo_traductor[user_id] = True # Reconfirmamos el modo activo
            return build_response(response_text, end_session=False)

        # 3. MANEJO DE "NO"
        elif intent_name == "AMAZON.NoIntent":
            response_text = "Entendido, hasta luego."
            return build_response(response_text, end_session=True)

        # 4. SALIR
        elif intent_name == "DesactivarModoIntent" or intent_name == "AMAZON.StopIntent" or intent_name == "AMAZON.CancelIntent":
            modo_traductor[user_id] = False
            response_text = "Modo traductor desactivado. Hasta luego."
            return build_response(response_text, end_session=True)

        # 5. TRADUCIR
        elif intent_name == "TraducirIntent":
            # Verificar modo activo
            if not modo_traductor.get(user_id, False):
                # Auto-activar por seguridad si ya estamos aquí
                modo_traductor[user_id] = True

            # Obtener el valor del slot (SearchQuery captura la frase)
            frase = request["intent"]["slots"]["palabra"]["value"].lower()
            logger.info(f"Frase recibida: {frase}")

            palabras = frase.split()
            respuestas_acumuladas = [] 

            for palabra in palabras:
                # Caso especial: Si la palabra es "sí" (traducción) y no afirmación
                # (Aunque SearchQuery a veces se confunde con YesIntent, 
                # al tener la frase "di sí" o "traduce sí" entrará aquí)
                if palabra in SENIAS_COMPLETAS:
                    enviar_senia_completa(palabra)
                    respuestas_acumuladas.append(f"Mostrando {palabra}.")
                else:
                    enviar_palabra_para_deletrear(palabra)
                    respuestas_acumuladas.append(f"Deletreando {palabra}.")

            response_text = " ".join(respuestas_acumuladas)
            return build_response(response_text, end_session=False)
        
        elif intent_name == "AMAZON.FallbackIntent":
            # Si el usuario no dice con el sample inicial, le hacemos acuerdo
            response_text = "Para traducir, debes decir la frase completa. Por ejemplo: Traduce Hola."
            return build_response(response_text, end_session=False)

        else:
            response_text = "No entendí el comando. Intenta decir: Traduce hola."
            return build_response(response_text, end_session=False)

    except Exception as e:
        logger.error("Error procesando la solicitud: %s", e)
        return build_response("Hubo un error técnico. Intenta de nuevo.", end_session=True)

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
            "shouldEndSession": end_session
        }
    }
