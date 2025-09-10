
import os
from dotenv import load_dotenv

print("▶️  Cargando variables de entorno...")
load_dotenv()

from src.services.knowledge_service import search_knowledge_base

def run_test():
    """
    Ejecuta una prueba simple contra el servicio de la base de conocimiento.
    """
    print("\n=============================================")
    print("🚀 INICIANDO PRUEBA DE LA BASE DE CONOCIMIENTO")
    print("=============================================\n")

    query_con_respuesta = "¿cuantos dias de vacaciones tengo?"
    print(f"❓ Consulta de prueba (exitosa): '{query_con_respuesta}'")

    resultado_exitoso = search_knowledge_base(query_con_respuesta)

    if resultado_exitoso and resultado_exitoso.get("answer"):
        print("\n✅ PRUEBA EXITOSA:")
        print(f"   Respuesta: {resultado_exitoso['answer']}")
        print(f"   Fuente: {resultado_exitoso['source']}\n")
    else:
        print("\n❌ PRUEBA FALLIDA: No se recibió una respuesta del KB.\n")
        print(f"   Resultado recibido: {resultado_exitoso}\n")

    print("---------------------------------------------")

    query_sin_respuesta = "¿cual es el precio del dolar?"
    print(f"❓ Consulta de prueba (fallida): '{query_sin_respuesta}'")

    resultado_fallido = search_knowledge_base(query_sin_respuesta)

    if not resultado_fallido:
        print("\n✅ PRUEBA EXITOSA: Como se esperaba, no se encontró un documento relevante.\n")
    else:
        print("\n❌ PRUEBA FALLIDA: Se esperaba 'None' pero se recibió una respuesta.\n")
        print(f"   Resultado recibido: {resultado_fallido}\n")

if __name__ == "__main__":
    run_test()