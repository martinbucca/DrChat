# Chat Service

![GraphRAG Architecture](img/graphrag-architecture.png)

This service uses the **GraphRAG** pattern to answer user questions. GraphRAG (Graph Retrieval-Augmented Generation) combines graph-based retrieval with generative AI to provide more accurate and context-aware responses.

**How GraphRAG Works:**
- User questions are received by the service.
- The system retrieves relevant information from a knowledge graph, which organizes data as interconnected entities and relationships.
- Retrieved context is passed to a language model, which generates a natural language answer using both the question and the graph-derived information.
- The response includes both the generated answer and the supporting retriever result from the knowledge graph.

This approach ensures that answers are grounded in structured knowledge, improving reliability and traceability.

This service provides a simple chat endpoint for user interactions. It is designed to handle chat messages and return responses, forming the backend for chat-based applications.

## Purpose

The Chat Service processes user messages and generates appropriate responses. It is intended to be used as a backend component for applications requiring chat functionality.

## Running with Docker

1. **Build the Docker image:**
    ```sh
    docker build -t chat-service .
    ```

2. **Run the container:**
    ```sh
    docker run -p 8000:8000 chat-service
    ```

    This will start the service on port `8000`.

## Running With python
1. **Create virtual env**
    ```sh
    python -m venv venv
    ```
2. **Activate virtual env**
    ```sh
    venv/Scripts/activate
    ```
3. **Install requirements**
    ```sh
    pip install -r requirements.txt
    ```
4. **Run main script**
  - Try:
      ```sh
      cd app
      python main.py
      ```
  - Or in chat-service dir:
      ```sh
      python -m app.main
      ```



## API Endpoint

### `POST /answer_question`

### Backend running on http://localhost:5001

- **Description:** Accepts a question and an optional session ID, returning an answer and retriever result (information retrieved to answer question)
- **Request Body:**
  ```json
  {
     "query": "How many participants were included in the final analysis of the study, and what were the main exclusion criteria?",
     "session_id": "optional-session-id",
     "created_at": "2025-09-09T15:03:34.804743"
  }
  ```
- **Response:**
  ```json
  {
    "answer": "The study included 5,221 participants with complete information in the final analysis.\n\nThe main exclusion criteria were:\n1. Participants under 20 years old and pregnant women (n = 31,152)\n2. Those with missing data on heavy metals (n = 26,855)\n3. Those with incomplete data on TyG, WWI, eGFR, and CKM (n = 6,962)\n\nSource: Document fnut-12-1613721, Page 2 and 4.",
    "retriever_result": [
      {
        "listIds": [
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:704",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:635",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:638",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:645"
        ]
      },
      {
        "listIds": [
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:576",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:638",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:644",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:645"
        ]
      },
      {
        "listIds": [
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:777",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:638",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:644",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:645"
        ]
      },
      {
        "listIds": [
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:696",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:568",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:631",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:632",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:633",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:635",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:638",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:639",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:642",
          "4:479e412b-48e2-4f68-9289-c98d5dcdb59c:645"
        ]
      }
    ],
    "answer_created_at": "2025-09-09T15:41:06.743381"
  }
  ```

- **Example cURL Call:**
  ```sh
  curl -X POST http://localhost:5001/answer_question \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the capital of France?", "session_id": "optional-session-id"}'
  ```

- **Returns:** A JSON object containing the answer and retriever result.

- **Use FastAPI Swagger UI**

1. `http://localhost:5001/docs`
2. `Try Out` al endpoint POST /answer_question
