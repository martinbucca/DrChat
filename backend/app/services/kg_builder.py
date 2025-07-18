import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import Node, Relationship
from langchain_huggingface import HuggingFaceEmbeddings

from dotenv import load_dotenv
load_dotenv()

EMBEDDINGS_MODEL = "sentence-transformers/msmarco-distilbert-base-tas-b"
MODEL = "deepseek-r1-distill-llama-70b"
DOCS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents")
GROQ_API_BASE = "https://api.groq.com/openai/v1"

os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY")

class KnowledgeGraphBuilder:
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
        self.embedding_provider = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
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
        return LLMGraphTransformer(
            llm=self.llm,
            #prompt=graph_transformer_prompt,
            ignore_tool_usage=True,
        )   
        
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

    def add_entities_and_relationships(self, chunk, chunk_id):
        '''
        Recibe un chunk de texto y su id, y genera entidades y relaciones a partir del texto (la funcion .convert_to_graph_documents).

        El chunk de texto se convierte en un nodo de grafo con el id del chunk y el texto del chunk.

        '''
        # Generate the entities and relationships from the chunk with LLM (converts text to graph entities and relationships)
        graph_docs = self.docs_transformer.convert_to_graph_documents([chunk])

        # las entidades y relaciones generadas por la llm estan en graph_docs
        for graph_doc in graph_docs:
            
            # Creo un nodo de grafo para el chunk
            chunk_node = Node(
                id=chunk_id,
                type="Chunk"
            )
            # Para cada entidad extraida del chunk
            for node in graph_doc.nodes:
                # Agrego una relacion entre el chunk y la entidad
                # chunk -[:HAS_ENTITY]-> entity
                graph_doc.relationships.append(
                    Relationship(
                        source=chunk_node,
                        target=node, 
                        type="HAS_ENTITY"
                        )
                    )

        # Carga directamente los nodos y relaciones en la base de datos Neo4j
        self.graph.add_graph_documents(graph_docs)


    def process_chunk(self, chunk):
        '''
        Recibe un chunk de texto y lo procesa para agregarlo a la base de datos Neo4j.
        '''
        filename = os.path.basename(chunk.metadata["source"])
        page = chunk.metadata["page"]
        chunk_id = f"{filename}.{page}"
        print("Processing -", chunk_id)

        # Se genera el vector embedding para el texto del chunk
        chunk_embedding = self.embedding_provider.embed_query(chunk.page_content)

        # Agregar un nodo 'Document' y otro nodo 'Chunk' al grafo
        # Se crea un nodo 'Document' con el id del archivo
        # Se crea un nodo 'Chunk' con el id del chunk, el texto del chunk y el embedding del chunk
        # Se crea una relacion entre el nodo 'Document' y el nodo 'Chunk' del tipo 'PART_OF'
        properties = {
            "filename": filename,
            "chunk_id": chunk_id,
            "text": chunk.page_content,
            "embedding": chunk_embedding
        }
        
        # Agrega el nodo 'Document' y el nodo 'Chunk' al grafo junto con la relacion entre ellos
        self.graph.query("""
            MERGE (d:Document {id: $filename})
            MERGE (c:Chunk {id: $chunk_id})
            SET c.text = $text
            MERGE (d)<-[:PART_OF]-(c)
            WITH c
            CALL db.create.setNodeVectorProperty(c, 'textEmbedding', $embedding)
            """, 
            properties
        )
        # a cada chunk se le extraen entidades y relaciones entre las entidades y se conectan al chunk correspondiente
        self.add_entities_and_relationships(chunk, chunk_id)
        

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


    def create_kg(self):
        try: 
            self.empty_neo4j_database()
            # Gather the data
            loader = DirectoryLoader(DOCS_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)
            docs = loader.load()
            # Split the data into chunks
            text_splitter = CharacterTextSplitter(
                separator="\n\n",
                chunk_size=1500,
                chunk_overlap=200,
            )

            chunks = text_splitter.split_documents(docs)
            # Vectorize Data: Create embeddings for each chunk
            for chunk in chunks:
                self.process_chunk(chunk)

            self.create_vector_index()
        except Exception as e:
            print(e)
            raise e

    





    
