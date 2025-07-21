import os
from dotenv import load_dotenv
load_dotenv()

from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq


# TODO: Seter estas variables en archivo de configuracion o variables de entorno
NUMBER_OF_DOCUMENTS_RETRIEVED = 3
EMBEDDINGS_MODEL = "sentence-transformers/msmarco-distilbert-base-tas-b"
MODEL_NAME="llama-3.3-70b-versatile"
PROMPT = """Brinda ayuda a los estudiantes de Ingenieria Informatica de la Universidad de Buenos Aires (Facultad de Ingenieria) 
respondiendo sobre las materias de la carrera.
Responde conscisamente y con contexto a la pregunta.
Utiliza el contexto para obtener informacion relevante a la pregunta.
Responde siempre en esapñol.
Si tu respuesta tiene items, formatealos como una lista para que puedan ser renderizados en un frontend react correctamente.
Si no sabes la respuesta o te falta contexto, deci que no sabes.
"""

class VectorRetriever:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        self.llm = ChatGroq(
            temperature=0,
            model_name=MODEL_NAME,
        )
        self.embedding_provider = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
        chunk_retriever = self.get_vector_index().as_retriever(search_kwargs={'k': NUMBER_OF_DOCUMENTS_RETRIEVED})
        chunk_chain = create_stuff_documents_chain(self.llm, self.prompt())
        self.chunk_retriever = create_retrieval_chain(
            chunk_retriever, 
            chunk_chain
        )

    def get_vector_index(self):
        # Vector store for the chunks. This will be used to retrieve the most relevant chunk for a given question.
        return Neo4jVector.from_existing_index(
            self.embedding_provider,
            graph=self.graph,
            # The name of the index created in the previous step
            index_name="chunkVector",
            # The name of the property in the node that contains the embeddings
            embedding_node_property="embedding",
            # The name of the property in the node that contains the text
            text_node_property="text",
            retrieval_query="""
        // get the document
        MATCH (node)-[:PART_OF]->(d:Document)
        WITH node, score, d
        // get the entities
        MATCH (node)-[:HAS_ENTITY]-(e)
        WITH node, score, d, collect(e) as nodeslist
        // find the relationships between the entities related to the document
        MATCH p = (e)-[r]-(e2)
        WHERE e in nodeslist and e2 in nodeslist
        // unwind the path, create a string of the entities and relationships
        UNWIND relationships(p) as rels
        WITH 
            node, 
            score, 
            d, 
            collect(apoc.text.join(
                [labels(startNode(rels))[0], startNode(rels).id, type(rels), labels(endNode(rels))[0], endNode(rels).id]
                ," ")) as kg
        RETURN
            node.text as text, score,
            { 
                document: d.id,
                entities: kg
            } AS metadata
        """
        )
    def prompt(self):
        instructions = (
        PROMPT + "\n\n" + "Contexto: {context}"
        )

        return ChatPromptTemplate.from_messages(
            [
                ("system", instructions),
                ("human", "{input}"),
            ]
        )

    def answer_with_rag(self, q):
        print("Finding similarities for query: ", q)
        answer = self.chunk_retriever.invoke({"input": q})["answer"]
        print("Answer: ", answer)
        return answer



