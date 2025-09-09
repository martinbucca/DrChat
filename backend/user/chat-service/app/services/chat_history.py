import datetime
from typing import List, Literal
from typing_extensions import TypedDict
import neo4j

WINDOW = 6

class LLMMessage(TypedDict):
    role: Literal["ai", "user"]
    content: str


GET_MESSAGES_QUERY = (
    "MATCH (s:`Session`)-[:LAST_MESSAGE]->(last_message) "
    "WHERE s.id = $session_id OPTIONAL MATCH p=(last_message)<-[:NEXT*0.."
    "{window}]-() WITH p, length(p) AS length "
    "ORDER BY length DESC LIMIT 1 UNWIND reverse(nodes(p)) AS node "
    "RETURN {{data:{{content: node.content}}, role:node.role}} AS result"
)

ADD_MESSAGE_QUERY = (
    "MATCH (s:`Session`) WHERE s.id = $session_id "
    "OPTIONAL MATCH (s)-[lm:LAST_MESSAGE]->(last_message) "
    "CREATE (s)-[:LAST_MESSAGE]->(new:Message) "
    "SET new.role = $role, new.content = $content, new.createdAt = $createdAt "
    "WITH new, lm, last_message WHERE last_message IS NOT NULL "
    "CREATE (last_message)-[:NEXT]->(new) "
    "DELETE lm"
)

class ChatMessageHistory():
    """
    MessageHistory manages the creation of message history objects for chat sessions.
    Attributes:
        _driver: Database driver or connection object for persistent storage.
        _window (int): The maximum number of messages to retain in the history window.
    """

    _instance = None

    
    def __init__(
        self,
        driver,
        window,
    ) -> None:
        self._driver = driver
        self._window = window - 1

    def messages(self, session_id: str) -> List[LLMMessage]:
        try:
            result = self._driver.execute_query(
                query_=GET_MESSAGES_QUERY.format(window=self._window),
                parameters_={"session_id": session_id},
            )
            messages = [
                LLMMessage(
                    content=el["result"]["data"]["content"],
                    role=el["result"]["role"],
                )
                for el in result.records
            ]
            return messages
        except neo4j.exceptions.Neo4jError as e:
            return []


    def add_message(self, message: LLMMessage, session_id: str) -> None:
        """Add a message to the message history.

        Args:
            message (LLMMessage): The message to add.
            session_id (str): The session identifier to which the message belongs.
        """
        try:
            created_at = datetime.datetime.now()
            result = self._driver.execute_query(
                query_=ADD_MESSAGE_QUERY,   
                parameters_={
                    "session_id": session_id,
                    "role": message["role"],
                    "content": message["content"],
                    "createdAt": created_at,
                },
            )
        except neo4j.exceptions.Neo4jError as e:
            raise Exception(f"Error adding message to history: {e}")

    @classmethod
    def get_instance(cls, driver, window=WINDOW):
        if cls._instance is None:
            cls._instance = cls(driver=driver, window=window)
        return cls._instance
