## Running:
1. **Create and complete .env file using .env.example as reference**
    ```
    VITE_OPENAI_API_KEY=""
    VITE_NEO4J_URI=""
    VITE_NEO4J_USERNAME=""
    VITE_NEO4J_PASSWORD=""
    VITE_BACKEND_URL=""
    VITE_USER_API_URL=""
    VITE_FILE_SERVICE_URL=""
    VITE_CHAT_HISTORY_SERVICE_URL=""
    ```

2. Run the frontend
    ```shell
    yarn install
    yarn run dev
    ```

### Running with Docker:

1. Build image
    ```shell
    docker build -t frontend:dev .
    ```

2. Run container
    ```shell
    docker run -it --rm \
    -p 5173:5173 \
    --env-file .env \
    -v $(pwd):/app \
    -v /app/node_modules \
    frontend:dev
    ```


## Documentation

The full documentation of every templates and components is available [here](https://neo4j.com/labs/neo4j-needle-starterkit/)
