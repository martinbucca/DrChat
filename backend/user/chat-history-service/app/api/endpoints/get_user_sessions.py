from fastapi import HTTPException
from app.api.requests.get_sessions_chats_requests import GetSessionsChatsRequest
from fastapi import Query


class GetUserSessionsEndpoint:
    def __init__(self, app, neo4j_driver):
        self.app = app
        self.neo4j_driver = neo4j_driver
        self._register_endpoint()

    def _register_endpoint(self):
        @self.app.get("/sessions")
        async def get_user_sessions(user_id: str = Query(...)):
            try:

                with self.neo4j_driver.session() as session:
                    result = session.run(
                        """
                        MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:Session)
                        OPTIONAL MATCH (s)-[:LAST_MESSAGE]->(last_message:Message)
                        WITH s, last_message
                        ORDER BY s.created_at DESC
                        OPTIONAL MATCH p=(last_message)<-[:NEXT*0..1000]-()
                        WITH s, last_message, p, length(p) AS length
                        ORDER BY s.created_at DESC, length DESC
                        WITH s, last_message, p
                        WHERE p IS NULL OR length(p) = 
                            max([l IN collect(length(p)) | l])
                        WITH s, last_message, 
                            (CASE WHEN p IS NOT NULL 
                                THEN [msg IN reverse(nodes(p)) | 
                                    {id: msg.id, content: msg.content, type: msg.type, timestamp: msg.timestamp}]
                                ELSE [] END) AS chats
                        RETURN s.id AS session_id, s.name AS session_name, s.created_at AS session_created_at, chats
                        """,
                        user_id=user_id
                    )

                    sessions = []
                    for record in result:
                        sessions.append({
                            "session_id": record["session_id"],
                            "session_name": record["session_name"],
                            "session_created_at": record["session_created_at"],
                            "chats": record["chats"]
                        })

                    return {"sessions": sessions}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
    @classmethod
    def register(cls, app, neo4j_driver):
        cls(app, neo4j_driver)