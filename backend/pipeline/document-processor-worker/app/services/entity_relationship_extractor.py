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
                pattern_relationships = self._extract_relationships(chunk_entities, chunk)
                relationships.extend(pattern_relationships)
                
                # Extract type-based relationships
                type_relationships = self._extract_type_based_relationships(chunk_entities)
                relationships.extend(type_relationships)
                
            except Exception as e:
                logger.warning(f"Error processing chunk: {e}")
                continue
        
        # Filtrar entidades duplicadas o muy similares
        entities = self._deduplicate_entities(entities)
        
        # Extract inter-chunk relationships using all entities
        inter_chunk_relationships = self._extract_inter_chunk_relationships(entities, text)
        relationships.extend(inter_chunk_relationships)
        
        # Deduplicate relationships
        relationships = self._deduplicate_relationships(relationships)
        
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

        # Relationship patterns - Expandidos para medicina
        relation_patterns = {
            'TREATS': [
                r'treat(s|ed|ing|ment)', r'cure(s|d)', r'therap(y|ies)', r'medication for',
                r'administered for', r'prescribed for', r'used to treat', r'effective against',
                r'therapeutic for', r'remedy for', r'applied to', r'indicated for'
            ],
            'CAUSES': [
                r'cause(s|d)', r'lead(s|ing) to', r'result(s|ed) in', r'trigger(s|ed)',
                r'induce(s|d)', r'precipitate(s|d)', r'provoke(s|d)', r'bring(s) about',
                r'responsible for', r'due to', r'secondary to', r'attributed to'
            ],
            'PREVENTS': [
                r'prevent(s|ed|ing|ion)', r'avoid(s|ed|ing)', r'protect(s|ed|ing) against',
                r'reduce(s|d) risk', r'lower(s|ed) risk', r'prophylaxis', r'inhibit(s|ed)',
                r'block(s|ed)', r'suppress(es|ed)'
            ],
            'IMPROVES': [
                r'improve(s|d)', r'enhance(s|d)', r'increase(s|d)', r'boost(s|ed)',
                r'restore(s|d)', r'repair(s|ed)', r'regenerate(s|d)', r'strengthen(s|ed)',
                r'optimize(s|d)', r'support(s|ed)'
            ],
            'LOCATED_IN': [
                r'located in', r'found in', r'present in', r'within the', r'inside the',
                r'part of', r'component of', r'region of', r'situated in', r'contained in'
            ],
            'ASSOCIATED_WITH': [
                r'associated with', r'related to', r'linked to', r'connected to',
                r'correlated with', r'accompanied by', r'co-occurs with', r'seen with'
            ]
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
    
    def _extract_type_based_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Extract relationships based on entity types using medical logic"""
        relationships = []
        
        if len(entities) < 2:
            return relationships
            
        # Solo considerar entidades con alta confianza
        high_confidence_entities = [e for e in entities if e.get('confidence', 0) > 0.85]
        
        if len(high_confidence_entities) < 2:
            return relationships
            
        # Reglas médicas basadas en tipos de entidad de BioBERT
        type_rules = {
            ('Therapeutic_procedure', 'Disease_disorder'): 'TREATS',
            ('Disease_disorder', 'Sign_symptom'): 'MANIFESTS_AS',
            ('Diagnostic_procedure', 'Disease_disorder'): 'DIAGNOSES',
            ('Lab_value', 'Disease_disorder'): 'INDICATES',
            ('Biological_structure', 'Disease_disorder'): 'AFFECTED_BY',
            ('Therapeutic_procedure', 'Sign_symptom'): 'ALLEVIATES',
            ('Diagnostic_procedure', 'Biological_structure'): 'EXAMINES',
            ('Lab_value', 'Therapeutic_procedure'): 'MONITORS',
            ('Detailed_description', 'Diagnostic_procedure'): 'DESCRIBES',
            ('Clinical_event', 'Disease_disorder'): 'INVOLVES'
        }
        
        for i, entity1 in enumerate(high_confidence_entities):
            for j, entity2 in enumerate(high_confidence_entities[i+1:], i+1):
                # Evitar auto-relaciones
                if (entity1.get('canonical_text') == entity2.get('canonical_text') or
                    entity1.get('text') == entity2.get('text')):
                    continue
                    
                # Verificar distancia (más permisiva para relaciones tipo-based)
                distance = abs(entity1['start'] - entity2['start'])
                if distance > 200:  # Un poco más permisiva
                    continue
                    
                # Verificar validez de entidades
                if (not entity1.get('canonical_text') or 
                    not entity2.get('canonical_text') or
                    len(entity1.get('canonical_text', '')) < 3 or
                    len(entity2.get('canonical_text', '')) < 3):
                    continue
                
                # Obtener tipos de entidad
                type1 = entity1.get('label', '')
                type2 = entity2.get('label', '')
                
                # Buscar regla que coincida (en ambas direcciones)
                relation_type = None
                source_entity = entity1
                target_entity = entity2
                
                if (type1, type2) in type_rules:
                    relation_type = type_rules[(type1, type2)]
                elif (type2, type1) in type_rules:
                    relation_type = type_rules[(type2, type1)]
                    source_entity = entity2
                    target_entity = entity1
                
                if relation_type:
                    # Calcular confianza basada en distancia
                    base_confidence = 0.75
                    distance_factor = max(0.5, 1.0 - (distance / 300.0))
                    final_confidence = min(0.9, base_confidence * distance_factor)
                    
                    relationship = {
                        'id': str(uuid.uuid4()),
                        'source': source_entity.get('canonical_text'),
                        'source_surface': source_entity.get('text'),
                        'target': target_entity.get('canonical_text'),
                        'target_surface': target_entity.get('text'),
                        'type': relation_type,
                        'confidence': final_confidence
                    }
                    relationships.append(relationship)
        
        return relationships
    
    def _extract_inter_chunk_relationships(self, entities: List[Dict], full_text: str) -> List[Dict]:
        """Extract relationships between entities across different chunks using medical logic"""
        relationships = []
        
        if len(entities) < 2:
            return relationships
            
        # Solo considerar entidades con alta confianza
        high_confidence_entities = [e for e in entities if e.get('confidence', 0) > 0.85]
        
        if len(high_confidence_entities) < 2:
            return relationships
            
        # Reglas médicas específicas con mayor distancia permitida
        type_rules = {
            ('Therapeutic_procedure', 'Disease_disorder'): 'TREATS',
            ('Disease_disorder', 'Sign_symptom'): 'MANIFESTS_AS', 
            ('Diagnostic_procedure', 'Disease_disorder'): 'DIAGNOSES',
            ('Lab_value', 'Disease_disorder'): 'INDICATES',
            ('Biological_structure', 'Disease_disorder'): 'AFFECTED_BY',
            ('Therapeutic_procedure', 'Sign_symptom'): 'ALLEVIATES',
            ('Diagnostic_procedure', 'Biological_structure'): 'EXAMINES',
            ('Lab_value', 'Therapeutic_procedure'): 'MONITORS',
            ('Disease_disorder', 'Therapeutic_procedure'): 'TREATED_BY',  # Bidireccional
            ('Sign_symptom', 'Disease_disorder'): 'SYMPTOM_OF',  # Bidireccional
        }
        
        # Patrones contextuales para validar relaciones a distancia
        contextual_patterns = {
            'TREATS': [r'treatment', r'therapy', r'therapeutic', r'cure', r'heal', r'remedy'],
            'CAUSES': [r'causes?', r'leads? to', r'results? in', r'triggers?'],
            'PREVENTS': [r'prevent', r'prophylaxis', r'protection', r'avoid'],
        }
        
        for i, entity1 in enumerate(high_confidence_entities):
            for j, entity2 in enumerate(high_confidence_entities[i+1:], i+1):
                # Evitar auto-relaciones
                if (entity1.get('canonical_text') == entity2.get('canonical_text') or
                    entity1.get('text') == entity2.get('text')):
                    continue
                    
                # Verificar validez de entidades
                if (not entity1.get('canonical_text') or 
                    not entity2.get('canonical_text') or
                    len(entity1.get('canonical_text', '')) < 3 or
                    len(entity2.get('canonical_text', '')) < 3):
                    continue
                
                # Calcular distancia
                distance = abs(entity1['start'] - entity2['start'])
                
                # Permitir distancias mayores para relaciones importantes
                max_distance = 800  # Aumentado significativamente
                
                if distance > max_distance:
                    continue
                
                # Obtener tipos de entidad
                type1 = entity1.get('label', '')
                type2 = entity2.get('label', '')
                
                # Buscar regla que coincida
                relation_type = None
                source_entity = entity1
                target_entity = entity2
                
                if (type1, type2) in type_rules:
                    relation_type = type_rules[(type1, type2)]
                elif (type2, type1) in type_rules:
                    relation_type = type_rules[(type2, type1)]
                    source_entity = entity2
                    target_entity = entity1
                
                if relation_type:
                    # Validar con contexto si las entidades están muy separadas
                    should_create_relation = True
                    
                    if distance > 300:  # Para distancias grandes, validar contexto
                        start_pos = min(entity1['start'], entity2['start'])
                        end_pos = max(entity1['end'], entity2['end'])
                        context = full_text[start_pos:end_pos].lower()
                        
                        # Buscar evidencia contextual
                        has_context = False
                        if relation_type in contextual_patterns:
                            for pattern in contextual_patterns[relation_type]:
                                if re.search(pattern, context):
                                    has_context = True
                                    break
                        else:
                            has_context = True  # Para otros tipos, aceptar por defecto
                            
                        should_create_relation = has_context
                    
                    if should_create_relation:
                        # Calcular confianza dinámica
                        base_confidence = 0.8
                        distance_penalty = min(0.3, distance / 2000.0)
                        final_confidence = max(0.5, base_confidence - distance_penalty)
                        
                        # Bonus por contexto médico
                        context_start = max(0, min(entity1['start'], entity2['start']) - 50)
                        context_end = min(len(full_text), max(entity1['end'], entity2['end']) + 50)
                        context_window = full_text[context_start:context_end].lower()
                        
                        medical_terms = ['treatment', 'therapy', 'disease', 'disorder', 'symptom', 'diagnosis', 'patient']
                        medical_context = sum(1 for term in medical_terms if term in context_window)
                        context_bonus = min(0.1, medical_context * 0.02)
                        
                        final_confidence = min(0.95, final_confidence + context_bonus)
                        
                        relationship = {
                            'id': str(uuid.uuid4()),
                            'source': source_entity.get('canonical_text'),
                            'source_surface': source_entity.get('text'),
                            'target': target_entity.get('canonical_text'),
                            'target_surface': target_entity.get('text'),
                            'type': relation_type,
                            'confidence': final_confidence,
                            'distance': distance  # Para debugging
                        }
                        relationships.append(relationship)
        
        logger.info(f"Created {len(relationships)} inter-chunk relationships")
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
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Remove duplicate relationships, keeping the one with highest confidence"""
        if not relationships:
            return relationships
        
        deduplicated = []
        seen_relationships = set()
        
        # Sort by confidence descending to keep best relationships first
        sorted_relationships = sorted(relationships, key=lambda x: x.get('confidence', 0), reverse=True)
        
        for relationship in sorted_relationships:
            source = relationship.get('source', '').strip()
            target = relationship.get('target', '').strip()
            rel_type = relationship.get('type', '').strip()
            
            if not source or not target or not rel_type:
                continue
            
            # Create relationship signature (bidirectional check)
            sig1 = (source, target, rel_type)
            sig2 = (target, source, rel_type)  # Check reverse too
            
            if sig1 not in seen_relationships and sig2 not in seen_relationships:
                seen_relationships.add(sig1)
                deduplicated.append(relationship)
        
        logger.info(f"Deduplicated relationships: {len(relationships)} -> {len(deduplicated)}")
        return deduplicated
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
