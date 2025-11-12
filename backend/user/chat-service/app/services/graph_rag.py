from langchain_openai import ChatOpenAI
from langchain_experimental.prompt_injection_identifier.hugging_face_identifier import HuggingFaceInjectionIdentifier, PromptInjectionException
from neo4j_graphrag.message_history import MessageHistory
from transformers import Pipeline
from typing import Optional, Callable, Any
from neo4j_graphrag.retrievers.base import Retriever
from langchain.prompts import PromptTemplate
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem
from app.services.chat_history import LLMMessage
from app.services.rag_result import RagResult
from app.services.chat_history import ChatMessageHistory
import logging

logger = logging.getLogger(__name__)
HuggingFaceInjectionIdentifier.model_rebuild()

class GraphRAGPipeline:
    """
    GraphRAGPipeline orchestrates a Retrieval-Augmented Generation (RAG) workflow. 
    It retrieves relevant context from a knowledge base, formats it along with message history, and constructs a prompt for a language model to generate a structured, 
    cited response.
    Attributes:
        llm: The language model used for answer generation.
        retriever: Component responsible for retrieving relevant documents or context.
        prompt_template: Custom or default prompt template for the LLM.
        default_response: Fallback answer when no relevant information is found.
        result_formatter: Optional function to format retriever results.
        history: Stores the conversation history for context.
    Methods:
        __init__(llm, retriever, prompt_template=None, default_response="No se encontró información relevante.", 
                 result_formatter=None, history=None):
            Initializes the pipeline with the LLM, retriever, prompt template, default response, 
            optional result formatter, and message history.
        search(query_text, session_id=None, retriever_config=None) -> RagResult:
            Executes a RAG search for the given query:
                - Retrieves relevant context using the retriever.
                - Formats the context and message history.
                - Constructs a prompt and invokes the LLM.
                - Updates message history with the latest user and assistant messages.
                - Returns a RagResult containing the answer and retriever results.
    """
    # TODO: MEJORAR PROMPT. Buscar articulos, videos, etc sobre como formatear, estructurar y optimizar prompts para RAG. 
    # Fijarse cual es la mejor manera de formatear el contexto para que el LLM lo entienda y lo use de la mejor manera posible.
    TEMPLATE = PromptTemplate.from_template(
        template="""
You are a medical assistant specialized in Covid 19.
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

    def __init__(
        self,
        llm: ChatOpenAI,
        retriever: Retriever,
        history: ChatMessageHistory,
        prompt_template: PromptTemplate = None,
        default_response: str = "No relevant information was found. Please make sure you have uploaded documents to the system.",
        result_formatter: Optional[Callable[[Any], RetrieverResultItem]] = None,
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt_template = prompt_template or self.TEMPLATE
        self.default_response = default_response
        self.result_formatter = result_formatter
        self.history = history
        self.injection_identifier = HuggingFaceInjectionIdentifier()

    def search(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        created_at: Optional[str] = None,
        retriever_config: Optional[dict] = None,
    ) -> RagResult:
        
        self.history.add_message(LLMMessage(role="user", content=query_text), session_id, created_at)
        if self.verify_prompt_injection(query_text):
            default_response = "⚠️ For the best experience, please keep your requests aligned with the assistant’s intended scope."
            logger.warning(f"Prompt injection detected in query: {query_text}")
            created_at = None
            if self.history:
                created_at = self.history.add_message(
                    LLMMessage(role="ai", content=default_response),
                    session_id,
                )

            return RagResult(
                answer=default_response,
                retriever_result=RetrieverResult(items=[]),
                created_at=created_at,
            )

        retriever_config = retriever_config or {}
        filters = {
            "session_id": {
                "$eq": session_id
            }
        }
        
        try:
            retriever_result: RetrieverResult = self.retriever.search(
                query_text=query_text,
                filters=filters,
                **retriever_config
            )
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            raise
            
        if len(retriever_result.items) == 0:
            logger.warning(f"No relevant documents found for query")
            
            created_at = None
            if self.history:
                created_at = self.history.add_message(
                    LLMMessage(role="ai", content=self.default_response),
                    session_id,
                )

            return RagResult(
                answer=self.default_response,
                retriever_result=retriever_result,
                created_at=created_at,
            )
        context_formatted = "\n\n"
        for item in retriever_result.items:
            context_formatted += "========================================================\n"
            context_formatted += item.content
            context_formatted += "========================================================\n"

        if self.history:
            messages = self.history.messages(session_id)
            formatted_history = ""
            for msg in messages:
                formatted_history += f"{msg['role']}: {msg['content']}\n"
            if formatted_history == "":
                formatted_history = "No previous messages."

        prompt = self.prompt_template.format(
            query_text=query_text,
            context=context_formatted,
            message_history=formatted_history,
        )

        llm_response = self.llm.invoke(prompt)

        created_at = self.history.add_message(LLMMessage(role="ai", content=llm_response.content), session_id)

        return RagResult(
            answer=llm_response.content,
            retriever_result=retriever_result,
            created_at=created_at
        )
    

    def verify_prompt_injection(self, query_text: str) -> bool:
        try:
            self.injection_identifier._run(query_text)
            return False
        except PromptInjectionException:
            return True
        except Exception as e:
            logger.error(f"Error during prompt injection detection: {e}")
            return False


