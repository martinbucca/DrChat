from langchain_openai import ChatOpenAI
from app.config import LLM_NER_MODEL, GROQ_API_BASE

class LLM:
    """
    A singleton class for managing a generic Large Language Model (LLM) instance.
    This class provides a thread-safe singleton interface to initialize and access a generic LLM client.
    It is designed to encapsulate the configuration and instantiation of the LLM, ensuring that only one
    instance exists throughout the application lifecycle.
    Attributes:
        _instance (LLM): The singleton instance of the LLM class.
        _llm: The underlying LLM client instance.
    Args:
        model_params (dict): Parameters for configuring the LLM model.
        api_key (str): API key for authenticating with the LLM provider.
    Methods:
        get_instance(model_params=None, api_key=None):
            Returns the singleton instance of the LLM class, creating it if necessary.
        llm:
            Property that returns the underlying LLM client instance.
    """

    _instance = None

    def __init__(self, model_params, api_key):
        self._llm = ChatOpenAI(
            model_name=LLM_NER_MODEL,
            temperature=0,
            openai_api_base=GROQ_API_BASE
        )

    @classmethod
    def get_instance(cls, model_params=None, api_key=None):
        if model_params is None:
            model_params = {}
        if cls._instance is None:
            cls._instance = cls(model_params, api_key)
        return cls._instance
    
    @property
    def llm(self):
        return self._llm
