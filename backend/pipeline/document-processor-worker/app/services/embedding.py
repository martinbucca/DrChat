from app.config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_EMBEDDINGS_MODEL, AZURE_OPENAI_ENDPOINT
from langchain_openai import AzureOpenAIEmbeddings

class Embedding:
    """
    Singleton class for managing an embedding model instance.
    This class ensures that only one instance of the embedding model is created and reused throughout the application.
    It provides access to the underlying Embeddigg Provider object via the `embedder` property.
    Attributes:
        _instance (Embedding): The singleton instance of the Embedding class.
        _embedder (HuggingFaceEmbeddings): The embedding provider model instance.
    Args:
        api_key (str, optional): API key for authentication if required by the embedding model.
    Methods:
        get_instance(api_key=None): Returns the singleton instance of the Embedding class.
        embedder: Property to access the HuggingFaceEmbeddings instance.
    """

    _instance = None

    def __init__(self, api_key=None):
        self._embedder = AzureOpenAIEmbeddings(model=AZURE_OPENAI_EMBEDDINGS_MODEL)

    @classmethod
    def get_instance(cls, api_key=None):
        if cls._instance is None:
            cls._instance = cls(api_key)
        return cls._instance
    
    @property
    def embedder(self):
        return self._embedder
      