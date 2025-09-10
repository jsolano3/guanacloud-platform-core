
import os

def load_prompt_from_file(file_name: str) -> str:
    """
    Carga un prompt desde un archivo en la carpeta 'src/prompts/'.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, '..', 'prompts', file_name)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"🔴 Error crítico: No se encontró el archivo de prompt en {file_path}")
        return "Error: No se pudo cargar la plantilla de prompt. Por favor, revisa la configuración."
    except Exception as e:
        print(f"🔴 Error inesperado al cargar el prompt {file_name}: {e}")
        return "Error: Ocurrió un problema al leer el archivo de prompt."