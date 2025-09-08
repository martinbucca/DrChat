# Chat History Service API

This service manages user chat histories for the DrChat backend.


## Neo4j Database Schama

### Nodes:
    - User:
      - id: Id unico para un usuario
    - Session:
      - id: Id unico para una sesion (chat)
      - name: Nombre de la sesion (chat)
      - created_at: Tiempo en el que se inserta en la Base de Datos
    - Message:
      - content
      - type
### Relationships:
    - (User)-[HAS_SESSION]->(Session)
    - (Session)-[LAST_MESSAGE]->(Message)
    - (Message)-[NEXT]->(Message)

## Endpoints

### 1. Create new Session/Chat

- **POST** `/session`
- **Description:** Creates a new session with a specific name in the Database for a specific user.

#### Body 

```json
{
  "user_id": "string",
  "session_id": "string",
  "session_name": "string"
}
```

#### Response

```json
{
  "session_id": "4",
  "created_at": "2025-09-07T23:44:34.516319",
  "message": "Sesión creada exitosamente"
}
```

#### Errors

- 500 Internal Server Error
- 400 Session ID already exists

---

### 2. Delete Session/Chat

- **DELETE** `/session`
- **Description:** Deletes a Session/chat and all the messages related to it

#### Body 

```json
{
  "user_id": "string",
  "session_id": "string"
}
```

#### Response

```json
{
    "session_id": "session_id",
    "message": "Sesión y mensajes asociados eliminados exitosamente"
}
```

#### Errors

- 500 Internal Server Error
- 404 Usuario o Sesion no encontrados para el usuario dado

---

### 3. Update Session/Chat name

- **PUT** `/session`
- **Description:** Updates a Session/chat name

#### Body 

```json
{
  "user_id": "string",
  "session_id": "string",
  "new_name": "string"
}
```

#### Response

```json
{
    "session_id": "session_id",
    "session_name": "session_name"
}
```

#### Errors

- 500 Internal Server Error
- 400 El nuevo nombre de la sesión no puede estar vacío
- 404 Usuario o Sesion no encontrados para el usuario dado

---

### 4. Get Sessions/Chats For User

- **GET** `/sessions`
- **Description:** Returns all the sessions with its name and creation time and all the messages associated with each session

#### Body 

```json
{
  "user_id": "string",
}
```

#### Response

```json
```

#### Errors

- 500 Internal Server Error
- 404 Usuario o Sesion no encontrados para el usuario dado