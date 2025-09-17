import logging
import re
from typing import Dict, List, Tuple
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
import uuid

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
            # Fallback to regex patterns if model fails
            self.ner_pipeline = None
            self.medical_patterns = self._load_medical_patterns()
            logger.info("Falling back to regex-based NER")
    
    def _load_medical_patterns(self) -> Dict[str, List[str]]:
        """Load medical patterns for fallback regex-based NER"""
        return {
            'diseases': [
                r'\b(diabetes|hypertension|cancer|tumor|carcinoma|infection|inflammation|syndrome|disease|disorder|condition)\b',
                r'\b(COVID-19|HIV|AIDS|tuberculosis|pneumonia|bronchitis|asthma|COPD)\b',
                r'\b(heart failure|stroke|myocardial infarction|coronary artery disease)\b'
            ],
            'drugs': [
                r'\b(aspirin|ibuprofen|acetaminophen|morphine|insulin|metformin|lisinopril)\b',
                r'\b(antibiotic|antiviral|antifungal|chemotherapy|immunotherapy)\b',
                r'\b(medication|drug|treatment|therapy|prescription)\b'
            ],
            'anatomy': [
                r'\b(heart|lung|brain|liver|kidney|stomach|intestine|muscle|bone|blood)\b',
                r'\b(cell|tissue|organ|vessel|artery|vein|nerve|gland)\b'
            ],
            'proteins': [
                r'\b(protein|enzyme|hormone|antibody|antigen|receptor|gene)\b',
                r'\b(insulin|hemoglobin|albumin|collagen|keratin)\b'
            ]
        }
    
    def extract_entities_and_relationships(self, text: str) -> Dict:
        """Extract medical entities and relationships from text"""
        try:
            if self.ner_pipeline:
                return self._extract_with_transformers(text)
            else:
                return self._extract_with_regex(text)
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
                    if entity['score'] > 0.7:  # High confidence threshold
                        entity_data = {
                            'id': str(uuid.uuid4()),  # Generate unique ID for each entity
                            'text': entity['word'],
                            'label': entity['entity_group'],
                            'start': int(entity['start']),
                            'end': int(entity['end']),
                            'confidence': float(entity['score'])  # Convert numpy float32 to Python float
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
    
    def _extract_with_regex(self, text: str) -> Dict:
        """Fallback extraction using regex patterns"""
        entities = []
        relationships = []
        
        for entity_type, patterns in self.medical_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_data = {
                        'id': str(uuid.uuid4()),  # Generate unique ID for each entity
                        'text': match.group(),
                        'label': entity_type,
                        'start': int(match.start()),
                        'end': int(match.end()),
                        'confidence': 0.8  # Already a Python float
                    }
                    entities.append(entity_data)
        
        # Extract simple relationships for regex mode
        relationships = self._extract_simple_relationships(entities, text)
        
        logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships using regex")
        return {"entities": entities, "relationships": relationships}
    
    def _extract_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """Extract relationships between entities using proximity and patterns"""
        relationships = []
        
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
                                'id': str(uuid.uuid4()),  # Generate unique ID for each relationship
                                'source': entity1['text'],
                                'target': entity2['text'],
                                'type': relation_type,
                                'confidence': 0.7
                            }
                            relationships.append(relationship)
                            break
        
        return relationships
    
    def _extract_simple_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """Extract simple relationships for regex mode"""
        relationships = []
        
        # Simple co-occurrence based relationships
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                distance = abs(entity1['start'] - entity2['start'])
                if distance < 50:  # Entities are very close
                    relationship = {
                        'id': str(uuid.uuid4()),  # Generate unique ID for each relationship
                        'source': entity1['text'],
                        'target': entity2['text'],
                        'type': 'RELATED_TO',
                        'confidence': 0.6
                    }
                    relationships.append(relationship)
        
        return relationships
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
