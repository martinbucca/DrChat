from fastapi import HTTPException
from app.api.requests.update_session_name_request import UpdateSessionNameRequest


class UpdateSessionNameEndpoint:
    def __init__(self, app, neo4j_driver):
        self.app = app
        self.neo4j_driver = neo4j_driver
        self._register_endpoint()

    def _register_endpoint(self):
        @self.app.put("/session")
        async def update_session_name(request: UpdateSessionNameRequest):
            try:
                user_id = request.user_id
                session_id = request.session_id
                new_name = request.new_name

                if not new_name or not new_name.strip():
                    raise HTTPException(status_code=400, detail="El nuevo nombre de la sesión no puede estar vacío")
                


                with self.neo4j_driver.session() as session:
                    result = session.run(
                        """
                        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:Session {id: $session_id})
                        SET s.name = $new_name
                        RETURN s.id AS session_id, s.name AS session_name
                        """,
                        user_id=user_id,
                        session_id=session_id,
                        new_name=new_name
                    )
                    record = result.single()
                    if record is None:
                        raise HTTPException(status_code=404, detail="Usuario o Sesión no encontrados para el usuario dado")

                    return {
                        "session_id": record["session_id"],
                        "session_name": record["session_name"]
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
    @classmethod
    def register(cls, app, neo4j_driver):
        cls(app, neo4j_driver)

