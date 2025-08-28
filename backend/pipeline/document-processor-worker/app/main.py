from app.services.chunker import Chunker
from app.services.driver import Neo4jDriver
from app.services.embedding import Embedding
from app.services.graph_builder import GraphBuilder
from app.services.documents_processor import DocumentsProcessor
from app.services.llm import LLM
from app.services.entity_relationship_extractor import EntityRelationshipExtractor

driver_instance = Neo4jDriver.get_instance()
driver = driver_instance.driver

embedding_instance = Embedding.get_instance()
embedder = embedding_instance.embedder

llm_instance = LLM.get_instance()
llm = llm_instance.llm

chunker_instance = Chunker.get_instance()

entity_relationship_extractor_instance = EntityRelationshipExtractor.get_instance(llm)

graph_builder_instance = GraphBuilder.get_instance(driver, embedder, entity_relationship_extractor_instance)

document_processor_instance = DocumentsProcessor.get_instance(
    chunker_instance,
    graph_builder_instance
)

if __name__ == "__main__":
    # ACA TENDRIA QUE IR LA LOGICA PARA LEER ARCHIVOS DEL BUCKET.
    # ELIMINAR DIRECTORIO documents (se usa para probar localmente)
    file_paths = ["./app/documents/emmm0003-0701.pdf", "./app/documents/fnut-12-1613721.pdf"]
    document_processor_instance.process_files(file_paths)





