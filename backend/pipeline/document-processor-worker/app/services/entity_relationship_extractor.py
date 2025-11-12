import logging
import re
from itertools import combinations
from typing import Dict, Iterable, List, Tuple, Optional
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
import uuid
import unicodedata

logger = logging.getLogger(__name__)

class EntityRelationshipExtractor:
    """
    Medical Entity and Relationship Extractor using specialized biomedical NER models.
    Uses pre-trained transformer models specifically designed for biomedical text.
    """
    
    _instance = None
    
    # Configuración de filtros inteligentes
    MEDICAL_STOP_WORDS = {
        'generic_descriptors': ['mechanical', 'fluorescent', 'chemical', 'physical', 'biological', 'technical', 
                               'clinical', 'experimental', 'statistical', 'numerical', 'analytical', 'synthetic',
                               'automatic', 'electronic', 'digital', 'manual', 'optical', 'magnetic'],
        'vague_terms': ['factors', 'effects', 'methods', 'approaches', 'techniques', 'procedures', 'processes',
                       'conditions', 'systems', 'mechanisms', 'pathways', 'networks', 'materials', 'components',
                       'elements', 'structures', 'patterns', 'models', 'features', 'properties'],
        'low_value': ['increased', 'decreased', 'reduced', 'elevated', 'improved', 'enhanced', 'modified',
                     'altered', 'affected', 'involved', 'associated', 'related', 'observed', 'detected',
                     'measured', 'assessed', 'evaluated', 'analyzed', 'examined', 'studied'],
        'problematic_single_words': ['all cells', 'cells', 'cell', 'tissue', 'sample', 'control', 'group',
                                   'study', 'analysis', 'data', 'result', 'findings', 'conclusion']
    }
    GENERIC_MEDICAL_CONTEXTS = [
        'therapy', 'treatment', 'surgery', 'procedure', 'intervention',
        'device', 'implant', 'prosthetic', 'cardiac', 'ventricular', 'vascular'
    ]
    VAGUE_TERM_ANCHORS = [
        'cardiac', 'cardiovascular', 'heart', 'ventricular', 'arterial',
        'pulmonary', 'myocardial', 'therapeutic', 'diagnostic'
    ]
    QUANTITATIVE_CONTEXT_PATTERN = re.compile(
        r'\b\d+(\.\d+)?\s*(mg|ml|mmol|percent|%|fold|times|days|weeks|months)\b'
    )
    RELATION_PATTERNS = {
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
    TYPE_RELATION_RULES = {
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
    GENERIC_RELATION_TERMS = {
        'mechanical', 'fluorescent', 'increased', 'decreased', 'factors', 'effects'
    }
    SPECIFIC_MEDICAL_TERMS = {
        'heart failure', 'cardiovascular diseases', 'cardiac', 'ventricular',
        'myocardial', 'arterial', 'pulmonary', 'therapeutic', 'diagnostic'
    }
    INTER_CHUNK_TYPE_RULES = {
        ('Therapeutic_procedure', 'Disease_disorder'): 'TREATS',
        ('Disease_disorder', 'Sign_symptom'): 'MANIFESTS_AS',
        ('Diagnostic_procedure', 'Disease_disorder'): 'DIAGNOSES',
        ('Lab_value', 'Disease_disorder'): 'INDICATES',
        ('Biological_structure', 'Disease_disorder'): 'AFFECTED_BY',
        ('Therapeutic_procedure', 'Sign_symptom'): 'ALLEVIATES',
        ('Diagnostic_procedure', 'Biological_structure'): 'EXAMINES',
        ('Lab_value', 'Therapeutic_procedure'): 'MONITORS',
        ('Disease_disorder', 'Therapeutic_procedure'): 'TREATED_BY',
        ('Sign_symptom', 'Disease_disorder'): 'SYMPTOM_OF',
    }
    INTER_CHUNK_CONTEXT_PATTERNS = {
        'TREATS': [r'treatment', r'therapy', r'therapeutic', r'cure', r'heal', r'remedy'],
        'CAUSES': [r'causes?', r'leads? to', r'results? in', r'triggers?'],
        'PREVENTS': [r'prevent', r'prophylaxis', r'protection', r'avoid'],
    }
    INTER_CHUNK_MAX_DISTANCE = 1200
    MEDICAL_CONTEXT_TERMS = [
        'treatment', 'therapy', 'disease', 'disorder', 'symptom', 'diagnosis', 'patient'
    ]
    
    # Thresholds dinámicos por tipo de entidad
    CONFIDENCE_THRESHOLDS = {
        'Disease_disorder': 0.92,        # Más restrictivo para enfermedades
        'Therapeutic_procedure': 0.90,   # Alto para tratamientos
        'Diagnostic_procedure': 0.88,    # Estándar para diagnósticos
        'Lab_value': 0.85,              # Menos restrictivo para valores
        'Sign_symptom': 0.90,           # Alto para síntomas
        'Biological_structure': 0.88,   # Estándar para estructuras
        'Detailed_description': 0.82,   # Más permisivo para descripciones
        'Coreference': 0.85             # Estándar para correferencias
    }
    
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
    
    def _is_entity_contextually_valid(self, entity_text: str, entity_type: str, context: str) -> bool:
        """Validación contextual inteligente de entidades"""
        entity_lower = entity_text.lower().strip()
        context_lower = context.lower()

        categories = [
            category for category, words in self.MEDICAL_STOP_WORDS.items()
            if entity_lower in words
        ]

        for category in categories:
            if not self._passes_category_validation(category, entity_lower, context_lower):
                return False

        return True

    def _passes_category_validation(self, category: str, entity_lower: str, context_lower: str) -> bool:
        """Run the category-specific validation rule if one is defined."""
        validators = {
            'generic_descriptors': self._has_required_medical_context,
            'vague_terms': self._is_supported_by_specific_context,
            'low_value': self._is_near_quantitative_data,
        }
        validator = validators.get(category)
        if not validator:
            return True
        return validator(entity_lower, context_lower)

    def _has_required_medical_context(self, _: str, context_lower: str) -> bool:
        """Generic descriptors need a clear medical procedure context."""
        return any(ctx in context_lower for ctx in self.GENERIC_MEDICAL_CONTEXTS)

    def _is_supported_by_specific_context(self, entity_lower: str, context_lower: str) -> bool:
        """Vague terms must appear near specific medical anchors."""
        position = context_lower.find(entity_lower)
        if position == -1:
            return True

        span_start = max(0, position - 50)
        span_end = position + len(entity_lower) + 50
        local_context = context_lower[span_start:span_end]
        return any(term in local_context for term in self.VAGUE_TERM_ANCHORS)

    def _is_near_quantitative_data(self, _: str, context_lower: str) -> bool:
        """Low value terms need quantitative measurements nearby."""
        return bool(self.QUANTITATIVE_CONTEXT_PATTERN.search(context_lower))

    def _get_dynamic_threshold(self, entity_type: str) -> float:
        """Obtener threshold dinámico basado en tipo de entidad"""
        return self.CONFIDENCE_THRESHOLDS.get(entity_type, 0.88)
    
    def _is_corrupted_entity(self, entity_text: str) -> bool:
        """Detecta entidades corruptas o con patrones extraños"""
        text = entity_text.lower().strip()
        
        # Patrones de corrupción comunes
        corruption_patterns = [
            r'o\s+o+\s*o+',  # "o o o o o" patterns
            r'^[a-z]\s+[a-z]\s+[a-z]',  # Letras sueltas repetidas como "a b c"
            r'(\w)\1{4,}',  # Caracteres repetidos >4 veces como "aaaaa"
            r'^[^a-zA-Z]*$',  # Solo símbolos/números
            r'\s{3,}',  # Espacios excesivos
            r'^[oO0]+\s+[oO0]+',  # Patrones de O's y 0's
        ]
        
        import re
        for pattern in corruption_patterns:
            if re.search(pattern, text):
                return True
                
        # Verificar ratio de espacios vs caracteres
        if len(text) > 5:
            space_ratio = text.count(' ') / len(text)
            if space_ratio > 0.6:  # Más de 60% espacios
                return True
        
        # Verificar si tiene demasiadas palabras de 1 letra
        words = text.split()
        if len(words) > 3:
            single_char_words = sum(1 for word in words if len(word) == 1)
            if single_char_words / len(words) > 0.5:  # Más de 50% palabras de 1 letra
                return True
                
        return False

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
                    raw_text = entity['word'].strip()
                    entity_type = entity['entity_group']
                    
                    # Obtener threshold dinámico basado en tipo de entidad
                    dynamic_threshold = self._get_dynamic_threshold(entity_type)
                    
                    # Filtros básicos con confianza dinámica
                    if (entity['score'] > dynamic_threshold and  # Confianza dinámica por tipo
                        len(raw_text) >= 6 and  # Mínimo 6 caracteres
                        not raw_text.isdigit() and  # No solo números
                        not raw_text.startswith('##') and  # Filtrar tokens fragmentados de BERT
                        not raw_text.endswith((' ', '-', '_', '+', '##')) and  # No terminar con caracteres problemáticos
                        not raw_text.startswith((' ', '-', '_', '+')) and  # No empezar con caracteres problemáticos
                        not re.match(r'^[a-zA-Z]{1,4}$', raw_text) and  # No palabras muy cortas sueltas
                        not re.match(r'^[\d\s\-–%+]+$', raw_text) and  # No solo números y símbolos
                        not re.match(r'^[^\w\s]+$', raw_text) and  # No solo caracteres especiales
                        len(raw_text.replace(' ', '').replace('-', '').replace('+', '')) > 3 and  # Contenido real mínimo
                        not self._is_corrupted_entity(raw_text)):  # Filtrar entidades corruptas
                        
                        canonical = self._canonicalize(raw_text)
                        
                        # Validación contextual inteligente
                        if (canonical and len(canonical) >= 4 and
                            not self._is_corrupted_entity(canonical) and
                            self._is_entity_contextually_valid(raw_text, entity_type, chunk)):
                            entity_data = {
                                'id': str(uuid.uuid4()),
                                'text': raw_text,
                                'canonical_text': canonical,
                                'label': entity_type,
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

        for entity1, entity2, between_text in self._generate_relationship_candidates(entities, text):
            relation_type = self._match_relation_type(between_text)
            if relation_type:
                relationships.append(self._build_relationship(entity1, entity2, relation_type))

        return relationships

    def _filter_high_confidence(self, entities: List[Dict], threshold: float = 0.85) -> List[Dict]:
        """Return only entities whose confidence exceeds the desired threshold."""
        return [entity for entity in entities if entity.get('confidence', 0) > threshold]

    def _generate_relationship_candidates(
        self, entities: List[Dict], text: str
    ) -> List[Tuple[Dict, Dict, str]]:
        """Collect high-confidence entity pairs that have meaningful context between them."""
        if len(entities) < 2:
            return []

        high_confidence = self._filter_high_confidence(entities)
        if len(high_confidence) < 2:
            return []

        candidates = []
        for entity1, entity2 in combinations(high_confidence, 2):
            if self._should_skip_pair(entity1, entity2):
                continue

            between_text = self._extract_between_text(entity1, entity2, text)
            if not between_text:
                continue

            candidates.append((entity1, entity2, between_text))

        return candidates

    def _should_skip_pair(self, entity1: Dict, entity2: Dict, max_distance: int = 150) -> bool:
        """Apply all quick rejection rules for a pair of entities."""
        if (
            entity1.get('canonical_text') == entity2.get('canonical_text')
            or entity1.get('text') == entity2.get('text')
        ):
            return True

        distance = abs(entity1['start'] - entity2['start'])
        if distance > max_distance:
            return True

        return not (self._has_valid_canonical(entity1) and self._has_valid_canonical(entity2))

    def _has_valid_canonical(self, entity: Dict) -> bool:
        """Check canonical text is present, long enough, and not corrupted."""
        canonical = entity.get('canonical_text')
        if not canonical or len(canonical) < 3:
            return False
        return not self._is_corrupted_entity(canonical)

    def _extract_between_text(self, entity1: Dict, entity2: Dict, text: str) -> str:
        """Return normalized text between two entities or empty string if insignificant."""
        start_pos = min(entity1['end'], entity2['end'])
        end_pos = max(entity1['start'], entity2['start'])
        between_text = text[start_pos:end_pos].lower()
        return between_text if between_text.strip() and len(between_text.strip()) >= 2 else ""

    def _match_relation_type(self, between_text: str) -> Optional[str]:
        """Return the first relation type whose pattern matches the text between entities."""
        for relation_type, patterns in self.RELATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, between_text):
                    return relation_type
        return None

    def _build_relationship(
        self,
        source: Dict,
        target: Dict,
        relation_type: str,
        confidence: float = 0.8,
        extras: Optional[Dict] = None,
    ) -> Dict:
        """Create the relationship payload with consistent fields."""
        relationship = {
            'id': str(uuid.uuid4()),
            'source': source.get('canonical_text'),
            'source_surface': source.get('text'),
            'target': target.get('canonical_text'),
            'target_surface': target.get('text'),
            'type': relation_type,
            'confidence': confidence,
        }
        if extras:
            relationship.update(extras)
        return relationship
    
    def _extract_type_based_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Extract relationships based on entity types using medical logic"""
        relationships = []
        
        high_confidence_entities = self._filter_high_confidence(entities)
        if len(high_confidence_entities) < 2:
            return relationships
        
        for entity1, entity2 in combinations(high_confidence_entities, 2):
            if self._should_skip_pair(entity1, entity2, max_distance=300):
                continue

            relation = self._determine_type_relation(entity1, entity2)
            if not relation:
                continue

            relation_type, source_entity, target_entity = relation
            distance = abs(source_entity['start'] - target_entity['start'])
            final_confidence = self._compute_type_relation_confidence(
                source_entity, target_entity, distance
            )

            if final_confidence is None or final_confidence < 0.65:
                continue

            relationships.append(
                self._build_relationship(
                    source_entity, target_entity, relation_type, final_confidence
                )
            )
        
        return relationships

    def _determine_type_relation(
        self, entity1: Dict, entity2: Dict
    ) -> Optional[Tuple[str, Dict, Dict]]:
        """Resolve the relation type and entity direction using predefined rules."""
        type1 = entity1.get('label', '')
        type2 = entity2.get('label', '')

        if (type1, type2) in self.TYPE_RELATION_RULES:
            return self.TYPE_RELATION_RULES[(type1, type2)], entity1, entity2
        if (type2, type1) in self.TYPE_RELATION_RULES:
            return self.TYPE_RELATION_RULES[(type2, type1)], entity2, entity1
        return None

    def _compute_type_relation_confidence(
        self, source_entity: Dict, target_entity: Dict, distance: int
    ) -> Optional[float]:
        """Compute contextual confidence for type-based relationships."""
        source_text = source_entity.get('text', '').lower()
        target_text = target_entity.get('text', '').lower()

        if (
            source_text in self.GENERIC_RELATION_TERMS
            and target_text in self.GENERIC_RELATION_TERMS
        ):
            return None

        base_confidence = 0.75
        distance_factor = max(0.5, 1.0 - (distance / 300.0))

        generic_penalty = (
            0.8
            if source_text in self.GENERIC_RELATION_TERMS
            or target_text in self.GENERIC_RELATION_TERMS
            else 1.0
        )

        medical_boost = 1.0
        if (
            any(term in source_text for term in self.SPECIFIC_MEDICAL_TERMS)
            or any(term in target_text for term in self.SPECIFIC_MEDICAL_TERMS)
        ):
            medical_boost = 1.2

        final_confidence = min(
            0.9, base_confidence * distance_factor * generic_penalty * medical_boost
        )
        return final_confidence
    
    def _extract_inter_chunk_relationships(self, entities: List[Dict], full_text: str) -> List[Dict]:
        """Extract relationships between entities across different chunks using medical logic"""
        relationships = []
        
        if len(entities) < 2:
            return relationships
            
        # Solo considerar entidades con alta confianza
        high_confidence_entities = self._filter_high_confidence(entities)
        if len(high_confidence_entities) < 2:
            return relationships

        for entity1, entity2 in combinations(high_confidence_entities, 2):
            relation = self._determine_inter_chunk_relation(entity1, entity2)
            if not relation:
                continue

            relation_type, source_entity, target_entity, distance = relation

            if distance > 300 and not self._has_supporting_context(
                relation_type, source_entity, target_entity, full_text
            ):
                continue

            confidence = self._compute_inter_chunk_confidence(
                source_entity, target_entity, distance, full_text
            )

            relationships.append(
                self._build_relationship(
                    source_entity,
                    target_entity,
                    relation_type,
                    confidence,
                    extras={'distance': distance},
                )
            )

        logger.info(f"Created {len(relationships)} inter-chunk relationships")
        return relationships

    def _determine_inter_chunk_relation(
        self, entity1: Dict, entity2: Dict
    ) -> Optional[Tuple[str, Dict, Dict, int]]:
        """Identify cross-chunk relation type and direction, enforcing distance limits."""
        if self._should_skip_pair(
            entity1, entity2, max_distance=self.INTER_CHUNK_MAX_DISTANCE
        ):
            return None

        type1 = entity1.get('label', '')
        type2 = entity2.get('label', '')

        if (type1, type2) in self.INTER_CHUNK_TYPE_RULES:
            relation_type = self.INTER_CHUNK_TYPE_RULES[(type1, type2)]
            source_entity, target_entity = entity1, entity2
        elif (type2, type1) in self.INTER_CHUNK_TYPE_RULES:
            relation_type = self.INTER_CHUNK_TYPE_RULES[(type2, type1)]
            source_entity, target_entity = entity2, entity1
        else:
            return None

        distance = abs(source_entity['start'] - target_entity['start'])
        return relation_type, source_entity, target_entity, distance

    def _has_supporting_context(
        self,
        relation_type: str,
        source_entity: Dict,
        target_entity: Dict,
        full_text: str,
    ) -> bool:
        """Check for context words supporting long-distance relations."""
        start_pos = min(source_entity['start'], target_entity['start'])
        end_pos = max(source_entity['end'], target_entity['end'])
        context = full_text[start_pos:end_pos].lower()

        patterns = self.INTER_CHUNK_CONTEXT_PATTERNS.get(relation_type)
        if not patterns:
            return True

        return any(re.search(pattern, context) for pattern in patterns)

    def _compute_inter_chunk_confidence(
        self,
        source_entity: Dict,
        target_entity: Dict,
        distance: int,
        full_text: str,
    ) -> float:
        """Estimate confidence for inter-chunk relations based on distance and context."""
        base_confidence = 0.8
        distance_penalty = min(0.3, distance / 2000.0)
        confidence = max(0.5, base_confidence - distance_penalty)

        context_start = max(0, min(source_entity['start'], target_entity['start']) - 50)
        context_end = min(
            len(full_text), max(source_entity['end'], target_entity['end']) + 50
        )
        context_window = full_text[context_start:context_end].lower()

        medical_context = sum(
            1 for term in self.MEDICAL_CONTEXT_TERMS if term in context_window
        )
        context_bonus = min(0.1, medical_context * 0.02)

        return min(0.95, confidence + context_bonus)
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar entities, keeping the one with highest confidence"""
        if not entities:
            return entities
        
        deduplicated: List[Dict] = []
        seen: Dict[str, bool] = {}

        for entity in self._sort_entities_by_confidence(entities):
            canonical = self._get_canonical_text(entity)
            if not canonical or canonical in seen:
                continue

            if self._is_similar_to_seen(canonical, seen.keys()):
                continue

            seen[canonical] = True
            deduplicated.append(entity)
        
        logger.info(f"Deduplicated entities: {len(entities)} -> {len(deduplicated)}")
        return deduplicated

    def _sort_entities_by_confidence(self, entities: List[Dict]) -> List[Dict]:
        """Sort entities so that higher confidence appears first."""
        return sorted(entities, key=lambda x: x.get('confidence', 0), reverse=True)

    def _get_canonical_text(self, entity: Dict) -> str:
        """Fetch canonical text stripped of whitespace."""
        return entity.get('canonical_text', '').strip()

    def _is_similar_to_seen(self, canonical: str, seen_canonicals: Iterable[str]) -> bool:
        """Return True if canonical is too similar to any already-seen value."""
        for seen_canon in seen_canonicals:
            if self._are_canonicals_similar(canonical, seen_canon):
                return True
        return False

    def _are_canonicals_similar(self, candidate: str, existing: str) -> bool:
        return (
            (candidate in existing and len(candidate) < len(existing) * 0.8)
            or (existing in candidate and len(existing) < len(candidate) * 0.8)
        )
    
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
