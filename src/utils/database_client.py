import sqlalchemy
from sqlalchemy.sql import text
from src.config import settings
from src.services.notification_service import enviar_notificacion_email
from google.oauth2.credentials import Credentials
# No fue necesario importar 'json' ya que las funciones que lo usaban están comentadas.

db_pool = None

def get_db_connection() -> sqlalchemy.engine.base.Engine:
    """
    Inicializa y devuelve un pool de conexiones a Cloud SQL de forma segura y eficiente.
    Reutiliza el pool si ya ha sido creado para mejorar el rendimiento.
    """
    global db_pool
    if db_pool:
        return db_pool

    from google.cloud.sql.connector import Connector
    connector = Connector()

    def getconn() -> "pg8000.dbapi.Connection":
        conn = connector.connect(
            settings.DB_CONNECTION_NAME,
            "pg8000",
            user=settings.DB_USER,
            password=settings.DB_PASS,
            db=settings.DB_NAME,
            ip_type="PRIVATE"
        )
        return conn

    db_pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
    return db_pool

def obtener_rol_usuario(user_email: str) -> tuple[str, str]:
    """Consulta PostgreSQL para obtener el rol y departamento de un usuario."""
    db = get_db_connection()
    with db.connect() as conn:
        query = text("SELECT role, department FROM roles_usuarios WHERE user_email = :email LIMIT 1")
        result = conn.execute(query, {"email": user_email}).fetchone()
        if result:
            return result.role, result.department
        return "user", None

def get_all_departments() -> list[str]:
    """Obtiene una lista única de todos los departamentos desde la tabla catálogo 'departments'."""
    db = get_db_connection()
    try:
        with db.connect() as conn:
            query = text("SELECT department_name FROM departments ORDER BY department_name ASC")
            results = conn.execute(query).fetchall()
            return [row.department_name for row in results]
    except Exception as e:
        print(f"🔴 Error al obtener la lista de departamentos: {e}")
        return []

def upsert_user(user_email: str, new_role: str, department_name: str, can_query_dwh: bool = False) -> str:
    """
    Inserta o actualiza un usuario (UPSERT), asegura que el departamento exista,
    y envía una notificación de bienvenida si es un usuario nuevo.
    """
    db = get_db_connection()
    allowed_roles = ['admin', 'lead', 'agent', 'user']
    if new_role not in allowed_roles:
        return f"Error: El rol '{new_role}' no es válido."

    try:
        user_name = " ".join([name.capitalize() for name in user_email.split('@')[0].split('.')])
    except Exception:
        user_name = user_email

    try:
        with db.connect() as conn:
            with conn.begin():
                user_exists_query = text("SELECT role FROM roles_usuarios WHERE user_email = :email")
                existing_user = conn.execute(user_exists_query, {"email": user_email}).fetchone()
                
                query_find_dept = text("SELECT department_name FROM departments WHERE department_name = :dept_name")
                exists = conn.execute(query_find_dept, {"dept_name": department_name}).fetchone()
                if not exists:
                    print(f"▶️ Creando nuevo departamento en el catálogo: {department_name}")
                    query_create_dept = text("INSERT INTO departments (department_name) VALUES (:dept_name) ON CONFLICT (department_name) DO NOTHING")
                    conn.execute(query_create_dept, {"dept_name": department_name})
                
                query_manage_user = text("""
                    INSERT INTO roles_usuarios (user_email, user_name, role, department, can_query_dwh)
                    VALUES (:email, :name, :role, :department, :can_query_dwh)
                    ON CONFLICT (user_email) DO UPDATE SET
                      user_name = EXCLUDED.user_name,
                      role = EXCLUDED.role,
                      department = EXCLUDED.department,
                      can_query_dwh = EXCLUDED.can_query_dwh;
                """)
                conn.execute(query_manage_user, {"email": user_email, "name": user_name, "role": new_role, "department": department_name,"can_query_dwh": can_query_dwh})

        if not existing_user:
            # CAMBIO: Se actualiza el asunto y cuerpo del correo con el nuevo nombre.
            asunto = "Bienvenido a GuanaCloud Platform - Tu Cuenta Ha Sido Configurada"
            cuerpo_html = f"""
            <html><body>
                <h2>¡Hola, {user_name}!</h2>
                <p>Se ha configurado tu acceso para la plataforma de soporte GuanaCloud Platform.</p>
                <ul>
                    <li><b>Email:</b> {user_email}</li>
                    <li><b>Rol Asignado:</b> {new_role.capitalize()}</li>
                    <li><b>Departamento:</b> {department_name}</li>
                </ul>
                <p>Ya puedes interactuar con el bot en Google Chat.</p>
            </body></html>
            """
            enviar_notificacion_email(user_email, asunto, cuerpo_html)
            print(f"✅ Nuevo usuario creado y notificación enviada a {user_email}")
            return f"Se ha creado exitosamente al usuario {user_email} y se le ha enviado un correo de notificación."
        else:
             print(f"✅ Usuario {user_email} actualizado.")
             return f"Se ha actualizado exitosamente a {user_email} con el rol '{new_role}' en el departamento '{department_name}'."
    except Exception as e:
        print(f"🔴 Error al gestionar el rol del usuario: {e}")
        return "Ocurrió un error al intentar actualizar la base de datos de roles."


def delete_user(user_email: str) -> str:
    """Elimina un usuario de la tabla de roles."""
    db = get_db_connection()
    try:
        with db.connect() as conn:
            with conn.begin():
                query = text("DELETE FROM roles_usuarios WHERE user_email = :email")
                result = conn.execute(query, {"email": user_email})
                
                if result.rowcount > 0:
                    print(f"✅ Usuario {user_email} eliminado del sistema.")
                    return f"El usuario {user_email} ha sido eliminado exitosamente."
                else:
                    print(f"⚠️  No se encontró al usuario {user_email} para eliminar.")
                    return f"No se encontró ningún usuario con el email {user_email}."
    except Exception as e:
        print(f"🔴 Error al eliminar usuario: {e}")
        return "Ocurrió un error al intentar eliminar al usuario de la base de datos."


def registrar_feedback(session_id: str, user_email: str, rating: int):
    """Inserta una nueva valoración en la tabla de feedback de PostgreSQL."""
    db = get_db_connection()
    with db.connect() as conn:
        with conn.begin():
            query = text("""
                INSERT INTO nps_feedback (session_id, user_email, rating)
                VALUES (:session_id, :user_email, :rating)
            """)
            conn.execute(query, {"session_id": session_id, "user_email": user_email, "rating": rating})
    print(f"✅ Feedback registrado para la sesión {session_id}.")

def actualizar_feedback_comentario(session_id: str, comment: str):
    """Actualiza el último feedback negativo con un comentario."""
    db = get_db_connection()
    with db.connect() as conn:
        with conn.begin():
            query = text("""
                UPDATE nps_feedback
                SET comment = :comment
                WHERE feedback_id = (
                    SELECT feedback_id FROM nps_feedback
                    WHERE session_id = :session_id AND rating = 0
                    ORDER BY timestamp DESC
                    LIMIT 1
                )
            """)
            conn.execute(query, {"comment": comment, "session_id": session_id})
    print(f"✅ Comentario de feedback actualizado para la sesión {session_id}.")

def get_asana_gid_for_user(user_email: str) -> str | None:
    """Consulta PostgreSQL para obtener el Asana GID de un usuario."""
    db = get_db_connection()
    try:
        with db.connect() as conn:
            query = text("SELECT asana_gid FROM roles_usuarios WHERE user_email = :email LIMIT 1")
            result = conn.execute(query, {"email": user_email}).scalar_one_or_none()
            return result
    except Exception as e:
        print(f"🔴 Error al obtener el Asana GID para {user_email}: {e}")
        return None

def check_dwh_permission(user_email: str) -> bool:
    """Verifica si un usuario tiene el permiso para consultar el DWH."""
    db = get_db_connection()
    try:
        with db.connect() as conn:
            query = text("SELECT can_query_dwh FROM roles_usuarios WHERE user_email = :email")
            result = conn.execute(query, {"email": user_email}).scalar_one_or_none()
            return result is True
    except Exception as e:
        print(f"🔴 Error al verificar el permiso de DWH para {user_email}: {e}")
        return False