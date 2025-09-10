import json
from src.utils.database_client import get_all_departments

def update_user_in_system(email_a_modificar: str, nuevo_rol: str, nuevo_departamento: str, **kwargs) -> str:
    """Función de herramienta para que la IA actualice o inserte un usuario."""
    return upsert_user(email_a_modificar, nuevo_rol, nuevo_departamento)

def delete_user_from_system(email_a_eliminar: str, **kwargs) -> str:
    """Función de herramienta para que la IA elimine un usuario."""
    return delete_user(email_a_eliminar)

def start_user_management_form(**kwargs) -> str:
    departments = get_all_departments()
    
    department_options = [{"text": dept, "value": dept} for dept in departments]
    department_options.append({"text": "--- Crear Nuevo Departamento ---", "value": "__create_new__"})


    card = {
        "cardsV2": [{
            "cardId": "user_management_card",
            "card": {
                "header": {
                    "title": "Gestión de Roles y Usuarios",
                    "subtitle": "Añade o modifica un usuario del sistema."
                },
                "sections": [{
                    "widgets": [
                        {
                            "textInput": {
                                "label": "Email del Usuario",
                                "name": "user_email"
                            }
                        },
                        {
                            "selectionInput": {
                                "name": "role",
                                "label": "Selecciona un Rol",
                                "items": [
                                    {"text": "Admin (Control Total)", "value": "admin"},
                                    {"text": "Lead (Líder de Equipo)", "value": "lead"},
                                    {"text": "Agent (Agente de Soporte)", "value": "agent"},
                                    {"text": "User (Usuario Estándar)", "value": "user"}
                                ]
                            }
                        },
                        {
                            "selectionInput": {
                                "name": "department",
                                "label": "Selecciona un Departamento",
                                "items": department_options,
                                "onChangeAction": {
                                    "function": "handle_department_change" 
                                }
                            }
                        },
                        {
                            "textInput": {
                                "label": "Nombre del Nuevo Departamento",
                                "name": "new_department_name"
                            }
                        },
                        {
                            "buttonList": {
                                "buttons": [{
                                    "text": "Guardar Cambios",
                                    "onClick": {
                                        "action": {
                                            "function": "submit_user_management_form"
                                        }
                                    }
                                }]
                            }
                        }
                    ]
                }]
            }
        }]
    }
    return json.dumps(card)