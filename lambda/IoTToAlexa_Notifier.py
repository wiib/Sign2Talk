import json
import urllib.request
import urllib.parse
import os
import datetime
import logging
import boto3

# Configuración de Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

IOT_ENDPOINT = "abcde12345-ats.iot.us-east-1.amazonaws.com" # Reemplaza con el endpoint real
iot_client = boto3.client("iot-data", endpoint_url=f"https://{IOT_ENDPOINT}")

# ==========================================
# CONFIGURACIÓN (Desde Variables de Entorno)
# ==========================================
CLIENT_ID = os.environ.get('ALEXA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('ALEXA_CLIENT_SECRET')

def get_access_token():
    url = "https://api.amazon.com/auth/o2/token"
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "alexa::proactive_events"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read())
            return response_body.get("access_token")
    except urllib.error.HTTPError as e:
        logger.error(f"Error obteniendo token: {e.read().decode()}")
        raise e

def send_proactive_event(token):
    # IMPORTANTE: Usamos el endpoint de desarrollo. 
    url = "https://api.amazonalexa.com/v1/proactiveEvents/stages/development"
    now = datetime.datetime.utcnow()
    expiry = now + datetime.timedelta(hours=1)
    
    payload = {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.00Z"),
        "referenceId": f"sign-{int(now.timestamp())}",
        "expiryTime": expiry.strftime("%Y-%m-%dT%H:%M:%S.00Z"),
        "event": {
            "name": "AMAZON.MessageAlert.Activated",
            "payload": {
                "state": {"status": "UNREAD", "freshness": "NEW"},
                "messageGroup": {"creator": {"name": "Robot"}, "count": 1}
            }
        },
        "relevantAudience": {"type": "Multicast", "payload": {}}
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        return response.status
    
    try:
        with urllib.request.urlopen(req) as response:
            logger.info(f"Notificación enviada. Status Code: {response.status}")
            return response.status
    except urllib.error.HTTPError as e:
        logger.error(f"Error enviando evento a Alexa: {e.read().decode()}")
        raise e

def lambda_handler(event, context):
    logger.info("Evento recibido: %s", json.dumps(event))
    palabra = event.get("palabra", "desconocida")
    
    try:
        # 1. GUARDAR EN EL BUZÓN (SHADOW)
        logger.info(f"Guardando '{palabra}' en Shadow...")
        payload_shadow = {
            "state": {
                "reported": {
                    "ultima_seña": palabra,
                    "timestamp": str(datetime.datetime.now())
                }
            }
        }
        iot_client.update_thing_shadow(
            thingName='Robot', 
            payload=json.dumps(payload_shadow)
        )
        
        # 2. TOCAR EL TIMBRE (Notificar a Alexa)
        if CLIENT_ID and CLIENT_SECRET:
            token = get_access_token()
            send_proactive_event(token)
        
        return {'statusCode': 200, 'body': "Guardado y Notificado"}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {'statusCode': 500, 'body': str(e)}