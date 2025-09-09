# Chat History Service API

This service manages user chat histories for the DrChat backend.


## Neo4j Database Schama

### Nodes:
    - User:
      - id: Id unico para un usuario
    - Session:
      - id: Id unico para una sesion (chat)
      - name: Nombre de la sesion (chat)
      - createdAt: Tiempo en el que se inserta en la Base de Datos
    - Message:
      - content: texto del mensaje
      - type: ai o user
      - createdAt: Tiempo en el que fue creado
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
{
  "sessions": [
    {
      "session_id": "1",
      "session_name": "Chat 1",
      "session_created_at": "2025-09-09T14:45:22.664585",
      "messages": [
        {
          "content": "What is sle",
          "role": "user",
          "created_at": "2025-09-09T14:48:24.832157"
        },
        {
          "content": "The provided context does not mention SLE (Systemic Lupus Erythematosus). Therefore, I cannot provide an accurate answer based on the given information.\n\nHowever, I can provide a general definition: Systemic Lupus Erythematosus (SLE) is a chronic autoimmune disease that can affect various parts of the body, including the skin, joints, kidneys, brain, and other organs. If you would like more information on SLE, I can try to provide a more detailed response.",
          "role": "ai",
          "created_at": "2025-09-09T14:48:33.396767"
        },
        {
          "content": "How many participants were included in the final analysis of the study, and what were the main exclusion criteria?",
          "role": "user",
          "created_at": "2025-09-09T14:49:30.176539"
        },
        {
          "content": "According to the context, the study included 5,221 participants with complete information in the final analysis.\n\nThe main exclusion criteria were:\n1. Participants under 20 years old and pregnant women (N = 31,152)\n2. Those with missing data on heavy metals (N = 26,855)\n3. Those with incomplete data on TyG, WWI, eGFR, and CKM (N = 6,962) \n\nReference: \nPage 2 of Document: fnut-12-1613721.",
          "role": "ai",
          "created_at": "2025-09-09T14:49:34.298211"
        },
        {
          "content": "What is CKM?",
          "role": "user",
          "created_at": "2025-09-09T14:50:36.049965"
        },
        {
          "content": "CKM stands for Cardiovascular-kidney-metabolic syndrome. It is a recently defined clinical syndrome that integrates the interactions between:\n\n1. Cardiovascular disease (CVD)\n2. Chronic kidney disease (CKD)\n3. Metabolic disorders, such as:\n\t* Diabetes\n\t* Obesity\n\t* Hypertension\n\t* Dyslipidemia\n\t* Hyperglycemia\n\nThe American Heart Association (AHA) has proposed a staging system for CKM, ranging from stage 0 (no risk factors) to stage 4 (established CVD with or without renal failure).\n\nReference: Document fnut-12-1613721, Page 2.",
          "role": "ai",
          "created_at": "2025-09-09T14:50:40.140373"
        }
      ]
    },
    {
      "session_id": "2",
      "session_name": "Chat 2",
      "session_created_at": "2025-09-09T15:02:47.26321",
      "messages": [
        {
          "content": "What is CKM?",
          "role": "user",
          "created_at": "2025-09-09T15:03:06.646667"
        },
        {
          "content": "CKM stands for Cardiovascular-kidney-metabolic syndrome. It is a recently defined clinical syndrome that integrates the interactions between:\n\n1. Cardiovascular disease (CVD)\n2. Chronic kidney disease (CKD)\n3. Metabolic disorders such as diabetes and obesity.\n\nThe American Heart Association (AHA) has proposed a staging system for CKM, ranging from stage 0 (no risk factors) to stage 4 (established CVD with or without renal failure). \n\nSource: Document fnut-12-1613721, Page 2.",
          "role": "ai",
          "created_at": "2025-09-09T15:03:13.465476"
        },
        {
          "content": "What is CVD?",
          "role": "user",
          "created_at": "2025-09-09T15:03:30.767631"
        },
        {
          "content": "CVD stands for Cardiovascular Disease. It is one of the primary components of the Cardiovascular-kidney-metabolic (CKM) syndrome, which also includes chronic kidney disease (CKD), diabetes, obesity, and hypertension. \n\nAccording to the provided context, the prevalence rates of CVD, diabetes, and CKD in China are 23.4%, 11.2%, and 10.8%, respectively (Document fnut-12-1613721, Page 8). \n\nNo further specific definition of CVD is provided in the context.",
          "role": "ai",
          "created_at": "2025-09-09T15:03:34.804743"
        }
      ]
    }
  ]
}
```

#### Errors

- 500 Internal Server Error
- 404 Usuario o Sesion no encontrados para el usuario dado