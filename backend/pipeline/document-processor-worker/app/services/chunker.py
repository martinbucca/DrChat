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
        chunking_strategy: str = "basic",
        max_characters: int = 800,
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
        self.new_after_n_chars = int(max_characters * 0.6)  # 480 chars - crear nuevo chunk antes
        self.combine_text_under_n_chars = int(max_characters * 0.15)  # 120 chars - combinar chunks pequeños
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
                new_after_n_chars=self.new_after_n_chars,
                combine_text_under_n_chars=self.combine_text_under_n_chars,
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
        """Remover texto repetitivo y optimizar para detección de relaciones médicas"""
        if not text or not text.strip():
            return ""
            
        # Patrones de limpieza básica
        patterns_to_remove = [
            r'Review\s+Regeneration\s+of\s+the\s+heart',
            r'EMBO\s+Molecular\s+Medicine',
            r'©\s+\d{4}\s+.*',
            r'http[s]?://\S+',  # URLs
            r'\b[A-Z]{2,}\s+\d{4}\b',  # Códigos de publicación
            r'\bFig\.\s*\d+[a-z]?\b',  # Referencias a figuras
            r'\bTable\s+\d+\b',  # Referencias a tablas
            r'\(\s*see\s+.*?\)',  # Referencias cruzadas
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Optimización para relaciones médicas:
        # Normalizar espacios alrededor de conectores importantes
        medical_connectors = [
            r'\s+and\s+', r'\s+or\s+', r'\s+with\s+', r'\s+in\s+', r'\s+of\s+', 
            r'\s+for\s+', r'\s+by\s+', r'\s+via\s+', r'\s+through\s+',
            r'\s+causes?\s+', r'\s+leads?\s+to\s+', r'\s+results?\s+in\s+',
            r'\s+associated\s+with\s+', r'\s+related\s+to\s+', r'\s+linked\s+to\s+',
            r'\s+affects?\s+', r'\s+influences?\s+', r'\s+regulates?\s+'
        ]
        
        for connector_pattern in medical_connectors:
            # Normalizar espacios alrededor de conectores (importante para relaciones)
            normalized = connector_pattern.replace(r'\s+', ' ').replace(r'\s+', ' ')
            text = re.sub(connector_pattern, normalized, text, flags=re.IGNORECASE)

        # Collapsar espacios múltiples PERO preservar estructura de párrafos
        text = re.sub(r'[ \t]+', ' ', text)  # Solo espacios horizontales
        text = re.sub(r'\n{3,}', '\n\n', text)  # Máximo 2 saltos de línea
        
        return text.strip()

    @classmethod
    def get_instance(cls,
        strategy: str = "hi_res",
        hi_res_model_name: str = "yolox",
        element_exclude: Optional[list] = None,
        extract_image_block_types: Optional[list] = None,
        chunking_strategy: str = "basic",
        max_characters: int = 800,
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
