"""
Sistema de aprendizaje automático de patrones de fecha
Detecta texto similar a fechas y genera regex dinámicamente
"""
import re
import json
import os
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


LEARNED_PATTERNS_FILE = 'learned_date_patterns.json'

class DatePatternLearner:
    """
    Aprender patrones de fecha dinamicamente y los guarda
    """

    def __init__(self):
        self.learned_patterns = []
        self.pattern_usage = Counter()
        self.load_learned_patterns()

    def load_learned_patterns(self):
        """Carga patrones aprendidos desde un archivo JSON"""
        try: 
            if os.path.exists(LEARNED_PATTERNS_FILE):
                with open(LEARNED_PATTERNS_FILE, 'r', encoding='utf-8') as f:
                    data =json.load(f)
                    self.learned_patterns = data.get('patterns', [])
                    self.pattern_usage = Counter(data.get('usage',{}))
                    logger.info(f"Cargados {len(self.learned_patterns)} patrones aprendidos.")
            else:
                logger.info("No se encontraron patrones aprendidos previamente.")
        except Exception as e:
            logger.error(f"Error al cargar patrones aprendidos: {e}")
            self.learned_patterns = []

    def save_learned_patterns(self):
        """Guarda los patrones aprendidos en un archivo JSON"""
        try: 
            data = {
                'patterns': self.learned_patterns,
                'usage': dict(self.pattern_usage),
                'last_updated': datetime.now().isoformat()
            }
            with open(LEARNED_PATTERNS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data,f,indent=2, ensure_ascii=False)
            logger.info(f"Guardados {len(self.learned_patterns)} patrones")
        except Exception as e: 
            logger.error(f"Error al guardar patrones: {e}")

    def detect_potential_date_strings(self, text: str) -> List[Tuple[str, int]]:
        """
        Detecta cadenas que PARECEN fechas pero no matchean con regex existentes
        
        Returns:
            List[Tuple[str, position]]: Lista de (texto_candidato, posición)
        """
        candidates = []
        
        # Patrones heurísticos para detectar posibles fechas
        heuristic_patterns = [
            # Números con letras en medio (probable mes)
            r'\b(\d{1,2}[A-Z]{3,4}\d{2,4})\b',
            
            # Letras seguidas de números (mes + año)
            r'\b([A-Z]{3,9}\s*[\-\/\.\s]?\s*\d{2,4})\b',
            
            # Números con separadores inusuales
            r'\b(\d{1,2}\s*[\~\`\^\*\+]\s*\d{1,2}\s*[\~\`\^\*\+]\s*\d{2,4})\b',
            
            # Palabras clave de fecha seguidas de algo
            r'(?:EXP|VENC|CAD|FECHA|DATE|MFG|BBE|BEST|USE)\s*[:\s]*([A-Z0-9\s\-\/\.]{5,20})',
            
            # Secuencias de números con separadores no estándar
            r'\b(\d{1,2}\s*[^\w\s]\s*\d{1,2}\s*[^\w\s]\s*\d{2,4})\b',
            
            # Formato compacto con letras
            r'\b(\d{1,2}[A-Z]{2,3}\d{1,4})\b',
        ]
        
        for pattern in heuristic_patterns:
            regex = re.compile(pattern, flags=re.IGNORECASE)
            matches = regex.finditer(text)
            
            for match in matches:
                candidate = match.group(1) if match.lastindex else match.group(0)
                candidates.append((candidate.strip(), match.start()))
        
        # Eliminar duplicados
        candidates = list(set(candidates))
        
        logger.debug(f"Detectados {len(candidates)} candidatos potenciales: {candidates}")
        return candidates
    
    def analyze_date_structure(self, date_str: str) -> Optional[dict]:
        """
        Analiza la estructura de una cadena similar a fecha
        
        Returns:
            dict con estructura detectada o None
        """
        date_str = date_str.strip()
        
        # Análisis de componentes
        has_digits = bool(re.search(r'\d', date_str))
        has_letters = bool(re.search(r'[A-Z]', date_str, re.IGNORECASE))
        
        if not has_digits:
            return None
        
        # Detectar separadores
        separators = re.findall(r'[^\w]', date_str)
        separator_set = set(separators) if separators else set()
        
        # Detectar componentes
        digit_groups = re.findall(r'\d+', date_str)
        letter_groups = re.findall(r'[A-Z]+', date_str, re.IGNORECASE)
        
        structure = {
            'original': date_str,
            'has_digits': has_digits,
            'has_letters': has_letters,
            'digit_groups': digit_groups,
            'letter_groups': letter_groups,
            'separators': list(separator_set),
            'length': len(date_str),
            'digit_count': len(digit_groups),
            'letter_count': len(letter_groups)
        }
        
        logger.debug(f"Estructura analizada: {structure}")
        return structure
    
    def generate_regex_from_structure(self, structure: dict) -> Optional[str]:
        """
        Genera un patrón regex basado en la estructura analizada
        
        Returns:
            str: Patrón regex o None
        """
        try:
            original = structure['original']
            digit_groups = structure['digit_groups']
            letter_groups = structure['letter_groups']
            separators = structure['separators']
            
            # Construir regex dinámicamente
            pattern_parts = []
            
            # Escapar el string original pero mantener estructura
            escaped = re.escape(original)
            
            # Reemplazar componentes por patrones genéricos
            # Números por \d+
            for digit_group in digit_groups:
                length = len(digit_group)
                if length <= 2:
                    escaped = escaped.replace(re.escape(digit_group), r'(\d{1,2})', 1)
                elif length == 4:
                    escaped = escaped.replace(re.escape(digit_group), r'(\d{4})', 1)
                else:
                    escaped = escaped.replace(re.escape(digit_group), r'(\d{2,4})', 1)
            
            # Letras por patrones de mes
            month_pattern = r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)'
            for letter_group in letter_groups:
                if len(letter_group) in [3, 4]:  # Probable mes abreviado
                    escaped = escaped.replace(
                        re.escape(letter_group.upper()), 
                        month_pattern, 
                        1
                    )
            
            # Hacer separadores opcionales y flexibles
            for sep in separators:
                if sep in ['-', '/', '.', ' ']:
                    escaped = escaped.replace(
                        re.escape(sep), 
                        r'\s*[\/\-\.\s]\s*'
                    )
            
            # Agregar límites de palabra
            pattern = r'\b' + escaped + r'\b'
            
            logger.info(f"Patrón generado: {pattern}")
            return pattern
            
        except Exception as e:
            logger.error(f"Error al generar regex: {e}")
            return None
    
    def learn_from_candidate(self, candidate: str) -> bool:
        """
        Aprende un nuevo patrón desde un candidato
        
        Returns:
            bool: True si se aprendió un patrón nuevo
        """
        # Analizar estructura
        structure = self.analyze_date_structure(candidate)
        if not structure:
            return False
        
        # Generar regex
        new_pattern = self.generate_regex_from_structure(structure)
        if not new_pattern:
            return False
        
        # Validar que el patrón no sea demasiado genérico
        if not self._validate_pattern(new_pattern):
            logger.warning(f"Patrón rechazado (demasiado genérico): {new_pattern}")
            return False
        
        # Verificar si ya existe
        if new_pattern in self.learned_patterns:
            logger.debug(f"Patrón ya existe: {new_pattern}")
            self.pattern_usage[new_pattern] += 1
            return False
        
        # Agregar patrón nuevo
        self.learned_patterns.append(new_pattern)
        self.pattern_usage[new_pattern] = 1
        logger.info(f" NUEVO PATRÓN APRENDIDO: {new_pattern}")
        logger.info(f" Desde candidato: {candidate}")
        
        # Guardar
        self.save_learned_patterns()
        return True
    
    def _validate_pattern(self, pattern: str) -> bool:
        """
        Valida que el patrón no sea demasiado genérico o inválido
        """
        # Rechazar patrones muy cortos
        if len(pattern) < 10: return False
        
        # Debe contener al menos un grupo de captura
        if '(' not in pattern: return False
        
        # Debe contener números
        if r'\d' not in pattern: return False
        
        # Intentar compilar
        try:
            re.compile(pattern, re.IGNORECASE)
            return True
        except re.error:
            return False
    
    def get_all_patterns(self) -> List[str]:
        """Retorna todos los patrones (base + aprendidos)"""
        return self.learned_patterns.copy()
    
    def get_top_patterns(self, n: int = 10) -> List[Tuple[str, int]]:
        """Retorna los N patrones más usados"""
        return self.pattern_usage.most_common(n)
    
    def prune_unused_patterns(self, min_usage: int = 3):
        """Elimina patrones que se usan muy poco"""
        before = len(self.learned_patterns)
        
        self.learned_patterns = [
            p for p in self.learned_patterns 
            if self.pattern_usage.get(p, 0) >= min_usage
        ]
        
        removed = before - len(self.learned_patterns)
        if removed > 0:
            logger.info(f"Eliminados {removed} patrones poco usados")
            self.save_learned_patterns()

pattern_learner = DatePatternLearner()
