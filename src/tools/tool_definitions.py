from vertexai.generative_models import Tool, FunctionDeclaration

crear_tiquete_declaration = FunctionDeclaration(
    name="crear_tiquete_helpdesk",
    description="Útil para crear un nuevo tiquete de soporte cuando un usuario reporta un problema.",
    parameters={
        "type": "object",
        "properties": {
            "descripcion": {"type": "string"},
            "equipo_asignado": {"type": "string"},
            "prioridad": {"type": "string"}
        },
        "required": ["descripcion", "equipo_asignado", "prioridad"]
    }
    
)

consultar_estado_declaration = FunctionDeclaration(
    name="consultar_estado_tiquete",
    description="Útil para verificar el estado actual de un tiquete existente usando su ID.",
    parameters={"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}
)

cerrar_tiquete_declaration = FunctionDeclaration(
    name="cerrar_tiquete",
    description="Cierra un tiquete de soporte que ya ha sido resuelto.",
    parameters={"type": "object", "properties": {"ticket_id": {"type": "string"}, "resolucion": {"type": "string"}}, "required": ["ticket_id", "resolucion"]}
)

reasignar_tiquete_declaration = FunctionDeclaration(
    name="reasignar_tiquete",
    description="Reasigna un tiquete existente a un nuevo responsable.",
    parameters={"type": "object", "properties": {"ticket_id": {"type": "string"}, "nuevo_responsable_email": {"type": "string"}}, "required": ["ticket_id", "nuevo_responsable_email"]}
)

modificar_sla_declaration = FunctionDeclaration(
    name="modificar_sla_manual",
    description="Modifica o cambia el SLA de un tiquete existente a un número específico de horas.",
    parameters={"type": "object", "properties": {"ticket_id": {"type": "string"}, "nuevas_horas_sla": {"type": "integer"}}, "required": ["ticket_id", "nuevas_horas_sla"]}
)

visualizar_flujo_declaration = FunctionDeclaration(
    name="visualizar_flujo_tiquete",
    description="Muestra el historial completo de un tiquete como una infografía visual.",
    parameters={"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}
)

consultar_metricas_declaration = FunctionDeclaration(
    name="consultar_metricas",
    description="Útil para responder preguntas sobre el **sistema de tickets interno**, como 'cuántos tickets abiertos hay' o 'tickets por agente'. **NO USAR** para datos de negocio o de servicios de asistencia.",
    parameters={"type": "object", "properties": {"pregunta_del_usuario": {"type": "string"}}, "required": ["pregunta_del_usuario"]}
)

convertir_a_tarea_declaration = FunctionDeclaration(
    name="convertir_incidencia_a_tarea",
    description="Útil cuando una incidencia reportada no es un error sino una solicitud de nueva funcionalidad o una tarea planificable. La convierte en una tarea en Asana.",
    parameters={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "motivo": {"type": "string", "description": "La razón por la cual se está convirtiendo a tarea."},
            "fecha_entrega": {"type": "string", "description": "La fecha de entrega acordada en formato YYYY-MM-DD."}
        },
        "required": ["ticket_id", "motivo", "fecha_entrega"]
    }
)

start_agendar_reunion_form_declaration = FunctionDeclaration(
    name="start_agendar_reunion_form",
    description="Inicia el flujo para agendar una reunión mostrando un formulario interactivo con campos para el título, invitados, fecha y hora.",
    parameters={
        "type": "object",
        "properties": {
            "email_invitados_adicionales": {
                "type": "array",
                "description": "Una lista opcional de correos electrónicos extraídos de la solicitud del usuario.",
                "items": {"type": "string"}
            }
        }
    }
)

start_user_form_declaration = FunctionDeclaration(
    name="start_user_management_form",
    description="Muestra un formulario interactivo para que un administrador pueda agregar o modificar los roles y departamentos de los usuarios. Usar cuando el admin quiera 'gestionar usuarios', 'agregar usuario', etc.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

visualizar_metrica_looker_declaration = FunctionDeclaration(
    name="visualizar_metrica_looker",
    description="Busca y muestra un GRÁFICO o 'Look' individual desde Looker. Úsalo cuando el usuario pida ver una métrica específica, como 'tickets por equipo'.",
    parameters={
        "type": "object",
        "properties": {
            "nombre_metrica": {
                "type": "string",
                "description": "El nombre del 'Look' que el usuario quiere ver."
            },
            "solicitante_email": {
                "type": "string",
                "description": "El email del usuario que realiza la solicitud."
            }
        },
        "required": ["nombre_metrica"]
    }
)

visualizar_dashboard_looker_declaration = FunctionDeclaration(
    name="visualizar_dashboard_looker",
    description="Busca y muestra una previsualización de un DASHBOARD o PANEL DE CONTROL completo desde Looker. Úsalo cuando el usuario pida ver un 'dashboard', 'panel' o 'panel de control' general.",
    parameters={
        "type": "object",
        "properties": {
            "nombre_dashboard": {
                "type": "string",
                "description": "El nombre del dashboard que el usuario quiere ver. Por ejemplo: 'Tickets (Seguimiento General)'."
            },
            "solicitante_email": {
                "type": "string",
                "description": "El email del usuario que realiza la solicitud."
            }
        },
        "required": ["nombre_dashboard"]
    }
)

update_user_declaration = FunctionDeclaration(
    name="update_user_in_system",
    description="Útil para modificar el rol y/o departamento de un usuario existente, o para crear un usuario si no existe.",
    parameters={
        "type": "object",
        "properties": {
            "email_a_modificar": {"type": "string", "description": "El email del usuario a actualizar."},
            "nuevo_rol": {"type": "string", "description": "El nuevo rol a asignar (admin, lead, agent, user)."},
            "nuevo_departamento": {"type": "string", "description": "El nuevo departamento al que pertenecerá."}
        },
        "required": ["email_a_modificar", "nuevo_rol", "nuevo_departamento"]
    }
)

delete_user_declaration = FunctionDeclaration(
    name="delete_user_from_system",
    description="Elimina permanentemente a un usuario del sistema usando su email.",
    parameters={
        "type": "object",
        "properties": {
            "email_a_eliminar": {"type": "string", "description": "El email del usuario a eliminar."}
        },
        "required": ["email_a_eliminar"]
    }
)

draft_communication_declaration = FunctionDeclaration(
    name="redactar_borrador",
    description="Redacta un borrador de comunicación profesional. Es útil cuando el usuario pide 'ayúdame a escribir un correo' o 'redacta un mensaje de chat'.",
    parameters={
        "type": "object",
        "properties": {
            "contexto": {
                "type": "string",
                "description": "El tema principal o los puntos clave que debe incluir el mensaje."
            },
            "destinatario": {
                "type": "string",
                "description": "El nombre de la persona o grupo al que va dirigido el mensaje."
            },
            "formato": {
                "type": "string",
                "description": "El formato de la comunicación. Debe ser 'email' o 'chat'.",
                "enum": ["email", "chat"]
            }
        },
        "required": ["contexto", "destinatario", "formato"]
    }
)

consultar_dwh_declaration = FunctionDeclaration(
    name="consultar_dwh",
   description="Útil para responder preguntas sobre **datos de negocio y operaciones de servicios de asistencia** que están en el Data Warehouse (DWH). Usar para preguntas como 'total de servicios en un país', 'promedio de distancia', o 'servicios por aseguradora'.",
    parameters={
        "type": "object",
        "properties": {
            "pregunta_del_usuario": {"type": "string"}
        },
        "required": ["pregunta_del_usuario"]
    }
)


all_tools_config = Tool(function_declarations=[
    crear_tiquete_declaration,
    consultar_estado_declaration,
    cerrar_tiquete_declaration,
    reasignar_tiquete_declaration,
    modificar_sla_declaration,
    visualizar_flujo_declaration,
    consultar_metricas_declaration,
    convertir_a_tarea_declaration,
    start_agendar_reunion_form_declaration,
    start_user_form_declaration,
    visualizar_metrica_looker_declaration,
    update_user_declaration,
    delete_user_declaration,
    draft_communication_declaration,
    visualizar_dashboard_looker_declaration,
    consultar_dwh_declaration, 
])