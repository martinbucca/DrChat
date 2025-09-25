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
        
        # Using BioBERT-based NER model for biomedical entities (for comparison)
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
            logger.info("BioBERT NER model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading BioBERT NER model: {e}")
            raise RuntimeError(f"Failed to initialize BioBERT NER model: {e}")

    def _canonicalize(self, text: str) -> str:
        """Normalize text: remove accents, lowercase, remove punctuation, collapse spaces."""
        if not text or not text.strip():
            return ""
        
        # Limpiar texto inicial
        text = text.strip()
        
        # Filtrar tokens BERT fragmentados y entidades problemáticas específicas
        if (text.startswith('##') or 
            text.endswith(' ' + 's') or  # Posesivos mal cortados como "heart ' s"
            text in ['esahc'] or  # Tokens extraños
            re.match(r'^[β-ω\-–+%\d\s]+$', text) or  # Solo símbolos griegos, números y símbolos
            len(text.split()) == 1 and len(text) < 6 and text.lower() in ['human', 'pulse', 'natal', 'gal', 'low', 'med'] or
            text.endswith((' de', ' the', ' of', ' in', ' to', ' for', ' with', ' and', ' or', ' +', ' -')) or
            text.startswith(('of ', 'the ', 'and ', 'or ', 'in ', 'to ', '+ ', '- '))):
            return ""
        
        # Normalize unicode (remueve tildes)
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        
        # Limpiar caracteres especiales problemáticos pero mantener espacios
        text = re.sub(r'[^\w\s]', ' ', text)  # Solo palabras y espacios
        
        # Lowercase
        text = text.lower()
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Filtrar textos muy cortos, stop words y palabras genéricas después del procesamiento
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'by', 'at', 'on', 
            'is', 'are', 'was', 'were', 'this', 'that', 'these', 'those', 'from', 'new', 'old', 
            'good', 'bad', 'human', 'factors', 'effects', 'delivered', 'committed', 'natal', 
            'pulse', 'ous', 'ener', 'che', 'mer', 'ogen', 'oca', 'brosis', 'sp', 'gal', 'med'
        }
        
        if (len(text) < 4 or 
            text in stop_words or
            re.match(r'^[a-z]{1,3}$', text) or  # Solo 1-3 letras
            len(text.replace(' ', '')) < 3):  # Muy poco contenido real
            return ""
            
        return text
    
    def extract_entities_and_relationships(self, text: str) -> Dict:
        """Extract medical entities and relationships from text using BioBERT model"""
        try:
            logger.info("Extracting entities using BioBERT transformer model")
            return self._extract_with_transformers(text)
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"entities": [], "relationships": []}
    
    def _extract_with_transformers(self, text: str) -> Dict:
        """Extract entities using BioBERT transformer model"""
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
                    # Filtros más estrictos específicos para BioBERT
                    raw_text = entity['word'].strip()
                    
                    # Filtrar entidades con problemas comunes de BioBERT
                    if (entity['score'] > 0.88 and  # Confianza más alta para BioBERT
                        len(raw_text) >= 6 and  # Mínimo 6 caracteres para BioBERT
                        not raw_text.isdigit() and  # No solo números
                        not raw_text.startswith('##') and  # Filtrar tokens fragmentados de BERT
                        not raw_text.endswith((' ', '-', '_', '+', '##')) and  # No terminar con caracteres problemáticos
                        not raw_text.startswith((' ', '-', '_', '+')) and  # No empezar con caracteres problemáticos
                        not re.match(r'^[a-zA-Z]{1,4}$', raw_text) and  # No palabras muy cortas sueltas
                        not re.match(r'^[\d\s\-–%+]+$', raw_text) and  # No solo números y símbolos
                        not raw_text.lower() in ['the', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'by', 'this', 'that', 'these', 'those', 'from', 
                                                'human', 'factors', 'effects', 'delivered', 'committed', 'natal', 'pulse'] and  # Stop words expandidas
                        not re.match(r'^[^\w\s]+$', raw_text) and  # No solo caracteres especiales
                        len(raw_text.replace(' ', '').replace('-', '').replace('+', '')) > 3):  # Contenido real mínimo
                        
                        canonical = self._canonicalize(raw_text)
                        
                        # Verificar que la canonicalización no esté vacía y tenga longitud mínima
                        if canonical and len(canonical) >= 4:
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
        
        # Filtrar entidades duplicadas o muy similares
        entities = self._deduplicate_entities(entities)
        
        logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships using transformers")
        return {"entities": entities, "relationships": relationships}
    
    def _extract_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """Extract relationships between entities using proximity and patterns"""
        relationships = []

        if len(entities) < 2:
            return relationships

        # Solo considerar entidades con alta confianza (más estricto para BioBERT)
        high_confidence_entities = [e for e in entities if e.get('confidence', 0) > 0.85]
        
        if len(high_confidence_entities) < 2:
            return relationships

        # Relationship patterns
        relation_patterns = {
            'TREATS': [r'treat(s|ed|ing|ment)', r'cure(s|d)', r'therap(y|ies)', r'medication for'],
            'CAUSES': [r'cause(s|d)', r'lead(s|ing) to', r'result(s|ed) in', r'trigger(s|ed)'],
            'ASSOCIATED_WITH': [r'associated with', r'related to', r'linked to', r'connected to'],
            'PART_OF': [r'part of', r'component of', r'located in', r'found in']
        }

        for i, entity1 in enumerate(high_confidence_entities):
            for j, entity2 in enumerate(high_confidence_entities[i+1:], i+1):
                # Evitar auto-relaciones (misma entidad)
                if (entity1.get('canonical_text') == entity2.get('canonical_text') or
                    entity1.get('text') == entity2.get('text')):
                    continue
                
                # Check if entities are close enough (increased range for more relationships)
                distance = abs(entity1['start'] - entity2['start'])
                if distance > 150:  # Increased from 100 to get more relationships
                    continue

                # Verificar que ambas entidades tengan canonical_text válido
                if (not entity1.get('canonical_text') or 
                    not entity2.get('canonical_text') or
                    len(entity1.get('canonical_text', '')) < 3 or  # Minimum 3 chars
                    len(entity2.get('canonical_text', '')) < 3):
                    continue

                # Extract text between entities
                start_pos = min(entity1['end'], entity2['end'])
                end_pos = max(entity1['start'], entity2['start'])
                between_text = text[start_pos:end_pos].lower()

                # Solo crear relación si hay texto significativo entre entidades (reducido de 3 a 2)
                if len(between_text.strip()) < 2:
                    continue

                # Check for relationship patterns
                relationship_found = False
                for relation_type, patterns in relation_patterns.items():
                    if relationship_found:
                        break
                    for pattern in patterns:
                        if re.search(pattern, between_text):
                            relationship = {
                                'id': str(uuid.uuid4()),
                                'source': entity1.get('canonical_text'),
                                'source_surface': entity1.get('text'),
                                'target': entity2.get('canonical_text'),
                                'target_surface': entity2.get('text'),
                                'type': relation_type,
                                'confidence': 0.8  # Mayor confianza para relaciones
                            }
                            relationships.append(relationship)
                            relationship_found = True
                            break
        
        return relationships
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar entities, keeping the one with highest confidence"""
        if not entities:
            return entities
        
        deduplicated = []
        seen_canonical = {}
        
        # Sort by confidence descending to keep best entities first
        sorted_entities = sorted(entities, key=lambda x: x.get('confidence', 0), reverse=True)
        
        for entity in sorted_entities:
            canonical = entity.get('canonical_text', '').strip()
            text = entity.get('text', '').strip()
            
            if not canonical:
                continue
                
            # Check for exact duplicate canonical text
            if canonical in seen_canonical:
                continue
                
            # Check for very similar entities (substring relationship)
            is_duplicate = False
            for seen_canon in seen_canonical.keys():
                # If current entity is a substring of existing or vice versa
                if (canonical in seen_canon and len(canonical) < len(seen_canon) * 0.8) or \
                   (seen_canon in canonical and len(seen_canon) < len(canonical) * 0.8):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_canonical[canonical] = True
                deduplicated.append(entity)
        
        logger.info(f"Deduplicated entities: {len(entities)} -> {len(deduplicated)}")
        return deduplicated
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
