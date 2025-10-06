import os
import time
import uuid
from neo4j import GraphDatabase
import requests
import pandas as pd
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_SERVICE_BASE_URL = "http://localhost:8001"
REGISTER_URL = "http://localhost:8004/api/register"
SESSION_URL = "http://localhost:8003/session"
ANSWER_QUESTION = "http://localhost:8002/answer_question"
VITE_NEO4J_URI="bolt://localhost:7687"
VITE_NEO4J_USERNAME="neo4j"
VITE_NEO4J_PASSWORD="password"


payload_register = {
    "email": "email@email.com",
    "name": "name",
    "password": "password",
    "profesion": "estudiante"
}
response = requests.post(REGISTER_URL, json=payload_register)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())


payload_session = {
    "user_id": "email@email.com",
    "session_id": str(uuid.uuid4()), 
    "session_name": "Test Chat"
}
response = requests.post(SESSION_URL, json=payload_session)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
session_id = response.json()["session_id"]

def upload_file(path, session_id):
    url = f"{FILE_SERVICE_BASE_URL}/files/upload"
    with open(path, "rb") as f:
        files = {"file": f}
        data = {"session_id": session_id}
        r = requests.post(url, files=files, data=data)
    if r.status_code != 200:
        raise Exception(f"Upload failed for {path}: {r.text}")
    result = r.json()
    print(f"Uploaded {os.path.basename(path)} -> file_id={result.get('file_id')}")
    return result.get("file_id")


file_paths = [
    os.path.join(BASE_DIR, "covid-19.pdf"),
    os.path.join(BASE_DIR, "regeneration.pdf")
]

file_ids = [upload_file(p, session_id) for p in file_paths]

def get_file_status(file_id):
    url = f"{FILE_SERVICE_BASE_URL}/files/{file_id}"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"Failed to get status for {file_id}: {r.text}")
    return r.json().get("status")

def wait_for_processing(file_ids, interval=20):
    """Polls file statuses every `interval` seconds."""
    print("\nWaiting for files to be processed...")
    processed = set()
    while len(processed) < len(file_ids):
        for fid in file_ids:
            if fid in processed:
                continue
            try:
                status = get_file_status(fid)
                print(f"File {fid}: {status}")
                if status == "processed":
                    processed.add(fid)
                elif status == "error":
                    print(f"File {fid} failed to process. Stopping.")
                    return False
            except Exception as e:
                print(f"Error checking {fid}: {e}")
        if len(processed) < len(file_ids):
            time.sleep(interval)
    print("All files processed successfully.")
    return True

wait_for_processing(file_ids)

# ==================== NEO4J HELPER ====================
class Neo4jHelper:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_node_by_id(self, node_id):
        query = f"MATCH (n) WHERE elementId(n) = \"{node_id}\" RETURN n" 
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            if record:
                node = record["n"]  
                if node and node.get("text"): 
                    return node["text"]
            return None

neo4j_helper = Neo4jHelper(VITE_NEO4J_URI, VITE_NEO4J_USERNAME, VITE_NEO4J_PASSWORD)

# ==================== QUERY ====================
def query_chatbot(question, session_id):
    payload = {
        "query": question,
        "session_id": session_id
    }
    try:
        r = requests.post(ANSWER_QUESTION, json=payload)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error querying: {e}")
        return None

# ===============================================


file_path = os.path.join(BASE_DIR, "questions_answers.xlsx")
df = pd.read_excel(file_path)
dataset = df.to_dict(orient="records")

results = []

for item in dataset:
    question = item.get("Question")
    ground_truth = item.get("Answer")

    print(f"\nAsking chatbot: {question}")
    resp = query_chatbot(question, session_id)
    if not resp:
        continue

    chatbot_answer = resp.get("answer")
    retriever_results = resp.get("retriever_result", [])
    answer_created_at = resp.get("answer_created_at")

    node_contexts = []
    for rr in retriever_results:
        list_ids = rr.get("listIds", [])
        if list_ids:
            node_id = list_ids[0]
            node_data = neo4j_helper.get_node_by_id(node_id)
            if node_data:
                node_contexts.append(node_data)

    result_entry = {
        "question": question,
        "ground_truth": ground_truth,
        "new_answer": chatbot_answer,
        "context": node_contexts
    }
    results.append(result_entry)


dataset_dict = {
    "user_input": [r["question"] for r in results],
    "reference": [r["ground_truth"] for r in results],
    "response": [r["new_answer"] for r in results],
    "retrieved_contexts": [r["context"] for r in results],
}

df = pd.DataFrame(dataset_dict)
output_path = os.path.join(BASE_DIR, "results.xlsx")
pd.DataFrame(df).to_excel(output_path, index=False)

dataset = Dataset.from_dict(dataset_dict)
result = evaluate(
    dataset = dataset, 
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ],
)

df = result.to_pandas()
output_path = os.path.join(BASE_DIR, "metrics.xlsx")
pd.DataFrame(df).to_excel(output_path, index=False)