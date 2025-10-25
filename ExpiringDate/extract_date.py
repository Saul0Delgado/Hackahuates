"""
Módulo de extracción de fechas desde imágenes
Mejor detección de fechas y manejo de errores
Aprendizaje automático de patrones

"""
import pytesseract
from pytesseract import Output
from PIL import Image, ImageEnhance
import numpy as np
import datetime
import re
from dateparser import parse
import logging
from collections import Counter
from typing import Optional, Tuple, List

from utils import (
    rescale_image,
    threshold,
    find_bbox,
    four_point_transform,
    remove_noise_and_smooth
)
from collections import Counter
from pattern_learner import pattern_learner

logger = logging.getLogger(__name__)

# Patrones de fecha más robustos
BASE_DATE_PATTERNS = [
    # --- PRIORIDAD 1: Fechas Completas (3 GRUPOS) ---
    
    # DD/MM/YYYY (Numérico)
    r'\b(\d{1,2})\s*[\/\-\.–—]\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})\b',
    
    # YYYY/MM/DD (ISO)
    r'\b(\d{4})\s*[\/\-\.–—]\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{1,2})\b',
    
    # DDMMMYY (Ej: 15JAN24)
    r'\b(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)(\d{2})\b',
    r'\b(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)(\d{4})\b',

    # DD-MMM-YY (ej: 15-JAN-24)
    r'\b(\d{1,2})\s*[\/\-\.]\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[A-Z]*\.?\s*[\/\-\.]\s*(\d{2,4})\b',
    
    # Día Mes Año (15 Jan 2024)
    r'\b(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|AUG|SEPT?|OCT|NOV|DEC)[A-Z]*\.?\s+(\d{4})\b',
    r'\b(\d{1,2})\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})\b',

    # Mes Día, Año (Jan 15, 2024)
    r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|AUG|SEPT?|OCT|NOV|DEC)[A-Z]*\.?\s+(\d{1,2})[,\s]+(\d{4})\b',
    r'\b(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{1,2})[,\s]+(\d{4})\b',

    # Con prefijos (VENC, EXP) + Fecha Completa
    r'(?:EXP|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRY|EXPIRES?|BBE|BB)\s*[:\s]*\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})',
    r'(?:EXP|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRY|EXPIRES?)\s*[:\s]*\s*(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)(\d{2,4})',
    r'(?:EXP(?:IRY)?(?:\s*DATE)?|VENC(?:IMIENTO)?|CAD(?:UCIDAD)?|USE\s*BY|BEST\s*BEFORE|EXPIRES?|BBE|BB|MFG)\s*[:\s]*(\d{1,2})[\/\-\.]\s*(\d{1,2})[\/\-\.]\s*(\d{2,4})',
    r'(?:EXP(?:IRY)?|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRES?)\s*[:\s]*(\d{1,2})\s*[\/\-\.]?\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[A-Z]*\s*[\/\-\.]?\s*(\d{2,4})',
    r'(?:EXP(?:IRY)?|VENC|CAD|EXPIRES?)\s*[:\s]*(\d{1,2})[\/\-\.]\s*(\d{2,4})',


    # --- PRIORIDAD 2: Fechas Parciales (2 GRUPOS) ---
    # (Estas van DESPUÉS de las completas)

    # MM/YYYY (Numérico)
    r'\b(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})\b',
    
    # MMM-YYYY (Texto)
    r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[A-Z]*\.?\s*[\/\-\.–—]?\s*(\d{4})\b',

    # Con prefijos (VENC, EXP) + Fecha Parcial
    r'(?:EXP|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRY|EXPIRES?)\s*[:\s]*\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})',


    # --- PRIORIDAD 3: Formatos Ambiguos (1 GRUPO) ---
    # (Estos van al final)
    
    # YYYYMMDD o DDMMYYYY (8 dígitos)
    r'\b(\d{8})\b',
]

OCR_CONFIGS = [
    '--psm 6 -l spa+eng',      # Bloque uniforme de texto (mejor para etiquetas)
    '--psm 11 -l spa+eng',     # Texto disperso (mejor para fechas pequeñas)
    '--psm 6 -l eng',          # Solo inglés
    '--psm 3 -l spa+eng',      # Detección automática de texto
    '--psm 4 -l spa+eng',      # Columna única de texto
    '--psm 7 -l eng',          # Línea única de texto
]

def get_all_patterns():
    """
    Retorna todos los patrones: base + aprendidos
    """
    base = BASE_DATE_PATTERNS.copy()
    learned = pattern_learner.get_all_patterns()
    
    # Patrones aprendidos tienen prioridad (van primero)
    return learned + base

def find_date(text: str, enable_learning: bool = True) -> Optional[datetime.datetime]:
    """
    Busca fechas con sistema de scoring y validación mejorados
    """
    if not text or not text.strip():
        return None
    
    logger.debug(f"Buscando fechas en texto: {text[:150]}...")
    
    all_patterns = get_all_patterns()
    candidates = []  # Lista de (fecha, score, texto_original, posición)
    
    for i, pattern in enumerate(all_patterns):
        try:
            regex = re.compile(pattern, flags=re.IGNORECASE)
            matches = list(re.finditer(regex, text))
            
            for match in matches:
                date_str = match.group(0)
                
                # Parsear fecha
                parsed_date = parse_date_robust(date_str)
                
                if not parsed_date:
                    continue
                
                # Validar fecha
                is_valid, validation_score = validate_date_for_products(parsed_date)
                
                if not is_valid:
                    logger.debug(f"Fecha rechazada (fuera de rango): {parsed_date}")
                    continue
                
                # Calcular score total
                # Factores:
                # 1. Prioridad del patrón (patrones tempranos = mayor prioridad)
                # 2. Score de validación
                # 3. Posición en el texto (fechas al inicio son más importantes)
                
                pattern_score = 1.0 - (i / len(all_patterns)) * 0.5  # 0.5 a 1.0
                position_score = 1.0 - (match.start() / len(text)) * 0.3  # 0.7 a 1.0
                
                total_score = (validation_score * 0.5 + 
                              pattern_score * 0.3 + 
                              position_score * 0.2)
                
                candidates.append({
                    'date': parsed_date,
                    'score': total_score,
                    'text': date_str,
                    'position': match.start(),
                    'pattern_index': i
                })
                
                logger.debug(f"Candidato: {parsed_date.date()} | Score: {total_score:.3f} | Texto: '{date_str}'")
                
                # Marcar uso del patrón
                if pattern in pattern_learner.learned_patterns:
                    pattern_learner.pattern_usage[pattern] += 1
        
        except re.error as e:
            logger.warning(f"Error en patrón {i}: {e}")
            continue
    
    # Si no hay candidatos, intentar aprendizaje
    if not candidates and enable_learning:
        logger.info("Sin candidatos. Intentando aprender patrones...")
        potential_dates = pattern_learner.detect_potential_date_strings(text)
        
        for candidate_text, pos in potential_dates:
            if pattern_learner.learn_from_candidate(candidate_text):
                logger.info(f"Patrón aprendido desde: '{candidate_text}'")
                # Reintentar búsqueda
                return find_date(text, enable_learning=False)
    
    if not candidates:
        return None
    
    # Ordenar por score (mayor a menor)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    best = candidates[0]
    logger.info(f"Mejor fecha: {best['date'].date()} | Score: {best['score']:.3f} | Texto: '{best['text']}'")
    
    return best['date']

def enhance_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Mejora la imagen antes del OCR
    - Incrementa contraste y nitidez
    - Útil para imágenes con poca iluminación
    """
    try:
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Aumentar nitidez
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        # Ajustar brillo ligeramente
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        return img
    except Exception as e:
        logger.warning(f"No se pudo mejorar la imagen: {e}")
        return img

def normalize_ocr_text(text: str) -> str:
    """
    Normalización agresiva del texto OCR
    """
    if not text:
        return text
    
    # Eliminar múltiples espacios
    text = re.sub(r'\s+', ' ', text)
    
    # Corregir confusiones comunes de OCR en contexto numérico
    text = re.sub(r'(?<=\d)[OoQD](?=\d)', '0', text)  # O, o, Q, D -> 0
    text = re.sub(r'(?<=\d)[Il|](?=\d)', '1', text)    # I, l, | -> 1
    text = re.sub(r'[OoQD](?=\d)', '0', text)
    text = re.sub(r'(?<=\d)[OoQD]', '0', text)
    text = re.sub(r'[Il](?=\d)', '1', text)
    text = re.sub(r'(?<=\d)[Il]', '1', text)
    
    # Corregir confusiones con letras en meses
    text = re.sub(r'\bOCl\b', 'OCT', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAGO5T\b', 'AGOST', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSEPl\b', 'SEP', text, flags=re.IGNORECASE)
    
    # Eliminar caracteres extraños alrededor de números
    text = re.sub(r'([^\w\s])(\d)', r' \2', text)
    text = re.sub(r'(\d)([^\w\s])', r'\1 ', text)
    
    return text.strip()

def parse_date_robust(date_str: str) -> Optional[datetime.datetime]:
    """
    Parser de fechas robusto con múltiples estrategias
    """
    if not date_str:
        return None
    
    # Estrategia 1: dateparser (configurado para fechas de productos)
    try:
        parsed = parse(
            date_str,
            languages=['es', 'en'],
            settings={
                'PREFER_DAY_OF_MONTH': 'first',
                'PREFER_DATES_FROM': 'future',
                'STRICT_PARSING': False,
                'DATE_ORDER': 'DMY',
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        if parsed:
            return parsed
    except:
        pass
    
    # Estrategia 2: Parseo manual para formatos compactos
    # Caso: DDMMMYY (15ENE24)
    match = re.match(r'(\d{1,2})(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)(\d{2,4})', date_str, re.IGNORECASE)
    if match:
        day, month_es, year = match.groups()
        month_map = {
            'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12
        }
        try:
            month = month_map[month_es.upper()]
            year = int(year)
            if year < 100:
                year += 2000 if year < 50 else 1900
            return datetime.datetime(year, month, int(day))
        except:
            pass
    
    # Estrategia 3: Formato YYYYMMDD o DDMMYYYY
    if len(date_str) == 8 and date_str.isdigit():
        try:
            # Intentar YYYYMMDD
            y, m, d = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return datetime.datetime(y, m, d)
        except:
            pass
        
        try:
            # Intentar DDMMYYYY
            d, m, y = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:8])
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return datetime.datetime(y, m, d)
        except:
            pass
    
    return None

def validate_date_for_products(date_obj: datetime.datetime) -> Tuple[bool, float]:
    """
    Valida si una fecha es razonable para un producto
    
    Returns:
        (es_valida, score_confianza)
    """
    now = datetime.datetime.now()
    years_diff = (date_obj - now).days / 365.25
    
    # Fechas de productos típicamente están entre:
    # - 3 años atrás (productos de larga duración ya en circulación)
    # - 10 años adelante (máximo para fechas de caducidad)
    
    if years_diff < -3:
        return False, 0.0
    
    if years_diff > 10:
        return False, 0.0
    
    # Sistema de scoring
    if -1 <= years_diff <= 5:
        # Rango óptimo: 1 año atrás a 5 años adelante
        score = 1.0
    elif -3 <= years_diff < -1:
        # Aceptable pero antiguo
        score = 0.7
    elif 5 < years_diff <= 10:
        # Aceptable pero muy futuro
        score = 0.6
    else:
        score = 0.5
    
    return True, score


def process_image(img: Image.Image) -> Optional[str]:
    """
    Pipeline principal de procesamiento en memoria con votación
    """
    try:
        # Mejorar imagen antes de procesamiento
        img = enhance_image_for_ocr(img)
        
        logger.debug("Redimensionando imagen...")
        img_array = rescale_image(img)
        
        logger.debug("Detectando contorno del documento...")
        thresh_img = threshold(img_array.copy())
        _, bbox = find_bbox(thresh_img)
        
        logger.debug("Enderezando documento...")
        img_cropped = four_point_transform(img_array, bbox)
        
        logger.debug("Preprocesamiento final...")
        final_img = remove_noise_and_smooth(img_cropped)
        pil_final_img = Image.fromarray(final_img)
        
        logger.debug("Iniciando OCR multi-pass...")
        
        all_dates = []  # Para votación
        
        for config in OCR_CONFIGS:
            logger.debug(f"Probando configuración: {config}")
            
            try:
                data = pytesseract.image_to_data(
                    pil_final_img,
                    config=config,
                    output_type=Output.DICT
                )
                
                # Filtrar por confianza
                text_parts = []
                for i in range(len(data['text'])):
                    conf = int(float(data['conf'][i]))
                    if conf > 30:  # Umbral más bajo pero filtrado
                        text_parts.append(data['text'][i])
                
                text = " ".join(text_parts)
                
                if not text.strip():
                    continue
                
                # Normalizar y buscar fechas
                normalized = normalize_ocr_text(text)
                date_obj = find_date(normalized)
                
                if date_obj:
                    all_dates.append(date_obj)
                    logger.debug(f"Fecha encontrada: {date_obj.date()}")
            
            except Exception as e:
                logger.warning(f"Error con config '{config}': {e}")
                continue
        
        # Votación de fechas
        if not all_dates:
            logger.warning("No se encontraron fechas en ninguna configuración OCR")
            return None
        
        # Contar votos
        date_counter = Counter(all_dates)
        best_date, votes = date_counter.most_common(1)[0]
        
        logger.info(f"Votación de fechas: {dict(date_counter)}")
        logger.info(f"Fecha ganadora: {best_date.date()} con {votes} votos")
        
        return best_date.strftime("%Y-%m-%d")
    
    except Exception as e:
        logger.error(f"Error en process_image: {e}", exc_info=True)
        return None


def process_image_diagnostic(img: Image.Image) -> dict:
    """
    Versión diagnóstica del pipeline
    """
    diag = {}
    
    try:
        diag["1_original"] = {
            "size": f"{img.width}x{img.height}",
            "mode": img.mode
        }
        
        img = enhance_image_for_ocr(img)
        diag["2_enhanced"] = {"status": "ok"}
        
        img_array = rescale_image(img)
        diag["3_rescaled"] = {"size": f"{img_array.shape[1]}x{img_array.shape[0]}"}
        
        thresh_img = threshold(img_array.copy())
        _, bbox = find_bbox(thresh_img)
        diag["4_bbox"] = {"points": bbox.tolist()}
        
        img_cropped = four_point_transform(img_array, bbox)
        diag["5_dewarped"] = {"size": f"{img_cropped.shape[1]}x{img_cropped.shape[0]}"}
        
        final_img = remove_noise_and_smooth(img_cropped)
        diag["6_preprocessed"] = {"size": f"{final_img.shape[1]}x{final_img.shape[0]}"}
        
        pil_final = Image.fromarray(final_img)
        
        ocr_results = {}
        all_dates = []
        
        for config in OCR_CONFIGS:
            try:
                data = pytesseract.image_to_data(pil_final, config=config, output_type=Output.DICT)
                
                text_parts = []
                confidences = []
                
                for i in range(len(data['text'])):
                    conf = int(float(data['conf'][i]))
                    if conf > 30:
                        text_parts.append(data['text'][i])
                        confidences.append(conf)
                
                text = " ".join(text_parts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                
                normalized = normalize_ocr_text(text)
                date_obj = find_date(normalized)
                
                ocr_results[config] = {
                    "text": text[:300] + "..." if len(text) > 300 else text,
                    "words_extracted": len(text_parts),
                    "avg_confidence": f"{avg_conf:.1f}%",
                    "date_found": date_obj.strftime("%Y-%m-%d") if date_obj else None
                }
                
                if date_obj:
                    all_dates.append(date_obj)
            
            except Exception as e:
                ocr_results[config] = {"error": str(e)}
        
        diag["7_ocr_results"] = ocr_results
        
        if all_dates:
            counter = Counter(all_dates)
            best, votes = counter.most_common(1)[0]
            
            diag["8_final_result"] = {
                "success": True,
                "date": best.strftime("%Y-%m-%d"),
                "votes": votes,
                "all_votes": {str(d.date()): c for d, c in counter.items()}
            }
        else:
            diag["8_final_result"] = {
                "success": False,
                "date": None,
                "reason": "No dates found"
            }
        
        return diag
    
    except Exception as e:
        logger.error(f"Error en diagnóstico: {e}", exc_info=True)
        diag["ERROR"] = str(e)
        return diag


def pipeline(img_name: str) -> Optional[str]:
    """
    Wrapper para compatibilidad con código existente (desde disco)
    """
    path = f'./static/uploaded_images/{img_name}.jpeg'
    
    try:
        img = Image.open(path)
        return process_image(img)
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {path}")
        return None
    except Exception as e:
        logger.error(f"Error al procesar {path}: {e}")
        return None