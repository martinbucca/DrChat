from langchain_openai import ChatOpenAI
from neo4j_graphrag.message_history import MessageHistory
from typing import Optional, Callable, Any
from neo4j_graphrag.retrievers.base import Retriever
from langchain.prompts import PromptTemplate
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem, LLMMessage
from rag_result import RagResult

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
        __init__(llm, retriever, prompt_template=None, default_response="No relevant information found.", 
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

    def __init__(
        self,
        llm: ChatOpenAI,
        retriever: Retriever,
        prompt_template: PromptTemplate = None,
        default_response: str = "No relevant information found.",
        result_formatter: Optional[Callable[[Any], RetrieverResultItem]] = None,
        history: Optional[MessageHistory] = None,
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt_template = prompt_template or self.TEMPLATE
        self.default_response = default_response
        self.result_formatter = result_formatter
        self.history = history

    def search(
        self,
        query_text: str,
        session_id: Optional[str] = None,
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




