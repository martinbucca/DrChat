from fastapi import HTTPException
from app.api.requests.create_session_request import CreateSessionRequest



class CreateSessionEndpoint:
    def __init__(self, app, neo4j_driver):
        self.app = app
        self.neo4j_driver = neo4j_driver
        self._register_endpoint()

    def _register_endpoint(self):
        @self.app.post("/session")
        async def create_session(request: CreateSessionRequest):
            try:
                user_id = request.user_id
                session_id = request.session_id
                session_name = request.session_name

                with self.neo4j_driver.session() as session:


                    

                    # Check if session with the same session_id already exists
                    result = session.run(
                        "MATCH (s:Session {id: $session_id}) RETURN s",
                        session_id=session_id
                    )
                    if result.single():
                        raise HTTPException(status_code=400, detail="Session ID already exists")

                    session.run(
                        """
                        MERGE (u:User {id: $user_id})
                        MERGE (s:Session {id: $session_id, name: $session_name, created_at: datetime()})
                        MERGE (u)-[:HAS_SESSION]->(s)
                        """,
                        user_id=user_id,
                        session_id=session_id,
                        session_name=session_name
                    )

                return {
                    "session_id": session_id,
                    "message": "Sesión creada exitosamente"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
    @classmethod
    def register(cls, app, neo4j_driver):
        cls(app, neo4j_driver)