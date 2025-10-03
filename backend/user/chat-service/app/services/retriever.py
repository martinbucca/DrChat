from neo4j_graphrag.retrievers import VectorCypherRetriever
import neo4j
from neo4j_graphrag.types import RetrieverResultItem
import logging

logger = logging.getLogger(__name__)

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
    // get the entities - optional to include chunks without entity mentions
    OPTIONAL MATCH (node)-[:MENTIONS]-(e)
    WITH node, score, d, collect({
        text: e.text,
        label: e.label,
        elementId: elementId(e)
    }) as entities
    RETURN
        node.text AS nodeText,
        score, 
        node.page_number AS page,
        d.name AS document,
        entities,
        collect(elementId(node)) + [entity IN entities | entity.elementId] as listIds
    """


    def __init__(self, driver, embedder, index_name):
        logger.info(f"Initializing retriever with index: {index_name}")
        
        self._retriever = VectorCypherRetriever(
            driver,
            index_name=index_name,
            retrieval_query=self.RETRIEVAL_QUERY,
            result_formatter=self.formatter,
            embedder=embedder,
            neo4j_database='neo4j',
        )

        self._retriever._node_label = "Chunk"
        self._retriever._node_embedding_property = "embedding"
        self._embedding_dimension = 3072
        
        logger.info("Retriever initialized successfully")

    # TODO: Implement a better formatter that structures the results in a more useful way.
    # def formatter(self, results):
    @staticmethod
    def formatter(record: neo4j.Record) -> RetrieverResultItem:
        node_text = record.get("nodeText", "")
        score = record.get("score", 0)
        document = record.get("document", "")
        page = record.get("page", "")
        entities = record.get("entities", [])
        list_ids = record.get("listIds", [])

        # Format entities as "name (id)"
        entities_str = ", ".join(
            f"{ent.get('text', '')} ({ent.get('label', '')})" for ent in entities if ent.get('text')
        )

        # Prepare content string, clear and ready for LLM
        clean_text = node_text.replace("\n", chr(10))
        content = (
            f"Score: {score}\n\n"
            f"Document: {document.split('/')[-1].rsplit('.', 1)[0]}\n\n"
            f"Text: {clean_text}\n\n"
            f"Entities mentioned in the text: {entities_str}\n\n"
            f"Page: {page}\n"
        )

        return RetrieverResultItem(
            content=content,
            metadata={
                "listIds": list_ids,
            }
        )
        
    @classmethod
    def get_instance(cls, driver, embedder, index_name=None):
        if cls._instance is None:
            cls._instance = cls(driver, embedder, index_name)
        return cls._instance
    
    def search(self, query_text: str, filters: dict = None, **kwargs):
        """Wrapper around _retriever.search with logging"""
        try:
            result = self._retriever.search(query_text=query_text, filters=filters, **kwargs)
            logger.info(f"Search completed, found {len(result.items)} items")
            return result
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    @property
    def retriever(self):
        return self._retriever
