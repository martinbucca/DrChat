import os
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer, GlinerGraphTransformer, RelikGraphTransformer
from langchain_core.documents import Document

load_dotenv()

class EntityRelationshipExtractor:
    """
    EntityRelationshipExtractor is a service class designed to extract medical entities and their relationships from unstructured text using a Large Language Model (LLM). The extracted entities and relationships are structured for integration into a graph database such as Neo4j.
    Key Features:
    - Utilizes an LLM to transform raw text into graph components (nodes/entities and edges/relationships) with a focus on clinically relevant information.
    - Supports configurable lists of allowed node and relationship types, tailored for medical and biomedical domains.
    - Provides serialization methods to convert extracted entities and relationships into dictionary formats suitable for downstream processing or database import.
    - Implements a singleton pattern via the `get_instance` class method to ensure a single extractor instance is used throughout the application.
    Usage:
    1. Initialize the extractor with a compatible LLM.
    2. Call `extract_entities_and_relationships(text)` to process a text chunk and receive structured entities and relationships.
    3. The output can be used to populate or update a medical knowledge graph.
    Attributes:
        llm: The language model used for entity and relationship extraction.
        doc_transformer: The document transformer responsible for converting text into graph components.
    Methods:
        extract_entities_and_relationships(text): Extracts and serializes entities and relationships from the input text.
        _serialize_nodes(nodes): Serializes node objects into dictionaries.
        _serialize_relationships(relationships): Serializes relationship objects into dictionaries.
        get_instance(): Returns a singleton instance of the extractor.

    """

    _instance = None

    def __init__(self, llm):
        self.llm = llm
        self.doc_transformer = self._create_doc_transformer()

    def _create_doc_transformer(self):
        '''
        Crea el transformador de documentos para convertir texto en entidades y relaciones de grafo.
        El transformador de documentos utiliza un LLM para convertir texto en entidades y relaciones de grafo.
        https://python.langchain.com/v0.1/docs/use_cases/graph/constructing/#llm-graph-transformer
        '''
        #graph_transformer_prompt = default_prompt + [
        #    ("human", "Importante: Las entidades y relaciones deben estar en el idioma Español.")
        #] 
        additional_instructions = """
        Extract medical entities and relationships from the following text. 
        Focus on clinically relevant information.
        Guidelines:
        1. Be precise with medical terminology
        2. Include relevant attributes in properties (e.g., dosage, severity)
        3. Connect related concepts appropriately
         """
        potential_nodes = [
            "Object", "Entity", "Group", "Person", "Organization", "Place",
            "ArticleOrPaper", "PublicationOrJournal",
            "Anatomy", "BiologicalProcess", "Cell", "CellularComponent",
            "CellType", "Condition", "Disease", "Drug",
            "EffectOrPhenotype", "Exposure", "GeneOrProtein", "Molecule",
            "MolecularFunction", "Pathway"
        ]
        potential_relationships = [
            "ACTIVATES", "AFFECTS", "ASSESSES", "ASSOCIATED_WITH", "AUTHORED",
            "BIOMARKER_FOR", "CAUSES", "CITES", "CONTRIBUTES_TO", "DESCRIBES", "EXPRESSES",
            "HAS_REACTION", "HAS_SYMPTOM", "INCLUDES", "INTERACTS_WITH", "PRESCRIBED",
            "PRODUCES", "RECEIVED", "RESULTS_IN", "TREATS", "USED_FOR"
        ]

        return LLMGraphTransformer(llm=self.llm,allowed_nodes=potential_nodes,
                                   allowed_relationships=potential_relationships,
                                   additional_instructions=additional_instructions, ignore_tool_usage=True, strict_mode=False)                  
    

    def extract_entities_and_relationships(self, text) -> dict:
        """
        Extracts entities and relationships from a text chunk and imports them into Neo4j.
        Connects each entity to the existing Chunk node via MENTIONS relationship.
        
        Args:
            chunk: The text chunk to process
            chunk_id: The ID of the existing Chunk node in Neo4j
        """
        doc = Document(page_content=text)

        graph_docs = self.doc_transformer.convert_to_graph_documents([doc])
        entities = []
        entity_relationships = []
        for graph_doc in graph_docs:
            entities.extend(graph_doc.nodes)
            entity_relationships.extend(graph_doc.relationships)
        serialized_entities = self._serialize_nodes(entities)
        serialized_relationships = self._serialize_relationships(entity_relationships)
        return {
            "entities": serialized_entities,
            "relationships": serialized_relationships
        }
    
    def _serialize_nodes(self, nodes):
        return [
            {
                "id": node.id, 
                "type": node.type
            }
            for node in nodes
        ]

    def _serialize_relationships(self, relationships):
        return [
            {
                "source": rel.source.id,
                "target": rel.target.id,
                "type": rel.type
            }
            for rel in relationships
        ]

    @classmethod
    def get_instance(cls, llm):
        if cls._instance is None:
            cls._instance = cls(llm)
        return cls._instance