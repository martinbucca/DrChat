from fastapi import HTTPException
from app.api.requests.delete_session_request import DeleteSessionRequest

class DeleteSessionEndpoint:
    def __init__(self, app, neo4j_driver):
        self.app = app
        self.neo4j_driver = neo4j_driver
        self._register_endpoint()

    def _register_endpoint(self):
        @self.app.delete("/session")
        async def delete_session(request: DeleteSessionRequest):
            try:
                user_id = request.user_id
                session_id = request.session_id

                with self.neo4j_driver.session() as session:
                    # Eliminar todos los mensajes de la sesión y la sesión en una sola query
                    result = session.run(
                        """
                        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:Session {id: $session_id})
                        OPTIONAL MATCH (s)-[:LAST_MESSAGE]->(last_message)
                        OPTIONAL MATCH p=(last_message)<-[:NEXT*0..]-(msg)
                        WITH u, s, collect(DISTINCT msg) + collect(DISTINCT last_message) AS messages
                        FOREACH (m IN messages | DETACH DELETE m)
                        DETACH DELETE s
                        RETURN s
                        """,
                        user_id=user_id,
                        session_id=session_id
                    )
                    record = result.single()
                    if record is None:
                        raise HTTPException(status_code=404, detail="Usuario o Sesion no encontrados para el usuario dado")

                    return {
                        "session_id": session_id,
                        "message": "Sesión y mensajes asociados eliminados exitosamente"
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
    @classmethod
    def register(cls, app, neo4j_driver):
        cls(app, neo4j_driver)
