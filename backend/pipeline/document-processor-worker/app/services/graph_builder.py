# Creating the vector index
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.indexes import create_fulltext_index
from neo4j import GraphDatabase
from app.config import VECTOR_INDEX_NAME, FULLTEXT_INDEX_NAME
import nltk
import base64
import zlib
import json

class GraphBuilder:
    """
    GraphBuilder processes document chunks, generates embeddings, extracts metadata and entities,
    and builds a knowledge graph in Neo4j. It supports semantic vector indexing for efficient search.

    Attributes:
        CHUNK_QUERY (str): Cypher query for inserting chunks and related entities into Neo4j.
        _instance (GraphBuilder): Singleton instance.

    Methods:
        __init__(self, driver, embedder, entity_relationship_extractor=None):
            Initializes with Neo4j driver, embedding model, and optional entity extractor. Creates vector indexes.
        process_chunks(self, chunks: list[dict]):
            Processes chunk dictionaries: computes embeddings, extracts entities, updates metadata, and loads into Neo4j.
        _run_query(self, tx, query, json_data):
            Executes a Cypher query in a Neo4j transaction with JSON data.
        _load_graph(self, json_data):
            Loads processed chunk data into Neo4j using CHUNK_QUERY.
        _extract_orig_elements(self, encoded):
            Decodes and decompresses base64/zlib-encoded original elements metadata.
        _create_vector_indexes(self):
            Creates vector (and optionally fulltext) indexes in Neo4j.
        get_instance(cls, driver, embedder, entity_relationship_extractor=None):
            Returns a singleton instance for the given driver, embedder, and extractor.
    """

    CHUNK_QUERY = '''
WITH apoc.convert.fromJsonList($json) AS maps
UNWIND maps AS map
WITH apoc.map.clean(map,[],["  ",""]) AS m
MERGE (d:Document {name: m.metadata.filename})
WITH m, d
CALL(m, d) {
  CREATE (n:Chunk {id: m.element_id})
  SET
    n.type = "NarrativeText",
    n.text = m.text,
    n.filename = m.metadata.filename,
    n.filetype = m.metadata.filetype,
    n.languages = m.metadata.languages,
    n.page_number = m.metadata.page_number,
    n.tokens = m.tokens,
    n.embedding = m.embedding
  CREATE (n)-[:PART_OF_DOCUMENT]->(d)
  RETURN n
}
WITH m, d, n
CALL(m, d, n) {
  WITH m, d, n
  WHERE m.metadata.type IN ['Image', 'Table']
  CREATE (i:$(m.metadata.type) {id: m.element_id})
  SET i.type = m.metadata.type,
      i.figure_caption = m.metadata.figure_caption,
      i.text = m.metadata.text,
      i.filename = m.metadata.filename,
      i.filetype = m.metadata.filetype,
      i.languages = m.metadata.languages,
      i.page_number = m.metadata.page_number,
      i.image_base64 = m.metadata.image_base64,
      i.image_mime_type = m.metadata.image_mime_type,
      i.text_as_html = m.metadata.text_as_html
  MERGE (n)-[:RELATED_CONTENT]->(i)
  MERGE (i)-[:PART_OF_DOCUMENT]->(d)
}
WITH m, n
UNWIND m.entities AS e
CALL {
  WITH e, n
  // Label dinámico usando apoc.create.addLabels
  MERGE (ent:Entity {id: e.type})
  SET ent.name = e.id
  WITH e, ent, n
  MERGE (n)-[:MENTIONS]->(ent)
}
WITH DISTINCT n
WITH collect(n) AS nodes
CALL apoc.nodes.link(nodes, "NEXT_CHUNK")
'''

    _instance = None

    def __init__(self, driver, embedder, entity_relationship_extractor=None):
        self.driver = driver
        self.embedder = embedder
        self.entity_relationship_extractor = entity_relationship_extractor
        self._create_vector_indexes()

    def process_chunks(self, chunks: list[dict]):
        for i, chunk in enumerate(chunks):
            if chunk.get("text"):
                text = chunk["text"]
                if self.entity_relationship_extractor:
                    ner_result = self.entity_relationship_extractor.extract_entities_and_relationships(text)
                    chunk["entities"] = ner_result.get("entities", [])
                    chunk["relationships"] = ner_result.get("relationships", [])
                chunk["tokens"] = len(nltk.word_tokenize(text))
                try:
                    embedding = self.embedder.embed_query(text)
                    chunk["embedding"] = embedding
                except Exception as e:
                    print(f"Error embedding text for chunk {i}: {e}")

        
            metadata = chunk.get("metadata", {})
            orig_elements = metadata.get("orig_elements", None)
            if orig_elements:
                orig_elements = self._extract_orig_elements(orig_elements)

                for obj in orig_elements:
                    if obj.get("type") == "FigureCaption" and obj.get("text", "").lower().startswith("figure"):
                        metadata["figure_caption"] = obj["text"]

                    if obj.get("type") == "Image":
                        metadata.update({
                            "element_id": obj["element_id"],
                            "type": obj["type"],
                            "image_base64": obj["metadata"]["image_base64"],
                            "image_mime_type": obj["metadata"]["image_mime_type"],
                            "text": obj["text"]
                        })

                    if obj.get("type") == "Table":
                        metadata.update({
                            "element_id": obj["element_id"],
                            "type": obj["type"],
                            "text_as_html": obj["metadata"]["text_as_html"],
                            "image_base64": obj["metadata"]["image_base64"],
                            "image_mime_type": obj["metadata"]["image_mime_type"],
                            "text": obj["text"]
                        })

            chunks[i]['metadata'].pop('orig_elements', None)

        json_data = json.dumps(chunks, indent=4)
        self._load_graph(json_data)

    def _run_query(self, tx, query, json_data):
        return tx.run(query, {"json": json_data}).consume()

    def _load_graph(self, json_data):
        with self.driver.session() as session:
            summary = session.execute_write(self._run_query, self.CHUNK_QUERY, json_data)
            print(f"nodes created => {summary.counters.nodes_created}, rels created => {summary.counters.relationships_created}")

    def _extract_orig_elements(self, encoded):
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded)
        return json.loads(decompressed.decode("utf-8"))

    def _create_vector_indexes(self):
        create_vector_index(
            self.driver,
            VECTOR_INDEX_NAME,
            label="Chunk",
            embedding_property="embedding",
            dimensions=768,
            similarity_fn="cosine",
            fail_if_exists=False,
        )
        # Por ahora es solo busqueda semantica, no hibrida. 
        # No se esta usando este index fulltext
        """
        create_fulltext_index(
            self.driver,
            FULLTEXT_INDEX_NAME,
            label="Entity",
            node_properties= ["text", "variants"],
            fail_if_exists=False,
        )
        """

    @classmethod
    def get_instance(cls, driver, embedder, entity_relationship_extractor=None):
        if cls._instance is None:
            cls._instance = cls(driver, embedder, entity_relationship_extractor)
        return cls._instance