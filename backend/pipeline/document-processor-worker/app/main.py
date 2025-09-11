from services.chunker import Chunker
from services.driver import Neo4jDriver
from services.embedding import Embedding
from services.graph_builder import GraphBuilder
from services.documents_processor import DocumentsProcessor
from services.llm import LLM
from services.entity_relationship_extractor import EntityRelationshipExtractor
from services.file_status_service import FileStatusService
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, KAFKA_GROUP_ID
from kafka import KafkaConsumer
import json
import logging
import time
import nltk

# Download required NLTK data
try:
    nltk.download('punkt_tab', quiet=True)
    nltk.download('punkt', quiet=True)
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

file_status_service = FileStatusService.get_instance()

logger.info("All services initialized successfully")

def process_file_message(file_path: str, file_id: str = None, session_id: str = None):
    """Process a file from a Kafka message"""
    try:
        logger.info(f"Processing file: {file_path} for session: {session_id}")
        
        # Update status to 'processing'
        if file_id:
            success = file_status_service.update_file_status(file_id, "processing")
            if success:
                logger.info(f"Updated file {file_id} status to 'processing'")
            else:
                logger.warning(f"Failed to update file {file_id} status to 'processing'")
        
        # Process the file
        document_processor_instance.process_file(file_path, session_id=session_id)
        
        # Update status to 'processed'
        if file_id:
            success = file_status_service.update_file_status(file_id, "processed")
            if success:
                logger.info(f"Updated file {file_id} status to 'processed'")
            else:
                logger.warning(f"Failed to update file {file_id} status to 'processed'")
        
        logger.info(f"Successfully processed file: {file_path} for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing file {file_path} for session {session_id}: {str(e)}")
        
        # Update status to 'error' if processing failed
        if file_id:
            success = file_status_service.update_file_status(file_id, "error")
            if success:
                logger.info(f"Updated file {file_id} status to 'error'")
            else:
                logger.warning(f"Failed to update file {file_id} status to 'error'")
        
        raise

def consume_messages():
    """Consume messages from Kafka and process files"""
    logger.info(f"Starting Kafka consumer for topic: {KAFKA_TOPIC}")
    logger.info(f"Kafka servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Consumer group: {KAFKA_GROUP_ID}")
    
    # Configure consumer with retry logic
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            logger.info("Connected to Kafka successfully")
            break
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
    
    try:
        for message in consumer:
            try:
                # Extract file_path from the message
                message_data = message.value
                file_path = message_data.get('file_path')
                file_id = message_data.get('file_id')
                session_id = message_data.get('session_id')
                
                if not file_path:
                    logger.error(f"No file_path found in message: {message_data}")
                    continue
                
                logger.info(f"Received Kafka message for file ID: {file_id}, session: {session_id}, path: {file_path}")
                
                # Process the file
                process_file_message(file_path, file_id, session_id)
                
            except Exception as e:
                logger.error(f"Error processing Kafka message: {str(e)}")
                # Continue processing other messages even if one fails
                continue
                
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {str(e)}")
        raise
    finally:
        consumer.close()
        logger.info("Kafka consumer closed")

if __name__ == "__main__":
    logger.info("Starting Document Processor Worker")
    consume_messages()





