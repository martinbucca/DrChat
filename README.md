# DrChat

Chatbot médico que procesa documentos PDF y permite a los usuarios interactuar con un sistema de preguntas y respuestas basado en la información contenida en dichos documentos.

Los archivos PDF pueden ser cargados via endpoint por administradores para alimentar el grafo base de conocimiento del sistema o ser enviados por los usuarios a través del frontend. En caso de ser enviados por los usuarios, los nodos generados incluirán un `chat_id` para asociar el documento a un chat específico. El sistema procesa los documentos, extrae entidades y relaciones, y permite a los usuarios realizar consultas sobre la información contenida en ellos.

---

## 🔧 Variables de entorno

A continuación se listan las variables de entorno necesarias para el correcto funcionamiento del proyecto:

| Variable                | Descripción                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `TOKENIZERS_PARALLELISM`| Controla el paralelismo en el procesamiento de tokenizadores (NLP).         |
| `GROQ_API_KEY`          | API Key para acceder a servicios de Groq (modelos de lenguaje).             |
| `NEO4J_URI`             | URI de conexión para la base de datos Neo4j.                                |
| `NEO4J_USERNAME`        | Usuario para autenticación en Neo4j.                                        |
| `NEO4J_PASSWORD`        | Contraseña para autenticación en Neo4j.                                     |
| `NEO4J_DATABASE`        | Nombre de la base de datos utilizada en Neo4j.                              |

---

## 🌐 **Frontend**

El frontend está desarrollado en React y se comunica con el backend a través de los endpoints expuestos por los microservicios. Permite a los usuarios interactuar con el sistema, enviar mensajes y recibir respuestas basadas en la información procesada.

---

## 🛠️ **Backend**

El backend está dividido en tres módulos principales: **Ingestion**, **Pipeline** y **User**. Cada módulo contiene microservicios y workers que interactúan entre sí a través de apis REST y Kafka.

### 📦 **Ingestion**

#### `file-service`
**Descripción:**  
👉 Microservicio que se encarga de recibir archivos PDF, guardarlos en la carpeta `storage` y publicar un mensaje en Kafka indicando que el archivo está listo para ser procesado. Además, se conecta a MongoDB (colección: `files`) donde mantiene el estado del archivo, que puede ser `pending`, `processing`, `processed` o `error`. Analizar que se debe hacer en caso de falla al procesar algún documento.

**Endpoints:**
- `POST /files/upload`: Recibe un archivo PDF y lo guarda en el sistema. Debe también poder recibir un chat_id opcional para asociar el archivo a un chat específico
- `GET /files/{file_id}`: Obtiene el estado del archivo por su ID
- `PUT /files/{file_id}/status`: Actualiza el estado del archivo (por ejemplo, de `pending` a `processing` o `processed`).

---

### 🔄 **Pipeline**

#### `document-processor-worker`
**Descripción:**  
👉 Worker que consume los mensajes publicados por el `file-service`, accede al archivo PDF correspondiente y lo divide en chunks. Procesa en paralelo cada uno y extrae entidades y relaciones para cargar en la base Neo4J. Además le solicita al `file-service` actualizar el estado a `processing` cuando empieza y a `processed` cuando termina.

---

### 👤 **User**

#### `chat-service`
**Descripción:**  
👉 Microservicio encargado de recibir los mensajes de los usuarios y almacenarlos en una colección de MongoDB (`chats`). Para responder, se comunica con el `retriever-service`, que obtiene el contexto y genera la respuesta.

**Endpoints:**
- `POST /chat/send`: Recibe un mensaje de usuario, lo almacena y responde. En la respuesta se incluye el ID del chat.
- `GET /chat/{chat_id}`: Obtiene el historial de mensajes de un chat por su ID.
- `GET /chat/{chat_id}/last`: Obtiene el último mensaje de un chat.

#### `retriever-service`
**Descripción:**  
👉 Microservicio encargado de recibir solicitudes de contexto desde el `chat-service`. Realiza consultas sobre el grafo en Neo4j para recuperar información contextual y relevante para la respuesta del chat.

**Endpoints:**
- `POST /retriever/context`: Recibe el mensaje y el `chat_id`, realiza la consulta en Neo4j, y devuelve el contexto necesario para la respuesta.
