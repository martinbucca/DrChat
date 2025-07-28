from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
#TODO: Esto esta bien? 
from core.logging import logger as log

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_document(self, doc_path: str) -> list[Document]:
        try:
            log.info(f"Processing document: {doc_path}")
            document = self._load_document(doc_path)
            chunks = self._chunk_document(document)
            return chunks
        except Exception as e:
            log.error(f"Error processing document {doc_path}: {str(e)}")
            raise e
    
    def _load_document(self, doc_path: str) -> list[Document]:
        '''
        Carga un documento PDF y lo convierte en una lista de objetos Document.
        '''
        loader = PyPDFLoader(doc_path)
        document = loader.load()
        return document
    
    def _chunk_document(self, document: list[Document]) -> list[Document]:
        '''
        Divide un documento en chunks utilizando alguna tecnica de división de texto.
        '''
        chunks = self.text_splitter.split_documents(document)
        return chunks