from fastapi import HTTPException
from app.api.requests.query_request import QueryRequest
from app.services.chat_history import LLMMessage
import logging
from neo4j.graph import Node, Relationship

logger = logging.getLogger(__name__)


def build_query(list_ids):
    formatted_sources = ", ".join(f'"{id_}"' for id_ in list_ids)
    query = f"""
    MATCH (a:Chunk)-[r:PART_OF_DOCUMENT]->(b:Document)
    WHERE elementId(a) in [{formatted_sources}]
    RETURN DISTINCT a,r,b
    UNION
    MATCH (a:Chunk)-[r:NEXT_CHUNK]-(b:Chunk)
    WHERE elementId(a) in [{formatted_sources}] AND elementId(b) in [{formatted_sources}]
    RETURN DISTINCT a,r,b
    UNION
    MATCH (a:Chunk)-[r:MENTIONS]-(b)
    WHERE elementId(a) in [{formatted_sources}] AND elementId(b) in [{formatted_sources}]
    RETURN DISTINCT a,r,b
    UNION
    MATCH (c:Chunk)-[:MENTIONS]->(a) 
    MATCH (c)-[:MENTIONS]->(b) 
    MATCH (a)-[r]->(b) 
    WHERE elementId(c) IN [{formatted_sources}] AND a <> b 
    RETURN DISTINCT a, r, b
    UNION
    MATCH (a:Chunk)-[r:RELATED_CONTENT]->(b:Image|Table)
    WHERE elementId(a) in [{formatted_sources}]
    RETURN DISTINCT a,r,b
    LIMIT 500;
    """
    return query.strip()

def run_query(driver,query:str):
        nodes = []
        rels = []
        node_ids = set()
        rel_ids = set()

        try:
            with driver.session() as session:
                result = session.run(query)

                for record in result:
                    a = record.get("a")
                    b = record.get("b")
                    r = record.get("r")

                    if isinstance(a, Node):
                        if a.element_id not in node_ids:
                            nodes.append({
                                "id": a.element_id, 
                                "labels": list(a.labels),
                                "properties": dict(a.items())
                            })
                            node_ids.add(a.element_id)

                    if isinstance(b, Node):
                        if b.element_id not in node_ids:
                            nodes.append({
                                "id": b.element_id,
                                "labels": list(b.labels),
                                "properties": dict(b.items())
                            })
                            node_ids.add(b.element_id)

                    if isinstance(r, Relationship):
                        if r.element_id not in rel_ids:
                            rels.append({
                                "id": r.element_id,
                                "start": r.start_node.element_id,
                                "end": r.end_node.element_id,
                                "type": r.type,
                                "properties": dict(r.items())
                            })
                            rel_ids.add(r.element_id)
            return {"nodes": nodes, "rels": rels}
        except Exception as e:
            print(f"Query error: {e}")
            return {"nodes": [], "rels": []}

class AnswerQuestionEndpoint:
    """
    Endpoint class for handling question-answering requests.
    This class registers a POST endpoint `/answer_question` on the provided FastAPI app.
    It receives a `QueryRequest` containing a user query and session ID, validates the input,
    and uses the provided `graphrag` object to search for an answer. The response includes
    the answer and retriever result. Handles invalid queries and internal errors with appropriate HTTP exceptions.
    Args:
        app: FastAPI application instance where the endpoint will be registered.
        graphrag: An object with a `search(query, session_id)` method to process the query.
    Methods:
        _register_endpoint():
            Registers the `/answer_question` POST endpoint.
    """
    def __init__(self, app, graphrag,driver):
        self._app = app
        self._graphrag = graphrag
        self._driver = driver
        self._register_endpoint()

    def _register_endpoint(self):
        @self._app.post("/answer_question")
        async def answer_question(request: QueryRequest):
            try:
                if not request.query or not request.query.strip():
                    raise HTTPException(status_code=400, detail="Consulta inválida")
                    
                session_id = request.session_id
                question = request.query
                created_at = request.created_at
                
                result = self._graphrag.search(question, session_id, created_at)
                answer = result.answer
                retriever_result = result.retriever_result
                
                answer_created_at = result.created_at
                retriever_nodes = []
                for item in retriever_result.items:
                    retriever_nodes.append(item.metadata)
                list_ids = [
                    list_id
                    for item in retriever_result.items
                    for list_id in item.metadata.get("listIds", [])
                    if list_id is not None
                ]
                query = build_query(list_ids)
                data = run_query(self._driver,query)
                return {"answer": answer, 
                        "retriever_result": retriever_nodes, 
                        "answer_created_at": answer_created_at, 
                        "nodes": data["nodes"], 
                        "rels": data["rels"]}
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

