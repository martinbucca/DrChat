from app.services.chunker import Chunker
from app.services.driver import Neo4jDriver
from app.services.embedding import Embedding
from app.services.graph_builder import GraphBuilder
from app.services.documents_processor import DocumentsProcessor
from app.services.llm import LLM
from app.services.entity_relationship_extractor import EntityRelationshipExtractor
import asyncio
from aiokafka import AIOKafkaConsumer

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

"""
async def process_message(filepath: str, sem: asyncio.Semaphore):
    async with sem:  # Límite de concurrencia
        await asyncio.to_thread(document_processor_instance.process_file, filepath)


async def consume():
    consumer = AIOKafkaConsumer(
        'document-topic',
        bootstrap_servers='localhost:9092',
        group_id="kg-workers"
    )
    await consumer.start()
    sem = asyncio.Semaphore(4)  # Máximo 4 archivos en paralelo
    try:
        async for msg in consumer:
            filepath = msg.value.decode()
            print(f"[Kafka] Mensaje recibido: {filepath}")
            asyncio.create_task(process_message(filepath, sem))
    finally:
        await consumer.stop()
"""
        

if __name__ == "__main__":
    # ACA TENDRIA QUE IR LA LOGICA PARA LEER ARCHIVO DEL BUCKET.
    # ELIMINAR DIRECTORIO documents (se usa para probar localmente)
    file_paths = "./app/documents/emmm0003-0701.pdf"
    document_processor_instance.process_file(file_paths)
    #asyncio.run(consume())





