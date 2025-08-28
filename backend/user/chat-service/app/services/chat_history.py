from neo4j_graphrag.message_history import Neo4jMessageHistory
from neo4j_graphrag.message_history import InMemoryMessageHistory
from neo4j_graphrag.message_history import MessageHistory

class MessageHistory:
    """"
    MessageHistory manages the creation of message history objects for chat sessions.
    Attributes:
        _driver: Optional database driver or connection object for persistent storage.
        _window (int): The maximum number of messages to retain in the history window.
    Methods:
        __init__(driver=None, window=40):
            Initializes the MessageHistory with an optional driver and window size.
        create_history(session_id=None):
            Creates and returns a new message history instance for a given session.
            By default, uses in-memory storage, but can be configured for persistent storage (e.g., Neo4j).
            Args:
                session_id (str, optional): Unique identifier for the chat session.
            Returns:
                An instance of a message history class (e.g., InMemoryMessageHistory).
    """
    # no singleton used as there may be mulitple session id's.

    def __init__(self, driver = None, window = 40):
        self._driver = driver
        self._window = window

    def create_history(self, session_id = None):
        history = InMemoryMessageHistory()
        """
        history = Neo4jMessageHistory(
            session_id=session_id,
            driver=self._driver,
            window=self._window
        )
        """
    
        return history#, self._driver, session_id