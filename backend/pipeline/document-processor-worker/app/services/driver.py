from neo4j import GraphDatabase
from app.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class Neo4jDriver:
    """
    A singleton class for managing a Neo4j database driver instance.
    This class ensures that only one instance of the Neo4j driver is created and used throughout the application.
    It provides methods to get the singleton instance, access the underlying driver, and close the connection.
    Attributes:
        _instance (Neo4jDriver): The singleton instance of the Neo4jDriver.
        _driver (neo4j.Driver): The Neo4j driver instance.
    Methods:
        __init__(uri, username, password):
            Initializes the Neo4j driver with the specified URI and credentials.
        get_instance(uri=None, username=None, password=None):
            Returns the singleton instance of Neo4jDriver. If it does not exist, creates a new one.
        driver:
            Property that returns the underlying Neo4j driver instance.
        close():
            Closes the Neo4j driver connection if it exists.
    """
    
    _instance = None

    def __init__(self, uri, username, password):
        self._driver = GraphDatabase.driver(uri, auth=(username, password))

    @classmethod
    def get_instance(cls, uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD):
        if cls._instance is None:
            cls._instance = cls(uri, username, password)
        return cls._instance

    @property
    def driver(self):
        return self._driver
    
    def close(self):
        if hasattr(self, '_driver') and self._driver:
            self._driver.close()