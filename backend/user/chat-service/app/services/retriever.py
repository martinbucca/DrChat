from neo4j_graphrag.retrievers import VectorCypherRetriever

class Retriever:
    """
    Retriever is a singleton class responsible for retrieving and formatting data from a Neo4j database using vector search.
    Attributes:
        _instance (Retriever): Singleton instance of the Retriever class.
        RETRIEVAL_QUERY (str): Cypher query template for retrieving nodes, their associated documents, and mentioned entities.
    Methods:
        __init__(driver, embedder, index_name):
            Initializes the Retriever with a Neo4j driver, an embedder, and an index name. Sets up a VectorCypherRetriever instance.
        get_instance(driver, embedder, index_name=None):
            Class method to get or create the singleton Retriever instance.
        retriever:
            Property that returns the underlying VectorCypherRetriever instance.
    Notes:
        - The RETRIEVAL_QUERY is used to augment the context by traversing relationships in the graph database.
        - The formatter method is a placeholder for future result formatting improvements.
    """
    
    _instance = None

    RETRIEVAL_QUERY = """
    // get the document
    WITH node, score
    MATCH (node)-[:PART_OF_DOCUMENT]->(d:Document)
    WITH node, score, d
    // get the entities
    MATCH (node)-[:MENTIONS]-(e)
    WITH node, score, d, collect({
        name: e.name,
        id: e.id
    }) as entities
    RETURN
        {
        text: node.text, 
        document: d.name,
        score: score,
        page: node.page_number,
        entities: entities
        } AS metadata
    """


    def __init__(self, driver, embedder, index_name):
        self._retriever = VectorCypherRetriever(
            driver,
            index_name=index_name,
            retrieval_query=self.RETRIEVAL_QUERY,
            #result_formatter=self.formatter,
            embedder=embedder,
            neo4j_database='neo4j',
        )

    # TODO: Implement a better formatter that structures the results in a more useful way.
    # def formatter(self, results):
        
    @classmethod
    def get_instance(cls, driver, embedder, index_name=None):
        if cls._instance is None:
            cls._instance = cls(driver, embedder, index_name)
        return cls._instance
    
    @property
    def retriever(self):
        return self._retriever