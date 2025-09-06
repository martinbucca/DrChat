# User Service (Auth)

Servicio de autenticación mínimo para registro e ingreso de usuarios. Expone endpoints REST vía FastAPI y persiste en PostgreSQL.

- Puerto: `5002`
- Base path: `/api`
- Endpoints:
  - `POST /api/register` → registra usuario
  - `POST /api/login` → autentica usuario

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

## Variables de entorno

- `DATABASE_URL` (opcional): cadena SQLAlchemy hacia Postgres.
  - Default interno: `postgresql+psycopg://app:secret@db:5432/drchat`

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

## Seguridad

Este flujo es básico para desarrollo: el “token” es un placeholder y no se valida en otros servicios. Para producción, reemplazar por JWT u otro esquema, guardar tokens en cookies `httpOnly` y validar en cada request de backend.

