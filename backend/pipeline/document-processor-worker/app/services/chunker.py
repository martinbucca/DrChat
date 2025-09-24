import re
from unstructured_client import UnstructuredClient
from unstructured_client.models import operations, shared
from config import UNSTRUCTURED_API_KEY, UNSTRUCTURED_URL
from typing import Optional
import os

class Chunker:
    """
    A singleton class responsible for chunking documents using various strategies and parameters.
    The Chunker class interfaces with an external Unstructured API to partition documents into
    manageable chunks, supporting different chunking strategies, model configurations, and PDF splitting options.
    Attributes:
        strategy (str): The partitioning strategy to use (default: "hi_res").
        hi_res_model_name (str): The name of the high-resolution model to use (default: "yolox").
        element_exclude (list, optional): List of element types to exclude from chunking.
        extract_image_block_types (list, optional): List of block types (e.g., 'Image', 'Table') to extract.
        chunking_strategy (str): The strategy for chunking (default: "by_title").
        max_characters (int): Maximum number of characters per chunk (default: 1500).
        split_pdf_page (bool): Whether to split PDF by page (default: True).
        split_pdf_allow_failed (bool): Whether to allow failed PDF splits (default: True).
        split_pdf_concurrency_level (int): Number of concurrent PDF splits (default: 15).
        client (UnstructuredClient): Client for communicating with the Unstructured API.
    Methods:
        chunk_document(filepath: str, filename: Optional[str] = None) -> list[dict]:
            Chunks the document at the given file path and returns a list of chunked elements as dictionaries.
        get_instance(...):
            Returns the singleton instance of the Chunker class, creating it if it does not exist.
    """

    _instance = None

    def __init__(
        self,
        strategy: str = "hi_res",
        hi_res_model_name: str = "yolox",
        element_exclude: Optional[list] = None,
        extract_image_block_types: Optional[list] = None,
        chunking_strategy: str = "by_title",
        max_characters: int = 1500,
        split_pdf_page: bool = True,
        split_pdf_allow_failed: bool = True,
        split_pdf_concurrency_level: int = 15,
    ):
        self.strategy = strategy
        self.hi_res_model_name = hi_res_model_name
        self.element_exclude = element_exclude or ['Header', 'Footer', 'ListItem', 'Formula', 'UncategorizedText']
        self.extract_image_block_types = extract_image_block_types or ['Image', 'Table']
        self.chunking_strategy = chunking_strategy
        self.max_characters = max_characters
        self.split_pdf_page = split_pdf_page
        self.split_pdf_allow_failed = split_pdf_allow_failed
        self.split_pdf_concurrency_level = split_pdf_concurrency_level
        self.client = UnstructuredClient(
            api_key_auth=UNSTRUCTURED_API_KEY,
            server_url=UNSTRUCTURED_URL
        )

    def chunk_document(self, filepath: str, filename: Optional[str] = None) -> list[dict]:
        if filename is None:
            filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            files = shared.Files(
                content=f.read(),
                file_name=filename
            )

        request = operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=files,
                strategy=self.strategy,
                hi_res_model_name=self.hi_res_model_name,
                element_exclude=self.element_exclude,
                extract_image_block_types=self.extract_image_block_types,
                chunking_strategy=self.chunking_strategy,
                max_characters=self.max_characters,
                split_pdf_page=self.split_pdf_page,
                split_pdf_allow_failed=self.split_pdf_allow_failed,
                split_pdf_concurrency_level=self.split_pdf_concurrency_level
            )
        )
        
        response = self.client.general.partition(request=request).elements

        # POST-PROCESAMIENTO: Limpiar texto repetitivo
        cleaned_elements = []
        for element in response:
            if 'text' in element:
                # Remover encabezados/pies comunes
                element['text'] = self._clean_repetitive_text(element['text'])
            cleaned_elements.append(element)

        return cleaned_elements
    
    def _clean_repetitive_text(self, text: str) -> str:
        """Remover texto repetitivo como encabezados/pies de página"""
        patterns_to_remove = [
            r'Review\s+Regeneration\s+of\s+the\s+heart',
            r'EMBO\s+Molecular\s+Medicine',
            r'©\s+\d{4}\s+.*',
            r'http[s]?://\S+',  # URLs
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Collapsar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @classmethod
    def get_instance(cls,
        strategy: str = "hi_res",
        hi_res_model_name: str = "yolox",
        element_exclude: Optional[list] = None,
        extract_image_block_types: Optional[list] = None,
        chunking_strategy: str = "by_title",
        max_characters: int = 1500,
        split_pdf_page: bool = True,
        split_pdf_allow_failed: bool = True,
        split_pdf_concurrency_level: int = 15,
    ):
        if cls._instance is None:
            cls._instance = cls(
                strategy,
                hi_res_model_name,
                element_exclude,
                extract_image_block_types,
                chunking_strategy,
                max_characters,
                split_pdf_page,
                split_pdf_allow_failed,
                split_pdf_concurrency_level
            )
        return cls._instance
