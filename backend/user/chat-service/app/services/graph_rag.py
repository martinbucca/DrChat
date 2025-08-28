import neo4j
import os
import ast
from neo4j_graphrag.retrievers import VectorCypherRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from neo4j_graphrag.message_history import InMemoryMessageHistory
from neo4j_graphrag.message_history import MessageHistory
from dataclasses import dataclass
from typing import Optional, List, Callable, Any, Union
from neo4j_graphrag.retrievers.base import Retriever
from langchain.prompts import PromptTemplate
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem, LLMMessage

from dotenv import load_dotenv
load_dotenv()

EMBEDDINGS_MODEL = "sentence-transformers/msmarco-distilbert-base-tas-b"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
URI = os.getenv('NEO4J_URI')
AUTH = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))

os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY")


@dataclass
class RagResult():
    answer: str
    retriever_result: Optional[RetrieverResult] = None


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


# TODO: MEJORAR PROMPT. Buscar articulos, videos, etc sobre como formatear, estructurar y optimizar prompts para RAG. 
# Fijarse cual es la mejor manera de formatear el contexto para que el LLM lo entienda y lo use de la mejor manera posible.
custom_template = PromptTemplate.from_template(
template="""
You are a medical assistant specialized in systemic lupus erythematosus (SLE).
Always:
- Provide a concise, structured answer
- Use the retrieved context to support your response
- Cite the most relevant information from context
- If the answer is uncertain or context is missing, state that clearly
- Do NOT fabricate information

Message History:
{message_history}   

Context:
{context}

Question:
{query_text}

Answer:
"""
)   


# TODO: Fijarse Neo4jMessageHistory
history = InMemoryMessageHistory()




class GraphRAGPipeline:
    def __init__(
        self,
        llm: ChatOpenAI,
        retriever: Retriever,
        prompt_template: PromptTemplate,
        default_response: str = "No relevant information found.",
        result_formatter: Optional[Callable[[Any], RetrieverResultItem]] = None,
        history: Optional[MessageHistory] = None,
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt_template = prompt_template
        self.default_response = default_response
        self.result_formatter = result_formatter
        self.history = history

    def search(
        self,
        query_text: str,
        retriever_config: Optional[dict] = None,
    ) -> RagResult:
        retriever_config = retriever_config or {}

        retriever_result: RetrieverResult = self.retriever.search(
            query_text=query_text,
            **retriever_config
        )

        if len(retriever_result.items) == 0:
            return RagResult(
                answer=self.default_response,
                retriever_result=retriever_result
            )
        
        context_formatted = "\n\n"
        for item in retriever_result.items:
            context_formatted += "========================================================\n"
            context_formatted += f"Score: {item.metadata['score']}\n\n"
            context_formatted += f"Document: {item.metadata['document'].split('/')[-1].rsplit('.', 1)[0]}\n\n"
            context_formatted += f"Text: {item.metadata['text'].replace('\\n', chr(10))}\n\n"
            context_formatted += f"These are the entities mentioned in the text: {', '.join([f'{ent['id']} ({ent['label']})' for ent in item.metadata['entities']])}\n\n"
            context_formatted += f"Page: {item.metadata['page']}\n\n"
            context_formatted += "========================================================\n"


        


        if self.history:
            messages = self.history.messages
            formatted_history = ""
            for msg in messages:
                # Aceptamos tanto LLMMessage como dict
                role = msg["role"]
                content = msg["content"]
                formatted_history += f"{role}: {content}\n"

        prompt = self.prompt_template.format(
            query_text=query_text,
            context=context_formatted,
            message_history=formatted_history,
        )

        print("===== Prompt enviado al LLM =====")
        print(prompt)
        print("=================================")

        llm_response = self.llm.invoke(prompt)

        self.history.add_message(LLMMessage(role="user", content=query_text))
        self.history.add_message(LLMMessage(role="assistant", content=llm_response.content))
        print(f"Answer: {llm_response.content}")

        return RagResult(
            answer=llm_response.content,
            retriever_result=retriever_result
        )


llm = ChatOpenAI(
    model_name=MODEL,
    temperature=0,
    openai_api_base=GROQ_API_BASE
)

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)

embedder = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)

retriever = VectorCypherRetriever(driver=driver, index_name="chunkVector", embedder=embedder, retrieval_query=RETRIEVAL_QUERY)

graphrag = GraphRAGPipeline(llm=llm, retriever=retriever, prompt_template=custom_template, history=history)





# What are the main reasons for patient-physician discordance in SLE?