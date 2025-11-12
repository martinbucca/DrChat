<h1 align="center">DrChat</h1>

<p align="center">
  <img src="frontend/public/DrChat.png" alt="DrChat Logo" width="200"/>
</p>

---

### 🩺 Descripción del Proyecto

**DrChat** es un chatbot médico inteligente que procesa documentos en formato **PDF** y permite a los usuarios interactuar mediante un sistema de **preguntas y respuestas** basado en la información contenida en dichos documentos.  

**DrChat** permite a los usuarios interactuar con un chatbot médico capaz de comprender el contenido de documentos clínicos y científicos.  
El sistema analiza la información contenida en los archivos y construye una base de conocimiento que le permite ofrecer respuestas más ricas y fundamentadas.  

Entre sus principales características se destacan:
- 💬 **Conversación contextual**: el chatbot mantiene el contexto de la conversación, permitiendo hacer preguntas relacionadas con respuestas anteriores.  
- 🧠 **Comprensión de documentos**: interpreta el contenido médico y científico para responder preguntas basadas en la información real de los textos.  
- 🔍 **Respuestas con fundamento**: cada respuesta se apoya en las fuentes originales, ofreciendo transparencia y trazabilidad.  
- 🧩 **Exploración del conocimiento**: permite descubrir conceptos y relaciones entre entidades médicas, facilitando la investigación y el aprendizaje.  
- ⚡ **Búsqueda inteligente**: utiliza razonamiento semántico para encontrar información relevante incluso cuando las preguntas no coinciden textualmente con el contenido.  

Estas funciones convierten a **DrChat** en una herramienta útil para **profesionales de la salud, estudiantes e investigadores**, ayudándolos a explorar y comprender grandes volúmenes de información médica de forma simple e interactiva.


El sistema está diseñado para asistir a **profesionales de la salud, investigadores y estudiantes** en la exploración y comprensión de grandes volúmenes de información médica no estructurada.

Podés acceder a la aplicación en 👉 **[dr-chat.app](https://dr-chat.app)**  

---

### 🎓 Contexto Académico

Este proyecto fue desarrollado en el marco del **Trabajo Profesional de la carrera de Ingeniería en Informática** de la **Universidad de Buenos Aires (UBA)**.  
Combina técnicas de **Procesamiento de Lenguaje Natural (NLP)**, **bases de datos en grafo** y **modelos de lenguaje (LLMs)** para demostrar el potencial de la integración entre inteligencia artificial y sistemas de conocimiento estructurado.

---

### ⚙️ Tecnologías Principales

- **Python** – Backend y procesamiento de documentos  
- **Neo4j** – Almacenamiento y consulta del grafo de conocimiento  
- **LangChain / GraphRAG** – Recuperación y generación aumentada por grafo  
- **React / Next.js** – Frontend interactivo  
- **Docker** – Contenedorización del entorno  




---

## 📋 Prerrequisitos

- **Docker** y **Docker Compose** instalados
- **Make** (opcional, para usar comandos simplificados)
- Claves de API configuradas para:
  - Azure OpenAI (embeddings)
  - Unstructured API (procesamiento de PDFs)

---

## 🚀 Guía de inicio rápido

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd DrChat
```

### 2. Configurar variables de entorno
```bash
# Copiar archivos de configuración
cp .env.example .env
cp frontend/.env.example frontend/.env

# Editar los archivos .env con tus configuraciones específicas
# - .env: Configuración para todos los servicios backend
# - frontend/.env: Configuración específica del frontend
```

### 3. Levantar el proyecto

#### Usando Makefile (recomendado):
```bash
# Ver todos los comandos disponibles
make help

# Buildear todo el proyecto
make build

# Levantar proyecto completo con bases de datos locales
make up

# Levantar con Neo4j externo (configurar NEO4J_URI en .env)
make up-external-neo4j

# Levantar con PostgreSQL externo (configurar POSTGRES_* en .env)
make up-external-postgres

# Levantar con bases de datos externas
make up-external

# Ver estado de contenedores
make status

# Ver logs de servicios principales
make logs

# Detener proyecto
make down
```

### 4. Acceso a los servicios

Una vez que los servicios estén ejecutándose:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interfaz web de DrChat |
| **File Service** | http://localhost:8001/docs | API de gestión de archivos (Swagger) |
| **File Service Health Check** | http://localhost:8001/ | Estado del file-service |
| **Chat Service** | http://localhost:8002/docs | API de chat (Swagger) |
| **Chat History Service** | http://localhost:8003/docs | API de historial de chat (Swagger) |
| **User Service** | http://localhost:8004/docs | API de usuarios (Swagger) |
| **Neo4j Browser** | http://localhost:7474 | Interfaz web de Neo4j (usuario: neo4j, contraseña: password) |
| **PostgreSQL** | localhost:5432 | Base de datos relacional (acceso directo) |
| **Kafka** | localhost:9092 | Broker de mensajes |

---

## 📋 Configuración de Variables de Entorno

El proyecto utiliza una configuración simplificada con solo **dos archivos** de variables de entorno:

### **Archivo Principal (`.env`)**
Contiene toda la configuración para los servicios backend y base de datos:

| Variable                        | Descripción                                                                |
|---------------------------------|----------------------------------------------------------------------------|
| **Base de Datos**               |                                                                            |
| `NEO4J_URI`                     | URI de conexión para Neo4j (ej: `bolt://neo4j:7687`)                       |
| `NEO4J_USERNAME`                | Usuario para autenticación en Neo4j                                        |
| `NEO4J_PASSWORD`                | Contraseña para autenticación en Neo4j                                     |
| `POSTGRES_HOST`                 | Host de PostgreSQL (ej: `postgres`)                                        |
| `POSTGRES_PORT`                 | Puerto de PostgreSQL (ej: `5432`)                                          |
| `POSTGRES_USER`                 | Usuario de PostgreSQL                                                      |
| `POSTGRES_PASSWORD`             | Contraseña de PostgreSQL                                                   |
| `POSTGRES_DB`                   | Nombre de la base de datos PostgreSQL                                      |
| **Kafka**                       |                                                                            |
| `KAFKA_BOOTSTRAP_SERVERS`       | Servidores de Kafka (ej: `kafka:29092`)                                    |
| `KAFKA_FILE_UPLOAD_TOPIC`       | Tópico de Kafka para eventos de archivos                                   |
| `KAFKA_GROUP_ID`                | ID del grupo de consumidores Kafka                                         |
| **URLs de Servicios**           |                                                                            |
| `FILE_SERVICE_URL`              | URL del servicio de archivos                                               |
| `CHAT_SERVICE_URL`              | URL del servicio de chat                                                   |
| `CHAT_HISTORY_SERVICE_URL`      | URL del servicio de historial de chat                                      |
| `USER_SERVICE_URL`              | URL del servicio de usuarios                                               |
| **IA/ML**                       |                                                                            |
| `AZURE_OPENAI_API_KEY`          | API Key para Azure OpenAI                                                  |
| `AZURE_OPENAI_API_VERSION`      | Versión de la API de Azure OpenAI                                          |
| `AZURE_OPENAI_ENDPOINT`         | Endpoint de Azure OpenAI                                                   |
| `AZURE_OPENAI_EMBEDDINGS_MODEL` | Modelo de embeddings de Azure OpenAI                                       |
| `LLM_CHAT_MODEL`                | Modelo de chat del LLM                                                     |
| `GROQ_API_BASE`                 | URL base de la API de Groq                                                 |
| `GROQ_API_KEY`                  | API Key para Groq                                                          |
| **Procesamiento de Documentos** |                                                                            |
| `UNSTRUCTURED_API_KEY`          | API Key para el servicio Unstructured                                      |
| `UNSTRUCTURED_URL`              | URL del servicio Unstructured                                              |
| `VECTOR_INDEX_NAME`             | Nombre del índice vectorial en Neo4j                                       |
| `FULLTEXT_INDEX_NAME`           | Nombre del índice de texto completo en Neo4j                               |
| **Almacenamiento y Logs**       |                                                                            |
| `STORAGE_DIR`                   | Directorio de almacenamiento de archivos                                   |
| `LOG_LEVEL`                     | Nivel de logging (INFO, DEBUG, ERROR)                                      |
| **Autenticación**               |                                                                            |
| `FIREBASE_WEB_API_KEY`          | API Key de Firebase                                                        |
| `GOOGLE_APPLICATION_CREDENTIALS`| Ruta al archivo de credenciales de Firebase                                |

### **Archivo Frontend (`frontend/.env`)**
Contiene la configuración específica del frontend:

| Variable                | Descripción                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `VITE_CHAT_SERVICE_URL` | URL del servicio de chat (ej: `http://localhost:8004`)                      |
| `VITE_USER_SERVICE_URL` | URL del servicio de usuarios (ej: `http://localhost:8001`)                  |
| `VITE_FILE_SERVICE_URL` | URL del servicio de archivos (ej: `http://localhost:8003`)                  |

---

## 🗺️ Diagrama de arquitectura

![Diagrama de arquitectura](img/diagrama-arquitectura.png)
