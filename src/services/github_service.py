import os
import requests
from vertexai.generative_models import GenerativeModel
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file

def _load_prompt_from_file(file_path: str) -> str:
    """Carga un prompt desde un archivo de texto."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"🔴 Error crítico: No se encontró el archivo de prompt en {file_path}")
        return "Por favor, revisa el siguiente código: {code_diff}"

def _get_prompt_for_repository(repo_name: str, code_diff: str) -> str:
    """
    Selecciona, carga y formatea el prompt de revisión de código adecuado
    basado en el nombre del repositorio.
    """
    if "looker" in repo_name.lower():
        print("▶️  Repositorio de Looker detectado. Usando prompt especializado para LookML.")
        prompt_template = load_prompt_from_file('github_lookml_review.md')
    else:
        print("▶️  Repositorio de Dataform/genérico detectado. Usando prompt para Dataform.")
        prompt_template = load_prompt_from_file('github_dataform_review.md')

    return prompt_template.format(code_diff=code_diff)


def _approve_pull_request(pr_data: dict, headers: dict):
    """
    Envía una aprobación formal a un Pull Request a través de la API de GitHub.
    """
    pr_number = pr_data.get("pull_request", {}).get("number")
    repo_full_name = pr_data.get("repository", {}).get("full_name")

    if not all([pr_number, repo_full_name]):
        print("🔴 Error: No se pudo obtener el número del PR o el nombre del repositorio para aprobarlo.")
        return

    approve_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews"
    # CAMBIO: Se actualiza el cuerpo del mensaje de aprobación automática.
    approve_payload = {
        "event": "APPROVE",
        "body": "Revisión automatizada por GuanaCloud Platform: El código cumple con los estándares de calidad."
    }

    try:
        print(f"▶️  Aprobando automáticamente el PR #{pr_number}...")
        response = requests.post(approve_url, headers=headers, json=approve_payload)
        response.raise_for_status()
        print(f"✅ PR #{pr_number} aprobado exitosamente.")
    except requests.exceptions.HTTPError as http_err:
        print(f"🔴 Error de HTTP al intentar aprobar el PR: {http_err} - {http_err.response.text}")
    except Exception as e:
        print(f"🔴 Error inesperado al aprobar el PR: {e}")


def ejecutar_revision_de_codigo(pr_data: dict):
    """
    Orquesta el proceso completo de revisión de código para un Pull Request.
    Si no hay observaciones, aprueba el PR automáticamente.
    """
    try:

        api_url = pr_data.get("pull_request", {}).get("url")
        if not api_url:
            print("🔴 Error: No se encontró la 'url' del PR en el payload del webhook.")
            return

        repo_name = pr_data.get("repository", {}).get("name", "")

        headers = {
            "Authorization": f"token {settings.GITHUB_PAT}",
            "Accept": "application/vnd.github.v3.diff" 
        }
        diff_response = requests.get(api_url, headers=headers)
        diff_response.raise_for_status()
        code_diff = diff_response.text

        print(f"▶️  Diff obtenido para el PR #{pr_data.get('number')} en el repo '{repo_name}'. Enviando a Gemini para análisis...")

        prompt = _get_prompt_for_repository(repo_name, code_diff)

        model = GenerativeModel(settings.GEMINI_TASK_MODEL)
        response = model.generate_content(prompt)
        review_comment = response.text

        comments_url = pr_data.get("pull_request", {}).get("comments_url")
        if not comments_url:
            print("🔴 Error: No se encontró la 'comments_url' en el payload.")
            return

        post_headers = {"Authorization": f"token {settings.GITHUB_PAT}"}
        comment_payload = {"body": review_comment}
        comment_response = requests.post(comments_url, headers=post_headers, json=comment_payload)
        comment_response.raise_for_status()

        print(f"✅ Comentario de revisión de código publicado exitosamente en el PR #{pr_data.get('number')}.")

        frase_aprobacion = "✅ ¡Excelente trabajo! El código sigue todas nuestras buenas prácticas. ¡Listo para merge!"
        if frase_aprobacion in review_comment and "dwh_dataform" in repo_name:
            _approve_pull_request(pr_data, post_headers)

    except requests.exceptions.HTTPError as http_err:
        print(f"🔴 Error de HTTP al comunicarse con la API de GitHub: {http_err} - {http_err.response.text}")
    except Exception as e:
        print(f"🔴 Error inesperado en la ejecución de la revisión de código: {e}")