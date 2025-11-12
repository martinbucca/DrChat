# Creating the vector index
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Dict, List, Optional, Tuple

from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.indexes import create_fulltext_index
from neo4j import GraphDatabase
from config import VECTOR_INDEX_NAME, FULLTEXT_INDEX_NAME, VECTOR_DIMENSIONS
import nltk
import base64
import zlib
import json
import logging

logger = logging.getLogger(__name__)

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
MERGE (d:Document {name: m.metadata.original_filename, session_id: COALESCE(m.metadata.session_id, "global")})
SET d.session_id = COALESCE(m.metadata.session_id, "global")
WITH m, d
MERGE (n:Chunk {id: m.element_id})
SET
  n.type = "NarrativeText",
  n.text = m.text,
  n.filename = m.metadata.original_filename,
  n.filetype = m.metadata.filetype,
  n.languages = m.metadata.languages,
  n.page_number = m.metadata.page_number,
  n.chunk_number = m.number,
  n.tokens = m.tokens,
  n.embedding = m.embedding,
  n.session_id = COALESCE(m.metadata.session_id, "global")
MERGE (n)-[:PART_OF_DOCUMENT]->(d)
WITH m, d, n
WHERE m.metadata.type IN ['Image', 'Table']
CALL apoc.merge.node([m.metadata.type], {id: m.element_id}, 
  {type: m.metadata.type,
   figure_caption: m.metadata.figure_caption,
   text: m.metadata.text,
   filename: m.metadata.original_filename,
   filetype: m.metadata.filetype,
   languages: m.metadata.languages,
   page_number: m.metadata.page_number,
   image_base64: m.metadata.image_base64,
   image_mime_type: m.metadata.image_mime_type,
   text_as_html: m.metadata.text_as_html,
   session_id: COALESCE(m.metadata.session_id, "global")}, 
  {}) YIELD node as i
WITH m, d, n, i
MERGE (n)-[:RELATED_CONTENT]->(i)
MERGE (i)-[:PART_OF_DOCUMENT]->(d)

// --- Entidades ---
WITH m, n
UNWIND m.entities AS e
CALL apoc.merge.node([e.label], {canonical_text: e.canonical_text}, 
  {text: e.text,
   confidence: e.confidence,
   start: e.start,
   end: e.end,
   id: e.id,
   label: e.label}, 
  {confidence: CASE 
                 WHEN coalesce(e.confidence,0) > coalesce({confidence: e.confidence}.confidence,0) 
                 THEN e.confidence 
                 ELSE {confidence: e.confidence}.confidence 
               END}) YIELD node as ent
WITH m, n, ent
MERGE (n)-[:MENTIONS]->(ent)

// --- Relaciones ---
WITH m, n
WHERE size(m.relationships) > 0
UNWIND m.relationships AS r
// USAR OPTIONAL MATCH PARA EVITAR ERRORES SI NO EXISTEN
OPTIONAL MATCH (source {canonical_text: r.source})
OPTIONAL MATCH (target {canonical_text: r.target})
WITH m, n, r, source, target
WHERE source IS NOT NULL AND target IS NOT NULL  // SOLO SI AMBOS EXISTEN
CALL apoc.merge.relationship(source, r.type, {id: r.id}, 
  {confidence: r.confidence}, 
  target, 
  {confidence: CASE WHEN coalesce(r.confidence,0) > coalesce({confidence: r.confidence}.confidence,0) THEN r.confidence ELSE {confidence: r.confidence}.confidence END}) 
YIELD rel
RETURN count(rel) as relationships_created
'''

    NEXT_CHUNK_QUERY = '''
MATCH (d:Document {name: $filename})<-[:PART_OF_DOCUMENT]-(n:Chunk)
WHERE n.session_id = coalesce($session_id, "global") AND n.chunk_number IS NOT NULL
WITH d, n
ORDER BY toInteger(n.chunk_number)
WITH d, collect(n) AS nodes
CALL apoc.nodes.link(nodes, "NEXT_CHUNK", {avoidDuplicates: true})
'''

    _instance = None

    def __init__(self, driver, embedder, entity_relationship_extractor=None):
        self.driver = driver
        self.embedder = embedder
        self.entity_relationship_extractor = entity_relationship_extractor
        self._create_vector_indexes()

    def process_chunks(
        self, chunks: List[Dict], original_filename: Optional[str] = None, session_id: Optional[str] = None
    ):
        total_chunks = len(chunks)
        logger.info(f"Processing {total_chunks} chunks in parallel for session {session_id}")

        if total_chunks == 0:
            logger.info("No chunks to process")
            return

        self._annotate_session_metadata(chunks, original_filename, session_id)

        max_workers = max(1, min(4, total_chunks))
        chunk_data = list(enumerate(chunks))
        process_chunk = partial(self._process_chunk, total_chunks=total_chunks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            processed_chunks = list(executor.map(process_chunk, chunk_data))

        logger.info("All chunks processed, loading into Neo4j")
        json_data = json.dumps(processed_chunks, indent=4)
        self._load_graph(json_data, original_filename, session_id)

    def _annotate_session_metadata(
        self, chunks: List[Dict], original_filename: Optional[str], session_id: Optional[str]
    ) -> None:
        if not session_id:
            return

        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.setdefault("metadata", {})
            metadata['session_id'] = session_id
            metadata['original_filename'] = original_filename
            chunk['number'] = index

    def _process_chunk(self, chunk_data: Tuple[int, Dict], total_chunks: int) -> Dict:
        index, chunk = chunk_data
        try:
            text = chunk.get("text")
            if text:
                self._process_chunk_text(chunk, text, index)

            self._process_chunk_metadata(chunk)
            logger.info(f"Processed chunk {index + 1}/{total_chunks}")
        except Exception as exc:
            logger.error(f"Error processing chunk {index}: {exc}")
            chunk.setdefault("processing_errors", []).append(str(exc))
        return chunk

    def _process_chunk_text(self, chunk: Dict, text: str, index: int) -> None:
        chunk["entities"] = []
        chunk["relationships"] = []

        if self.entity_relationship_extractor:
            ner_result = self.entity_relationship_extractor.extract_entities_and_relationships(text)
            chunk["entities"] = ner_result.get("entities", [])
            chunk["relationships"] = ner_result.get("relationships", [])

        chunk["tokens"] = len(nltk.word_tokenize(text))

        try:
            chunk["embedding"] = self.embedder.embed_query(text)
        except Exception as exc:
            logger.error(f"Error embedding text for chunk {index}: {exc}")
            chunk["embedding"] = []

    def _process_chunk_metadata(self, chunk: Dict) -> None:
        metadata = chunk.setdefault("metadata", {})
        orig_elements = metadata.get("orig_elements")
        if orig_elements:
            elements = self._extract_orig_elements(orig_elements) if isinstance(orig_elements, (bytes, str)) else orig_elements
            for obj in elements or []:
                self._merge_orig_element(metadata, obj)

        metadata.pop('orig_elements', None)

    def _merge_orig_element(self, metadata: Dict, obj: Dict) -> None:
        element_type = obj.get("type")

        if element_type == "FigureCaption" and obj.get("text", "").lower().startswith("figure"):
            metadata["figure_caption"] = obj["text"]
            return

        if element_type == "Image":
            metadata.update({
                "element_id": obj.get("element_id"),
                "type": element_type,
                "image_base64": obj.get("metadata", {}).get("image_base64"),
                "image_mime_type": obj.get("metadata", {}).get("image_mime_type"),
                "text": obj.get("text"),
            })
            return

        if element_type == "Table":
            metadata.update({
                "element_id": obj.get("element_id"),
                "type": element_type,
                "text_as_html": obj.get("metadata", {}).get("text_as_html"),
                "image_base64": obj.get("metadata", {}).get("image_base64"),
                "image_mime_type": obj.get("metadata", {}).get("image_mime_type"),
                "text": obj.get("text"),
            })

    def _run_query(self, tx, query, json_data):
        return tx.run(query, {"json": json_data}).consume()

    def _run_query_next_chunk_rel(self, tx, query, filename, session_id):
        return tx.run(query, {"filename": filename, "session_id": session_id}).consume()

    def _load_graph(self, json_data, filename, session_id):
        with self.driver.driver.session() as session:
            summary_chunks = session.execute_write(self._run_query, self.CHUNK_QUERY, json_data)
            summary_next = session.execute_write(self._run_query_next_chunk_rel, self.NEXT_CHUNK_QUERY, filename, session_id)

            logger.info(
                f"nodes created => {summary_chunks.counters.nodes_created}, "
                f"rels created => {summary_chunks.counters.relationships_created + summary_next.counters.relationships_created}"
            )

    def _extract_orig_elements(self, encoded):
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded)
        return json.loads(decompressed.decode("utf-8"))

    def _create_vector_indexes(self):
        create_vector_index(
            self.driver.driver,
            VECTOR_INDEX_NAME,
            label="Chunk",
            embedding_property="embedding",
            dimensions=VECTOR_DIMENSIONS,
            similarity_fn="cosine",
            fail_if_exists=False,
        )

        # Constraint para evitar duplicados de entidades
        with self.driver.driver.session() as session:
            try:
                session.run("""
                CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
                FOR (e:Entity)
                REQUIRE e.id IS UNIQUE
                """)
                logger.info("Constraint entity_id_unique creada")
            except Exception as e:
                logger.warning(f"No se pudo crear constraint entity_id_unique: {e}")

            try:
                session.run("""
                CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
                FOR (c:Chunk)
                REQUIRE c.id IS UNIQUE
                """)
                logger.info("Constraint chunk_id_unique creada")
            except Exception as e:
                logger.warning(f"No se pudo crear constraint chunk_id_unique: {e}")

    @classmethod
    def get_instance(cls, driver, embedder, entity_relationship_extractor=None):
        if cls._instance is None:
            cls._instance = cls(driver, embedder, entity_relationship_extractor)
        return cls._instance
