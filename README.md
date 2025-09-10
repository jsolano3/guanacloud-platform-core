# ​ Kai (Knowledge & Assistance Interface): Plataforma Multi-Agente de Soporte Corporativo Connect

Una plataforma de **IA para soporte interno** , diseñada para automatizar procesos y elevar la eficiencia operativa.
</div>
<div align="center">
<img  alt="Kai" width="150"/>
<br>
<strong>Una plataforma de IA Multi-Agente para Soporte Corporativo</strong>
<br>
Diseñada para automatizar procesos, centralizar el conocimiento y elevar la eficiencia operativa mediante agentes de IA autónomos y especializados.
</div>
---

##  Índice
- [Visión de Negocio](#visión-de-negocio)  
- [Alcance y Funcionalidades](#alcance-y-funcionalidades)  
- [Visión Técnica](#visión-técnica)  
- [Infraestructura como Código](#infraestructura-como-código)
- [Metodología y Gobierno del Código](#metodología-y-gobierno-del-código)  
- [Estructura del Proyecto](#estructura-del-proyecto)  
- [Instalación y Despliegue](#instalación-y-despliegue)  
- [Uso y Ejemplos](#uso-y-ejemplos)  
- [Créditos](#créditos)

---

## Visión de proyecto

Kai es un asistente de IA de Nivel 1 que actúa como el primer punto de contacto para todas las solicitudes de soporte. Utiliza un motor de IA avanzado para ofrecer auto-servicio, gestionar tiquetes de forma inteligente y automatizar flujos de trabajo, liberando el potencial de los equipos humanos.

### 🚀 Funcionalidades Clave

🧠 Soporte Nivel 0 con Base de Conocimiento: Responde preguntas frecuentes al instante utilizando búsqueda semántica en una base de conocimiento vectorial (knowledge_service.py).

#### 🎟️ Gestión Inteligente de Tiquetes:

  **Creación y Razonamiento:** Analiza el lenguaje del usuario para determinar la prioridad y el equipo correcto (Data Engineering vs. BI) usando Gemini (logic.py).

  **Ciclo de Vida Completo:** Permite crear, consultar, cerrar, reasignar y modificar el SLA de los tiquetes (ticket_manager.py).

  **Control por Roles:** El sistema adapta las funcionalidades disponibles según el rol del usuario (user, agent, lead), validando permisos para cada acción (logic.py - tiene_permiso).

  **📊 Analíticas en Lenguaje Natural:** Los usuarios pueden hacer preguntas complejas sobre métricas de soporte (ej. "cuál fue el tiempo promedio de resolución la semana pasada"), que Kai convierte a consultas SQL y ejecuta en postgres (ticket_querier.py).

  **🖼️ Visualización Multimodal:** Genera infografías del historial de un tiquete (ticket_visualizer.py), convirtiendo datos tabulares en una línea de tiempo visual y fácil de entender.

#### 🔗 Integraciones Externas:

  **Asana:** Convierte tiquetes que son en realidad nuevas funcionalidades en tareas planificables directamente en Asana, asignándolas al líder de equipo correcto (asana_service.py).

   **Google Calendar:** Agenda reuniones de seguimiento, añadiendo automáticamente a los involucrados en el tiquete (ticket_manager.py).

  **🔔 Notificaciones Proactivas:** Mantiene a todos informados a través de notificaciones por Email (vía Brevo) y Google Chat para cada evento relevante (notification_service.py).

  **📈 Resúmenes Diarios Automatizados:** Un proceso programado (summary_task.py) envía resúmenes diarios a los administradores (agregados, por Chat) y a los usuarios (detallados, por Email) sobre el estado de los tiquetes abiertos.

---

## Alcance y Funcionalidades

Kai está construido sobre una arquitectura serverless y nativa de la nube en Google Cloud Platform, garantizando escalabilidad, resiliencia y eficiencia.


**Compute y Orquestación:** El backend es una aplicación Flask contenida en Docker y desplegada en Cloud Run, que sirve como el punto de entrada para los webhooks de Google Chat (main.py, Dockerfile).

  ### Capa de Inteligencia Artificial (Vertex AI):

  - **Modelo de Razonamiento:** Gemini 2.5 Flash es el cerebro principal para el chat, la toma de decisiones y el uso de herramientas (logic.py).

  - **Modelo de Tareas:** Gemini 2.5 Pro se utiliza para tareas más complejas como la generación de SQL a partir de lenguaje natural (ticket_querier.py).

  - **Embeddings:** El modelo text-embedding-005 convierte el texto de la base de conocimiento en vectores de 768 dimensiones (knowledge_service.py).

  - **Búsqueda Semántica:** Vertex AI Vector Search almacena y busca en los embeddings para encontrar respuestas relevantes.

  - **Generación de Imágenes:** El modelo Imagen crea las infografías de los flujos de tiquetes (ticket_visualizer.py).

  ### Base de Datos y Almacenamiento:

  - **Postgres:** Es la base de datos principal que almacena el historial de tiquetes, eventos, roles de usuario y configuración de SLAs (database_client.py).

 - **Firestore:** Se utiliza para gestionar la memoria conversacional y el estado de las sesiones de chat de los usuarios (memory_service.py).

 - **Cloud Storage:** Almacena los artefactos generados, como las infografías de los flujos de tiquetes.

  ### Automatización y Scheduling:

  - **Cloud Scheduler**: Dispara un job diario que invoca un endpoint protegido en Cloud Run (`/run-summary`) para ejecutar la tarea de envío de resúmenes.

---

## Infraestructura como Código

Toda la infraestructura de Google Cloud para este proyecto (Cloud Run, Cloud SQL, IAM, Secret Manager, etc.) está definida y gestionada como código utilizando **Terraform**. Esto garantiza la repetibilidad, el control de versiones y la portabilidad de la plataforma. Los archivos de configuración se encuentran en el directorio `terraform/`. El estado de la infraestructura se almacena en el archivo `terraform.tfstate`.

---


## Metodología y Gobierno del Código

- **Metodología Agile (Scrum)**:
  - Sprints de 2 semanas, con daily, planning, revisión y demo.  
  - Backlog gestionado en Asana.

- **Git Flow**:
  - `main`: producción.  
  - `develop`: integración continua.  
  - `feature/<name>`: nuevas funcionalidades.  
  - `hotfix/<name>`: correcciones urgentes.

- **Estilo de Código**:
  - Python 3.12, con formateo automatizado (`black`, `isort`) y lint (`flake8`).  
  - Nomenclatura:
    - `snake_case` para funciones/variables  
    - `PascalCase` para clases  
    - `UPPER_SNAKE_CASE` para constantes

---

## Estructura del Proyecto

```bash

kai-core-api/
├── .github/workflows/        # Workflows de CI/CD
│   └── deploy.yml
├── terraform/                # Infra como codigo (IaC)
│   ├── main.tf
│   ├── variable.tf
│   ├── secrets.tf
│   ├── iam.tf
│   ├── import.sh
│   ├── output.tf
├── src/
│   ├── prompts/              # Prompts de todos los procesos
│   │   ├── generate_sql_from_nl.md
│   │   ├── generate_timeline_infographic.md
│   │   ├── github_dataform_review.md
│   │   ├── github_lookml_review.md
│   │   ├── rag_classify_document.md
│   │   ├── rag_final_answer.md
│   │   ├── summarize_document.md
│   │   ├── system_prompt.md
│   ├── services/              # Lógica de negocio y conexión a servicios externos
│   │   ├── asana_service.py
│   │   ├── admin_service.py
│   │   ├── calendar_service.py
│   │   ├── knowledge_service.py
│   │   ├── github_service.py
│   │   ├── looker_service.py
│   │   ├── memory_service.py
│   │   ├── notification_service.py
│   │   ├── query_service.py
│   │   ├── ticket_manager.py
│   │   └── ticket_visualizer.py
│   ├── tasks/                 # Tareas programadas (ej. resúmenes diarios)
│   │   └── summary_task.py
│   ├── tools/
│   │   ├── create_kb_index.py # Definiciones de herramientas para la IA
│   │   └── tool_definitions.py
│   ├── utils/
│   │   ├── prompt_loader.py   # Clientes y funciones de utilidad
│   │   └── database_client.py
│   ├── config.py              # Carga de configuración
│   └── logic.py               # Orquestador principal de la lógica del agente
├── .env                       # Variables de entorno (no versionado)
├── Dockerfile                 # Definición del contenedor
├── main.py                    # Punto de entrada de la aplicación Flask
└── requirements.txt           # Dependencias de Python
  
```


- **services/**: lógica externa (Asana, KB, notificaciones).  
- **tasks/**: scripts para resúmenes programados.  
- **tools/**: herramientas disponibles para el modelo IA.  
- **utils/**: utilidades reutilizables (p. ej. cliente Postgres).

---

## Instalación y Despliegue

El despliegue es un proceso de dos etapas: provisionar la infraestructura con Terraform (en caso de un proyecto nuevo) 
y luego desplegar el código de la aplicación con GitHub Actions.

1. Provisionar Infraestructura con Terraform:

```bash
cd terraform
terraform init
terraform apply
```

Ejecuta terraform apply y proporciona los valores para las variables requeridas (como gcp_project_id y las contraseñas de la base de datos).

2. El repositorio está configurado con GitHub Actions para CI/CD.
  
  Clona el repositorio:

   ```bash
   git clone https://github.com/Connect-Assistance/kai-core-api.git
   cd kai_core_api
   ```
   
3. Configura variables

 Para entorno local en .env, y para cloud run credeciales en secret manager y varibales en deploy.yml.

` env
GEMINI_CHAT_MODEL="gemini-2.5-flash"
GEMINI_TASK_MODEL="gemini-2.5-PRO"
IMAGEN_MODEL="imagen-4.0-generate-001"
EMBEDDING_MODEL_NAME="text-embedding-005"
GOOGLE_CHAT_WEBHOOK_URL="https://chat.googleapis.com/....."
GCS_BUCKET_NAME="dex-helpdesk-flujos"
BREVO_API_KEY="xsmtpsib-......"
ASANA_PERSONAL_ACCESS_TOKEN="2/12086949524531......."
ASANA_PROJECT_GID="1204402129492806"
ASANA_LEAD_DATA_ENGINEERING_GID="1200014366404278"
#ASANA_LEAD_TI_GID="1205224117672129"
ASANA_LEAD_BI_ANALYST_GID="1205224117672129"
`

4. Despliega usando Cloud Run:

 - Un push a la rama develop desplegará automáticamente en el entorno de desarrollo de Cloud Run.
 - Un Pull Request de develop a main (una vez aprobado y fusionado) desplegará en el entorno de producción.

```bash
githubActions
```

## Uso y Ejemplos

### Interactúa con Kai en Google Chat:

**Base de Conocimiento:**
“¿Cómo puedo solicitar acceso a los dashboards de Looker?”

**Crear Tiquete:**
“Hola, tengo un problema con el pipeline de ventas.”

**Consultar estado:**
“¿Cuál es el estado del tiquete KAI-20250826-1FA8?”

**Convertir a Tarea:**
“El tiquete KAI-123 es una nueva funcionalidad. Conviértelo a tarea.”

**Agendar Reunión:**
“Sí, por favor, agenda la reunión con hola.test@connect.inc”

**Visualizar Historial:**
“Muéstrame el flujo completo del tiquete KAI-20250826-1FA8.”