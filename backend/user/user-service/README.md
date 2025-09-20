# User Service (Auth)

Servicio de autenticación para registro e ingreso de usuarios.  
Expone endpoints REST vía **FastAPI** y persiste usuarios en **PostgreSQL**.  
Integra **Firebase Admin** para enviar correos de verificación de cuenta al registrarse.

- Puerto por defecto: `5002`
- Base path: `/api`
- Endpoints principales:
  - `POST /api/register` → registra usuario y envía email de verificación
  - `POST /api/login` → autentica usuario con email y contraseña

---

## 🔐 Manejo de contraseñas

- Se usa [`passlib`](https://passlib.readthedocs.io/) con **bcrypt** para generar un **hash seguro** antes de persistir en la base de datos.
- El hash se guarda en la columna `password` (tipo `VARCHAR(255)` o `TEXT`) 

## 📧 Verificación de correo

- Al registrar un usuario se genera un **link de verificación** con **Firebase Admin** y se envía vía **Resend**.
- No se guarda ni se envía la contraseña a Firebase.
- Si las variables de Firebase no están configuradas, el registro funciona pero no se enviará el correo.


## Correr con Docker Compose (recomendado)

Prerequisitos: Docker y Docker Compose.

Comandos útiles desde la raíz del repo:

- Levantar solo DB + user-service (build incluido):
  ```bash
  docker compose up -d --build db user-service
  ```
- Ver logs:
  ```bash
  docker compose logs -f db user-service
  ```
- Reiniciar user-service después de cambios:
  ```bash
  docker compose up -d --build user-service
  ```
- Apagar (conservar datos de la DB mediante volumen `pgdata`):
  ```bash
  docker compose down
  ```
- Apagar y borrar datos persistidos:
  ```bash
  docker compose down -v
  ```

Notas:
- El servicio de Postgres (`db`) NO expone el puerto 5432 al host; los contenedores se comunican por la red interna usando el hostname `db`.
- La URL de conexión por defecto del user-service es `postgresql+psycopg://app:secret@db:5432/drchat` (se puede sobreescribir con `DATABASE_URL`).
- El `docker-compose.yml` en la raíz del proyecto define además contenedores para frontend, chat-service y chat-history-service; podés levantar todo con:
  ```bash
  docker compose up -d --build
  ```
  (Verificá que tus `.env` estén completos para cada servicio.)

## Variables de entorno

- `DATABASE_URL` (opcional): cadena SQLAlchemy hacia Postgres.
  - Default interno: `postgresql+psycopg://app:secret@db:5432/drchat`
- **Integración Firebase** (opcional):
  - `GOOGLE_APPLICATION_CREDENTIALS`: ruta dentro del contenedor a las credenciales del Service Account.
  - `FIREBASE_WEB_API_KEY`: API key del proyecto Firebase (se usa para el flujo REST `signInWithPassword` + `sendOobCode`).
  - En Docker, montar el JSON del Service Account y exponer las variables en `user-service`.
  - Si no se configuran estas variables, el servicio sigue funcionando pero no se enviará la verificación por correo.

## Endpoints

- Registro
  - `POST /api/register`
  - Body JSON:
    ```json
    {
      "name": "Ana",
      "email": "ana@test.com",
      "password": "123456",
      "profesion": "medicina"
    }
    ```
  - Respuesta 200:
    ```json
    { "name": "Ana", "email": "ana@test.com", "token": "token-ana@test.com" }
    ```

- Login
  - `POST /api/login`
  - Body JSON:
    ```json
    { "email": "ana@test.com", "password": "123456" }
    ```
  - Respuesta 200:
    ```json
    { "name": "Ana", "email": "ana@test.com", "token": "token-ana@test.com" }
    ```

## Probar rápido con curl

```bash
# Registro
curl -X POST http://localhost:5002/api/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ana","email":"ana@test.com","password":"123456","profesion":"medicina"}'

# Login
curl -X POST http://localhost:5002/api/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@test.com","password":"123456"}'
```

## Correr local (sin Docker)

Dentro de `backend/user/user-service`:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
# Opcional: export DATABASE_URL si no usás Docker para la DB
uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```