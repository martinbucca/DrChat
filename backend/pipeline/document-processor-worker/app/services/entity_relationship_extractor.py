import os
from langchain_neo4j import Neo4jGraph
from core.logging import logger as log
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer, GlinerGraphTransformer, RelikGraphTransformer

load_dotenv()


MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
GROQ_API_BASE = "https://api.groq.com/openai/v1"

os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY")


class EntityRelationshipExtractor:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        self.llm = ChatOpenAI(
            model=MODEL,
            temperature=0,
            openai_api_base=GROQ_API_BASE
        )
        self.docs_transformer = self.create_doc_transformer()  

    def create_doc_transformer(self):
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
    
    
    def extract_entities_and_relationships(self, chunk, chunk_id: str):
        """
        Extracts entities and relationships from a text chunk and imports them into Neo4j.
        Connects each entity to the existing Chunk node via MENTIONS relationship.
        
        Args:
            chunk: The text chunk to process
            chunk_id: The ID of the existing Chunk node in Neo4j
        """
        log.info(f"Extracting entities and relationships for chunk ID: {chunk_id}")
        graph_docs = self.docs_transformer.convert_to_graph_documents([chunk])
        for graph_doc in graph_docs:
            entities = graph_doc.nodes    
            entity_relationships = graph_doc.relationships
            
            self._import_entities(entities, chunk_id)
            self._import_entity_relationships(entity_relationships) 
    

    def _import_entities(self, entities, chunk_id):
        """Imports entities and connects them to the specified Chunk node"""
        if not entities:
            return
        
        for entity in entities:
            # Ensure the entity has a unique ID and type
            if not entity.id or not entity.type:
                continue
            
            query = f"""
                MERGE (e:__Entity__ {{id: $id}})
                SET e += $properties
                SET e:{entity.type}
                WITH e as entity
                MATCH (c:Chunk {{id: $chunk_id}})
                MERGE (c)-[:MENTIONS]->(entity)
            """

            self.graph.query(query, params={
                "id": entity.id,
                "properties": entity.properties,
                "chunk_id": chunk_id
            })

        
    def _import_entity_relationships(self, relationships):
        """Imports relationships between Entity nodes"""
        if not relationships:
            return
        
        for rel in relationships:
            if not rel.source or not rel.target or not rel.type:
                continue
            
            query = """
                MATCH (source:__Entity__ {id: $source})
                MATCH (target:__Entity__ {id: $target})
                MERGE (source)-[r:`%s`]->(target)
                SET r += $properties
            """ % (rel.type)
            self.graph.query(query, params={
                "source": rel.source.id,
                "target": rel.target.id,
                "properties": rel.properties
            })