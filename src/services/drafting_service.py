import json
from vertexai.generative_models import GenerativeModel
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file

def redactar_borrador(contexto: str, destinatario: str, formato: str, solicitante_nombre: str, **kwargs) -> str:
    """
    Redacta un borrador de comunicación (correo o chat) usando una firma genérica.
    """
    try:
        print(f"▶️  Iniciando redacción de un borrador en formato '{formato}'.")

        if formato == "email":
            # Usamos una firma genérica como placeholder.
            firma_usuario = f"\n\nSaludos cordiales,\n{solicitante_nombre}"

            prompt_template = load_prompt_from_file("draft_email.md")
            prompt = prompt_template.format(
                destinatario=destinatario,
                remitente=solicitante_nombre,
                contexto=contexto,
                firma=firma_usuario
            )
        elif formato == "chat":
            prompt_template = load_prompt_from_file("draft_chat_message.md")
            prompt = prompt_template.format(
                destinatario=destinatario,
                contexto=contexto
            )
        else:
            return "Error: Formato no válido. Por favor, elige 'email' o 'chat'."

        model = GenerativeModel(settings.GEMINI_TASK_MODEL)
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print(f"🔴 Error durante la redacción del borrador: {e}")
        return f"Lo siento, ocurrió un error al intentar generar el borrador: {e}"