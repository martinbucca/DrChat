import os
from langchain_neo4j import Neo4jGraph
from langchain_community.graphs.graph_document import Node, Relationship
from langchain_huggingface import HuggingFaceEmbeddings
from document_processor import DocumentProcessor
from core.logging import logger as log

from dotenv import load_dotenv
load_dotenv()

EMBEDDINGS_MODEL = "sentence-transformers/msmarco-distilbert-base-tas-b"


class KnowledgeGraphBuilder:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        self.document_processor = DocumentProcessor()
        self.embedding_provider = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
              
    #TODO: OJO! Cheaquear esto en el futuro porque va a borrar todo el grafo
    # Sirve para limpiar y testear
    def empty_neo4j_database(self):
        '''
        Elimina todos los nodos y relaciones de la base de datos Neo4j.
        '''

        self.graph.query("""
        MATCH (n)
        DETACH DELETE n;
        """
        )
        self.graph.query("""
        DROP INDEX chunkVector IF EXISTS;
        """
        )


    def process_chunk(self, chunk, chunk_num: int):
        '''
        Recibe un chunk de texto y lo procesa para agregarlo a la base de datos Neo4j.
        '''

        filename = chunk.metadata["source"]
        page = chunk.metadata["page"] + 1
        chunk_id = f"{filename}.{chunk_num}"
        page_content = chunk.page_content

        log.info(f"Processing chunk {chunk_num} for file {filename}, page {page}")
        chunk_embedding = self.embedding_provider.embed_query(chunk.page_content)

        properties = {
            "filename": filename,
            "chunk_id": chunk_id,
            "text": chunk.page_content,
            "embedding": chunk_embedding,
            "page": page
        }
        
        self.add_document_and_chunks_to_graph(properties, chunk_num)                              
            
    def add_document_and_chunks_to_graph(self, properties, offset):
        """
        Se encarga de agregar un documento y sus chunks al grafo Neo4j.
        Si el chunk no es el primero, se establece una relación con el chunk anterior.
        Si es el primer chunk, no se establece relación con ningún chunk anterior.
        Cada chunk se almacena como un nodo 'Chunk' y el documento como un nodo 'Document'.
        Cada chunk tiene como propiedades el texto, la página y un embedding de texto.
        """
        if offset > 1:
            previous_chunk_id = f"{properties["filename"]}.{offset - 1}"
            properties["previous_chunk_id"] = previous_chunk_id
            query ="""
                MERGE (d:Document {id: $filename})
                MERGE (c:Chunk {id: $chunk_id})
                SET c.text = $text,
                    c.page = $page
                MERGE (d)<-[:PART_OF]-(c)
                WITH c, $previous_chunk_id AS previous_chunk_id
                MATCH (p:Chunk {id: previous_chunk_id})
                MERGE (c)<-[:NEXT]-(p)
                WITH c
                CALL db.create.setNodeVectorProperty(c, 'textEmbedding', $embedding)
                """      
        else:
            query = """
                MERGE (d:Document {id: $filename})
                MERGE (c:Chunk {id: $chunk_id})
                SET c.text = $text,
                    c.page = $page
                MERGE (d)<-[:PART_OF]-(c)
                WITH c
                CALL db.create.setNodeVectorProperty(c, 'textEmbedding', $embedding)
                """
            
        self.graph.query(query, params=properties)
        self.graph.query("""
            CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;
        """)
        self.graph.query("""
            CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;    
        """)   

        
    def create_vector_index(self):
        # Crea un vector index en la base de datos Neo4j para el campo 'textEmbedding' de los nodos 'Chunk'
        # Este index se utiliza para realizar busquedas por similitud entre los chunks
        self.graph.query("""
            CREATE VECTOR INDEX `chunkVector`
            IF NOT EXISTS
            FOR (c: Chunk) ON (c.textEmbedding)
            OPTIONS {indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
        }};""")


    def create_kg(self, pdf_file_paths: list[str]):
        try: 
            self.empty_neo4j_database()
            

            for path in pdf_file_paths:
                log.info(f"Processing document: {path}")
                chunks = self.document_processor.process_document(path)
                chunk_num = 1
                for chunk in chunks:
                    self.process_chunk(chunk, chunk_num)
                    chunk_num += 1
            
            self.create_vector_index()

        except Exception as e:
            log.error(f"Error creating knowledge graph: {str(e)}")
            raise e

    






    