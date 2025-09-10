import json
import requests
from src.config import settings

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def enviar_notificacion_email(destinatario: str, asunto: str, cuerpo_html: str):
    if not settings.BREVO_API_KEY:
        print("🔴 Error Crítico: La variable BREVO_API_KEY no está configurada.")
        return False
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": settings.SENDER_NAME, "email": settings.SENDER_EMAIL},
        "to": [{"email": destinatario}],
        "subject": asunto,
        "htmlContent": cuerpo_html
    }
    try:
        response = requests.post(BREVO_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"✅ Correo de notificación enviado a {destinatario} a través de Brevo.")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"🔴 Error HTTP al enviar correo con Brevo: {http_err} - {response.text}")
        return False
    except Exception as e:
        print(f"🔴 Error inesperado en el envío de correo con Brevo: {e}")
        return False


def enviar_notificacion_chat(mensaje: str | dict):
    """
    Envía un mensaje a un espacio de Google Chat usando un webhook.
    Puede enviar texto simple (str) o una tarjeta interactiva (dict).
    """
    if not settings.GOOGLE_CHAT_WEBHOOK_URL:
        print("⚠️  Advertencia: No se ha configurado la URL del webhook de Google Chat.")
        return False
        
    try:
        mensaje_json = {"text": mensaje} if isinstance(mensaje, str) else mensaje

        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        response = requests.post(settings.GOOGLE_CHAT_WEBHOOK_URL, headers=headers, data=json.dumps(mensaje_json)) 
        response.raise_for_status()
        print("✅ Notificación enviada a Google Chat.")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"🔴 Error HTTP al enviar notificación a Google Chat: {http_err} - {response.text}")
        return False
    except Exception as e:
        print(f"🔴 Error inesperado en el envío de mensaje de Chat: {e}")
        return False