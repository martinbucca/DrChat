from fastapi import HTTPException
from app.api.requests.get_sessions_chats_requests import GetSessionsChatsRequest
from fastapi import Query


GET_SESSIONS_MESSAGES_QUERY = (
    "MATCH (u:User {id: $user_id})-[:HAS_SESSION]->(s:Session) "
    "OPTIONAL MATCH (s)-[:LAST_MESSAGE]->(last_message:Message) "
    "WITH s, last_message "
    "ORDER BY s.created_at DESC "
    "OPTIONAL MATCH p=(last_message)<-[:NEXT*0..1000]-() "
    "WITH s, last_message, collect(p) AS paths "
    "WITH s, last_message, "
    "  [p IN paths | {p: p, length: CASE WHEN p IS NULL THEN 0 ELSE length(p) END}] AS path_infos "
    "UNWIND path_infos AS path_info "
    "WITH s, last_message, path_info "
    "ORDER BY path_info.length DESC "
    "WITH s, last_message, collect(path_info)[0] AS max_path_info "
    "WITH s, last_message, max_path_info.p AS p "
    "WITH s, last_message, "
    "(CASE WHEN p IS NOT NULL "
    "THEN [msg IN reverse(nodes(p)) | "
    "{content: msg.content, role: msg.role, created_at: toString(msg.createdAt)}] "
    "ELSE [] END) AS messages "
    "RETURN s.id AS session_id, s.name AS session_name, toString(s.created_at) AS session_created_at, messages "
)




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
                        GET_SESSIONS_MESSAGES_QUERY,
                        user_id=user_id
                    )

                    sessions = []
                    for record in result:
                        sessions.append({
                            "session_id": record["session_id"],
                            "session_name": record["session_name"],
                            "session_created_at": record["session_created_at"],
                            "messages": record["messages"]
                        })

                    return {"sessions": sessions}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
    @classmethod
    def register(cls, app, neo4j_driver):
        cls(app, neo4j_driver)