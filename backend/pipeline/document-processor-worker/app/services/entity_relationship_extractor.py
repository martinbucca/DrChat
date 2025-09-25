import logging
import re
from typing import Dict, List, Tuple
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
import uuid
import unicodedata
import re

logger = logging.getLogger(__name__)

class EntityRelationshipExtractor:
    """
    Medical Entity and Relationship Extractor using specialized biomedical NER models.
    Uses pre-trained transformer models specifically designed for biomedical text.
    """
    
    _instance = None
    
    def __init__(self):
        """Initialize with biomedical NER model"""
        self.device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Initializing biomedical NER on device: {'GPU' if self.device == 0 else 'CPU'}")
        
        # Using BioBERT-based NER model for biomedical entities
        model_name = "d4data/biomedical-ner-all"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=self.device
            )
            logger.info("Biomedical NER model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading biomedical NER model: {e}")
            raise RuntimeError(f"Failed to initialize biomedical NER model: {e}")

    def _canonicalize(self, text: str) -> str:
        """Normalize text: remove accents, lowercase, remove punctuation, collapse spaces."""
        if not text:
            return ""
        # Normalize unicode (remueve tildes)
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        # Lowercase
        text = text.lower()
        # Keep alphanumerics and spaces only
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
    
    def extract_entities_and_relationships(self, text: str) -> Dict:
        """Extract medical entities and relationships from text using transformers model"""
        try:
            logger.info("Extracting entities using biomedical transformer model")
            return self._extract_with_transformers(text)
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"entities": [], "relationships": []}
    
    def _extract_with_transformers(self, text: str) -> Dict:
        """Extract entities using biomedical transformer model"""
        entities = []
        relationships = []

        # Split text into chunks if too long for the model
        max_length = 512
        text_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]

        for chunk in text_chunks:
            try:
                # Extract entities using NER pipeline
                ner_results = self.ner_pipeline(chunk)

                chunk_entities = []
                for entity in ner_results:
                    if entity['score'] > 0.7:
                        raw_text = entity['word']
                        canonical = self._canonicalize(raw_text)
                        entity_data = {
                            'id': str(uuid.uuid4()),
                            'text': raw_text,
                            'canonical_text': canonical,
                            'label': entity['entity_group'],
                            'start': int(entity['start']),
                            'end': int(entity['end']),
                            'confidence': float(entity['score'])
                        }
                        entities.append(entity_data)
                        chunk_entities.append(entity_data)
                
                # Extract relationships between nearby entities
                relationships.extend(self._extract_relationships(chunk_entities, chunk))
                
            except Exception as e:
                logger.warning(f"Error processing chunk: {e}")
                continue
        
        logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships using transformers")
        return {"entities": entities, "relationships": relationships}
    
    def _extract_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """Extract relationships between entities using proximity and patterns"""
        relationships = []

        if len(entities) < 2:
            return relationships

        # Solo considerar entidades con alta confianza
        high_confidence_entities = [e for e in entities if e.get('confidence', 0) > 0.7]

        for i, entity1 in enumerate(high_confidence_entities):
            for j, entity2 in enumerate(high_confidence_entities[i+1:], i+1):
                distance = abs(entity1['start'] - entity2['start'])
                if distance > 150:  # Aumentar distancia máxima
                    continue

                # Verificar que ambas entidades tengan canonical_text
                if not entity1.get('canonical_text') or not entity2.get('canonical_text'):
                    continue

        # Relationship patterns
        relation_patterns = {
            'TREATS': [r'treat(s|ed|ing|ment)', r'cure(s|d)', r'therap(y|ies)', r'medication for'],
            'CAUSES': [r'cause(s|d)', r'lead(s|ing) to', r'result(s|ed) in', r'trigger(s|ed)'],
            'ASSOCIATED_WITH': [r'associated with', r'related to', r'linked to', r'connected to'],
            'PART_OF': [r'part of', r'component of', r'located in', r'found in']
        }

        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # Check if entities are close enough (within 100 characters)
                distance = abs(entity1['start'] - entity2['start'])
                if distance > 100:
                    continue

                # Extract text between entities
                start_pos = min(entity1['end'], entity2['end'])
                end_pos = max(entity1['start'], entity2['start'])
                between_text = text[start_pos:end_pos].lower()

                # Check for relationship patterns
                for relation_type, patterns in relation_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, between_text):
                            relationship = {
                                'id': str(uuid.uuid4()),
                                'source': entity1.get('canonical_text', entity1.get('text')),
                                'source_surface': entity1.get('text'),
                                'target': entity2.get('canonical_text', entity2.get('text')),
                                'target_surface': entity2.get('text'),
                                'type': relation_type,
                                'confidence': 0.7
                            }
                            relationships.append(relationship)
                            break
        
        return relationships
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
