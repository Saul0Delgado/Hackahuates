"""
Módulo de extracción de fechas desde imágenes
Mejor detección de fechas y manejo de errores
Aprendizaje automático de patrones

"""
import pytesseract
from PIL import Image
import numpy as np
import datetime
import re
from dateparser import parse
import logging

from utils import (
    rescale_image,
    threshold,
    crop_img,
    find_bbox,
    remove_noise_and_smooth
)

from pattern_learner import pattern_learner

logger = logging.getLogger(__name__)

# Patrones de fecha más robustos
BASE_DATE_PATTERNS = [
    # --- Prioridad 1: Formatos numéricos completos DD/MM/YYYY (MÁS COMÚN) ---
    # CRÍTICO: Usar \s* para permitir MÚLTIPLES espacios opcionales
    # Ejemplos: 22-08-2025, 22 - 08 - 2025, 22  -  08  -  2025, 07.05.10
    r'\b(\d{1,2})\s*[\/\-\.–—]\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})\b',
    
    # Formato YYYY/MM/DD, YYYY-MM-DD (ISO)
    r'\b(\d{4})\s*[\/\-\.–—]\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{1,2})\b',
    
    # --- Prioridad 2: Formatos de caducidad MM/YY o MM/YYYY ---
    # Maneja: 04-2023, 04/23, 04 - 23, 04-23
    r'\b(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})\b',

    # --- Prioridad 3: Formato DDMMMYY (SIN SEPARADORES) ---
    # NUEVO: Ejemplos: 31MAY26, 15JAN24, 01DEC25
    r'\b(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)(\d{2})\b',
    r'\b(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)(\d{4})\b',

    # --- Prioridad 4: Formatos con prefijos (EXP, VENC, etc.) ---
    # Con formato completo DD/MM/YYYY
    r'(?:EXP|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRY|EXPIRES?|BBE|BB)\s*[:\s]*\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})',
    # Con formato MM/YYYY
    r'(?:EXP|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRY|EXPIRES?)\s*[:\s]*\s*(\d{1,2})\s*[\/\-\.–—]\s*(\d{2,4})',
    # NUEVO: Con formato DDMMMYY
    r'(?:EXP|VENC|CAD|USE\s*BY|BEST\s*BEFORE|EXPIRY|EXPIRES?)\s*[:\s]*\s*(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)(\d{2,4})',
    
    # --- Prioridad 5: Formato MMM-YYYY ---
    # Ejemplos: APR-2023, APR - 2023, APR 2023
    r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[A-Z]*\.?\s*[\/\-\.–—]?\s*(\d{4})\b',
    
    # --- Prioridad 6: Formatos con nombres de mes (texto) ---
    # Mes Día, Año (Jan 15, 2024)
    r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|AUG|SEPT?|OCT|NOV|DEC)[A-Z]*\.?\s+(\d{1,2})[,\s]+(\d{4})\b',
    
    # Día Mes Año (15 Jan 2024)
    r'\b(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUNE|JUL|AUG|SEPT?|OCT|NOV|DEC)[A-Z]*\.?\s+(\d{4})\b',
    
    # DD-MMM-YY (ej: 15-JAN-24, 22-AGO-25)
    r'\b(\d{1,2})\s*[\/\-\.]\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[A-Z]*\.?\s*[\/\-\.]\s*(\d{2,4})\b',
    
    # Meses completos
    r'\b(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{1,2})[,\s]+(\d{4})\b',
    r'\b(\d{1,2})\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})\b',
    
    # --- Prioridad 7: Formatos compactos sin separadores ---
    # YYYYMMDD o DDMMYYYY (debe ser exactamente 8 dígitos)
    r'\b(\d{8})\b',
]

OCR_CONFIGS = [
    '--psm 6 -l eng',  
    '--psm 6 -l spa+eng',
    '--psm 11 -l eng',  
    '--psm 11 -l spa+eng',
    '--psm 3 -l spa+eng',
    '--psm 7 -l eng',  
]

def get_all_patterns():
    """
    Retorna todos los patrones: base + aprendidos
    """
    base = BASE_DATE_PATTERNS.copy()
    learned = pattern_learner.get_all_patterns()
    
    # Patrones aprendidos tienen prioridad (van primero)
    return learned + base

def find_date(text, enable_learning=True):
    """
    Busca y extrae fechas de un texto usando múltiples patrones
    Con capacidad de aprendizaje automático
    
    Args:
        text (str): Texto donde buscar fechas
        enable_learning (bool): Si True, aprende nuevos patrones
        
    Returns:
        datetime: Objeto datetime con la fecha encontrada, o None si no se encuentra
    """
    if not text or not text.strip():
        logger.warning("Texto vacío recibido en find_date")
        return None
    
    logger.debug(f"Buscando fechas en texto: {text[:100]}...")
    
    all_patterns = get_all_patterns()
    dates_found = []
    matched_patterns = set()
    # Buscar con todos los patrones
    for i, pattern in enumerate(all_patterns):
        regex = re.compile(pattern, flags=re.IGNORECASE)
        matches = list(re.finditer(regex, text))
        
        for match in matches:
            date_str = match.group(0)
            logger.debug(f"Patrón {i}: Coincidencia encontrada: '{date_str}'")
            matched_patterns.add(pattern)
            # Intentar parsear la fecha con configuración explícita
            try:
                # Configuración optimizada para fechas de caducidad
                parsed_date = parse(
                    date_str, 
                    languages=['es', 'en'], 
                    settings={
                        'PREFER_DAY_OF_MONTH': 'first',  # DD/MM/YYYY (formato europeo)
                        'STRICT_PARSING': False,
                        'DATE_ORDER': 'DMY'  # Día-Mes-Año
                    }
                )
                
                if parsed_date:
                    # Almacenar: (fecha, texto_original, posición, índice_patrón)
                    dates_found.append((parsed_date, date_str, match.start(), i))
                    logger.debug(f"Fecha parseada: {parsed_date} desde '{date_str}'")

                    if pattern in pattern_learner.learned_patterns:
                        pattern_learner.pattern_usage[pattern] += 1

            except Exception as e:
                logger.debug(f"Error al parsear '{date_str}': {e}")
                continue
    
    if not dates_found and enable_learning:
        logger.info("No se encontraron fechas. Intentando aprender nuevos patrones...")
        
        # Detectar candidatos potenciales
        candidates = pattern_learner.detect_potential_date_strings(text)
        
        if candidates:
            logger.info(f"Encontrados {len(candidates)} candidatos para aprendizaje")
            
            for candidate, pos in candidates:
                # Intentar aprender del candidato
                if pattern_learner.learn_from_candidate(candidate):
                    logger.info(f"Patrón aprendido desde: '{candidate}'")
                    
                    # Reintentar búsqueda con el nuevo patrón
                    return find_date(text, enable_learning=False)
    
    if not dates_found:
        logger.info("No se encontraron fechas válidas en el texto")
        return None
    
    # Ordenar por: 1) Prioridad del patrón, 2) Posición en el texto
    dates_found.sort(key=lambda x: (x[3], x[2]))
    
    # Filtrar fechas en rango razonable
    now = datetime.datetime.now()
    valid_dates = []
    
    for date, date_str, pos, pattern_idx in dates_found:
        years_diff = (date - now).days / 365.25
        
        # Para fechas de caducidad: entre 5 años atrás y 20 adelante
        if -5 <= years_diff <= 20:
            valid_dates.append((date, date_str, pos, abs(years_diff)))
            logger.debug(f"Fecha válida: {date} (diferencia: {years_diff:.1f} años)")
    
    if not valid_dates:
        if dates_found:
            logger.warning(f"No hay fechas en rango válido, usando la primera encontrada: {dates_found[0][0]}")
            return dates_found[0][0]
        return None
    
    # Ordenar por cercanía temporal (fechas más cercanas al presente primero)
    valid_dates.sort(key=lambda x: x[3])
    
    selected_date = valid_dates[0][0]
    logger.info(f"Fecha seleccionada: {selected_date} desde '{valid_dates[0][1]}'")
    return selected_date


def normalize_ocr_text(text):
    """
    Normaliza el texto del OCR para mejorar detección de fechas
    
    Args:
        text (str): Texto crudo del OCR
        
    Returns:
        str: Texto normalizado
    """
    if not text:
        return text
    
    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'\s+', ' ', text)
    
    # Corregir caracteres comúnmente confundidos en OCR
    corrections = {
        'O': '0',  # Letra O por cero (solo en contexto numérico)
        'o': '0',
        'I': '1',  # Letra I por uno
        'l': '1',
        '|': '1',
    }
    
    # Aplicar correcciones solo en contextos numéricos
    text = re.sub(r'(?<=\d)[Oo](?=\d)', '0', text)
    text = re.sub(r'(?<=\d)[Il|](?=\d)', '1', text)
    text = re.sub(r'[Oo](?=\d)', '0', text)
    text = re.sub(r'(?<=\d)[Oo]', '0', text)
    
    logger.debug(f"Texto normalizado: {text[:100]}...")
    return text


def process_image(img: Image.Image):
    """
    Pipeline de procesamiento en memoria 
    Acepta un objeto PIL Image, lo procesa y devuelve una fecha

    Args: 
        img (PIL Image.Image) Objeto de imagen
    Returns: 
        str: Fecha en formato YYYY-MM-DD, None si no se encuentra
    """

    try:
        logger.debug("Redimensionando imagen...")
        img_array = rescale_image(img)
        
        logger.debug("Removiendo ruido y suavizando...")
        final_img = remove_noise_and_smooth(img_array)
        
        pil_final_img = Image.fromarray(final_img)
        
        logger.debug("Ejecutando OCR (estrategia multi-pass)...")
        
        # Intentar varias configuraciones de OCR
        for config in OCR_CONFIGS:
            logger.debug(f"Probando config OCR: {config}")
            text = pytesseract.image_to_string(
                pil_final_img,
                config=config
            )
            
            logger.debug(f"Texto extraído ({len(text)} caracteres): {text[:200]}...")
            
            if not text or not text.strip():
                continue
            
            # NUEVO: Normalizar texto antes de buscar fechas
            normalized_text = normalize_ocr_text(text)
            
            # Buscar fechas en el texto normalizado
            date = find_date(normalized_text)
            
            if date:
                formatted_date = date.strftime("%Y-%m-%d")
                logger.info(f"Fecha encontrada con config '{config}': {formatted_date}")
                return formatted_date
        
        logger.warning("No se encontró fecha después de probar todas las configs de OCR.")
        return None

    except Exception as e:
        logger.error(f"Error en process_image: {e}", exc_info=True)
        return None


def pipeline(img_name: str) -> str | None:
    """
    Wrapper del pipeline para leer desde disco.
    Usado por los endpoints de diagnóstico.
    
    Args:
        img_name (str): Nombre del archivo (sin extensión) en la carpeta de uploads
        
    Returns:
        str: Fecha en formato YYYY-MM-DD, o None si no se encuentra
    """
    path = f'./static/uploaded_images/{img_name}.jpeg'
    
    try:
        logger.info(f"Iniciando pipeline (desde disco) para: {img_name}")
        img = Image.open(path)
        logger.debug(f"Imagen cargada: {img.size}, modo: {img.mode}")
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {path}")
        return None
    except Exception as e:
        logger.error(f"Error al abrir imagen {path}: {e}")
        return None
    
    # Llamar a la función de procesamiento en memoria
    formatted_date = process_image(img)
    
    if formatted_date:
        logger.info(f"Pipeline (desde disco) completado. Fecha: {formatted_date}")
    else:
        logger.warning(f"Pipeline (desde disco) no encontró fecha para {img_name}")
        
    return formatted_date

def extract_date_with_confidence(img_name):
    """
    Versión extendida que retorna la fecha y un nivel de confianza
    
    Args:
        img_name (str): Nombre del archivo (sin extensión)
        
    Returns:
        tuple: (fecha_str, confianza) o (None, 0) si no se encuentra
    """
    # Implementación futura para agregar métricas de confianza
    date = pipeline(img_name)
    confidence = 0.50 if date else 0.0  # Placeholder
    return date, confidence