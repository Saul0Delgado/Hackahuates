"""
Utilidades para procesamiento de imágenes
Versión mejorada con mejor manejo de errores y optimizaciones
"""
import os
import re
import cv2
import numpy as np
from PIL import Image
import random
import string
from skimage.filters import threshold_local
import logging

logger = logging.getLogger(__name__)

def random_string(length=12):
    """
    Genera una cadena aleatoria segura para nombres de archivo
    
    Args:
        length (int): Longitud de la cadena (default: 12)
        
    Returns:
        str: Cadena aleatoria alfanumérica
    """
    # Usar caracteres alfanuméricos para mayor seguridad
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def rescale_image(img, max_dimension=1024):
    """
    Redimensiona imágenes grandes manteniendo la relación de aspecto
    
    Args:
        img (PIL.Image): Imagen a redimensionar
        max_dimension (int): Dimensión máxima permitida
        
    Returns:
        numpy.ndarray: Imagen redimensionada con borde
    """
    try:
        # Obtener dimensiones originales
        width, height = img.size
        logger.debug(f"Tamaño original: {width}x{height}")
        
        # Calcular factor de escala
        factor = min(1.0, float(max_dimension) / max(width, height))
        
        if factor < 1.0:
            new_width = int(width * factor)
            new_height = int(height * factor)
            logger.debug(f"Redimensionando a: {new_width}x{new_height}")
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convertir a array numpy
        img = np.array(img)
        
        # Asegurar que la imagen esté en formato BGR para OpenCV
        if len(img.shape) == 2:  # Imagen en escala de grises
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:  # Imagen con canal alpha (RGBA)
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif img.shape[2] == 3:  # Ya está en RGB, convertir a BGR
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # Agregar borde negro
        img = cv2.copyMakeBorder(
            img, 10, 10, 10, 10,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0]
        )
        
        return img
        
    except Exception as e:
        logger.error(f"Error en rescale_image: {e}")
        raise

def auto_canny(img, sigma=0.50):
    """
    Detección automática de bordes usando Canny con umbral adaptativo
    
    Args:
        img (numpy.ndarray): Imagen en escala de grises
        sigma (float): Factor para calcular umbrales (default: 0.50)
        
    Returns:
        numpy.ndarray: Imagen con bordes detectados
    """
    # Calcular la mediana de las intensidades de píxeles
    med = np.median(img)
    
    # Calcular umbrales basados en la mediana
    lower = int(max(0, (1.0 - sigma) * med))
    upper = int(min(255, (1.0 + sigma) * med))
    
    logger.debug(f"Canny thresholds: lower={lower}, upper={upper}")
    
    # Aplicar detección de bordes Canny
    edge_img = cv2.Canny(img, lower, upper)
    
    return edge_img

def edged(img):
    """
    Encuentra bordes en la imagen usando preprocesamiento y Canny
    
    Args:
        img (numpy.ndarray): Imagen en color (BGR)
        
    Returns:
        numpy.ndarray: Imagen con bordes detectados
    """
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar blur gaussiano para reducir ruido
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detectar bordes
    edge_img = auto_canny(blur)
    
    return edge_img

def threshold(img):
    """
    Aplica umbralización a la imagen combinando Otsu y detección de bordes
    
    Args:
        img (numpy.ndarray): Imagen en color (BGR)
        
    Returns:
        numpy.ndarray: Imagen umbralizada binaria
    """
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invertir imagen (texto oscuro sobre fondo claro -> texto claro sobre fondo oscuro)
    gray = cv2.bitwise_not(gray)
    
    # Aplicar blur para reducir ruido
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Umbralización usando método de Otsu
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Obtener bordes
    edge_img = edged(img)
    
    # Combinar umbralización con detección de bordes
    thresh = cv2.bitwise_or(edge_img, thresh)
    
    return thresh

def find_bbox(thresh):
    """
    Encuentra el bounding box del recibo/documento en la imagen
    
    Args:
        thresh (numpy.ndarray): Imagen umbralizada
        
    Returns:
        tuple: (contornos, bounding_box) donde bounding_box es un array de 4 puntos
    """
    # Encontrar contornos
    cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Manejo robusto si no se encuentran contornos
    if not cnts or len(cnts) == 0:
        logger.warning("No se encontraron contornos. Usando imagen completa.")
        h, w = thresh.shape[:2]
        bbox = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=int)
        return [], bbox
    
    # Ordenar contornos por área (mayor a menor)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    
    # Seleccionar el contorno apropiado
    # Si hay más de un contorno, usar el segundo (típicamente el documento)
    # Si solo hay uno, usar el más grande
    if len(cnts) > 1:
        contour_to_use = cnts[1]
        logger.debug("Usando el segundo contorno más grande")
    else:
        contour_to_use = cnts[0]
        logger.debug("Usando el contorno más grande")
    
    # Encontrar el rectángulo de área mínima
    rect = cv2.minAreaRect(contour_to_use)
    bbox = cv2.boxPoints(rect)
    bbox = bbox.astype(int)
    
    logger.debug(f"Bounding box encontrado: {bbox}")
    
    return cnts, bbox

def crop_img(img, bbox):
    """
    Recorta la imagen usando el bounding box del documento
    
    Args:
        img (numpy.ndarray): Imagen original
        bbox (numpy.ndarray): Bounding box con 4 puntos
        
    Returns:
        numpy.ndarray: Imagen recortada
    """
    try:
        # Encontrar las coordenadas extremas
        left, top = bbox[bbox.sum(axis=1).argmin()]
        right, bottom = bbox[bbox.sum(axis=1).argmax()]
        
        # Asegurar que las coordenadas estén dentro de los límites
        h, w = img.shape[:2]
        left = max(0, left)
        top = max(0, top)
        right = min(w, right)
        bottom = min(h, bottom)
        
        # Recortar
        img_cropped = img[top:bottom, left:right]
        
        logger.debug(f"Imagen recortada: {img_cropped.shape}")
        
        return img_cropped
        
    except Exception as e:
        logger.error(f"Error al recortar imagen: {e}")
        return img  # Retornar imagen original si falla

def image_smoothening(img):
    """
    Suaviza la imagen aplicando umbralización y filtros
    
    Args:
        img (numpy.ndarray): Imagen en escala de grises
        
    Returns:
        numpy.ndarray: Imagen suavizada
    """
    # Primera umbralización
    _, th1 = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
    
    # Aplicar blur gaussiano
    blur = cv2.GaussianBlur(th1, (5, 5), 0)
    
    # Segunda umbralización con Otsu
    _, th2 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return th2

def remove_noise_and_smooth(img):
    """
    Preprocesamiento final: remueve ruido y suaviza para mejorar OCR
    
    Args:
        img (numpy.ndarray): Imagen en color (BGR)
        
    Returns:
        numpy.ndarray: Imagen preprocesada lista para OCR
    """
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Umbralización adaptativa local
    thresh = threshold_local(gray, 11, offset=10, method="gaussian")
    thresh = (gray > thresh).astype("uint8") * 255
    
    # Operaciones morfológicas para limpiar
    kernel = np.ones((1, 1), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Suavizado adicional
    smooth_img = image_smoothening(gray)
    
    # Combinar ambas umbralizaciones
    final_img = cv2.bitwise_or(smooth_img, thresh)
    
    logger.debug(f"Imagen final preprocesada: {final_img.shape}")
    
    return final_img

