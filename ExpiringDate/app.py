"""
API Flask para extracción de fechas de caducidad desde imágenes
Versión mejorada con mejor manejo de errores, logging y validación
"""
from flask import Flask, send_from_directory
from flask_restx import Api, Resource, reqparse
from flask_cors import CORS
from base64 import b64decode
from werkzeug.datastructures import FileStorage
import os
import logging
from datetime import datetime
import io  
from PIL import Image 

from extract_date import process_image, pipeline
from utils import random_string

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de la app
app = Flask(__name__)
CORS(app)  # Habilitar CORS para uso con frontends

# Configuración
UPLOAD_FOLDER = './static/uploaded_images'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Inicializar API con Swagger
api = Api(
    app,
    version='2.0',
    title='OCR Date Extractor API',
    description='API REST para extraer fechas de caducidad de imágenes usando OCR y procesamiento de imágenes.',
    doc='/docs',
    prefix='/api'
)

# Namespace
ns = api.namespace('extraction', description='Operaciones de extracción de fechas')

# Parsers
b64_parser = reqparse.RequestParser()
b64_parser.add_argument(
    'base_64_image_content',
    type=str,
    required=True,
    location='json',
    help='Imagen codificada en Base64 (sin el prefijo data:image/...)'
)

upload_parser = reqparse.RequestParser()
upload_parser.add_argument(
    'image',
    type=FileStorage,
    location='files',
    required=True,
    help='Archivo de imagen (multipart/form-data)'
)

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_base64(b64_string):
    """Valida que el string sea base64 válido"""
    try:
        # Intentar decodificar
        decoded = b64decode(b64_string, validate=True)
        return True, decoded
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    """Ruta principal - redirige a la documentación"""
    return {
        'message': 'OCR Date Extractor API',
        'version': '2.0',
        'documentation': '/docs',
        'endpoints': {
            'base64': '/api/extraction/extract_date',
            'upload': '/api/extraction/extract_date_from_image',
            'health': '/api/extraction/health'
        }
    }

@ns.route('/health')
class Health(Resource):
    def get(self):
        """
        Endpoint de salud para verificar el estado de la API
        """
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0'
        }

# ==================================================================
# LOS ENDPOINTS DE DIAGNÓSTICO (/test/...)
# SE MANTIENEN IGUALES. USAN EL pipeline() original
# que lee de disco, lo cual es correcto para depuración.
# ==================================================================
@ns.route('/test/tesseract')
class TestTesseract(Resource):
    def get(self):
        """
        Verifica que Tesseract esté instalado y funcionando correctamente
        """
        try:
            import pytesseract
            
            # Obtener versión
            version = pytesseract.get_tesseract_version()
            
            # Obtener idiomas disponibles
            try:
                langs = pytesseract.get_languages()
            except:
                langs = []
            
            return {
                'success': True,
                'tesseract_installed': True,
                'version': str(version),
                'languages_available': langs,
                'spanish_available': 'spa' in langs,
                'english_available': 'eng' in langs,
                'recommendation': 'spa+eng' if ('spa' in langs and 'eng' in langs) else 'eng'
            }, 200
            
        except Exception as e:
            return {
                'success': False,
                'tesseract_installed': False,
                'error': str(e),
                'message': 'Tesseract OCR no está instalado o no se encuentra en el PATH',
                'installation_guide': {
                    'ubuntu_debian': 'sudo apt-get install tesseract-ocr tesseract-ocr-spa',
                    'macos': 'brew install tesseract tesseract-lang',
                    'windows': 'https://github.com/UB-Mannheim/tesseract/wiki'
                }
            }, 500

@ns.route('/test/ocr')
class TestOCR(Resource):
    @ns.expect(upload_parser)
    @ns.response(200, 'OCR ejecutado exitosamente')
    @ns.response(400, 'Error en los datos de entrada')
    def post(self):
        """
        Prueba OCR en una imagen y muestra el texto extraído sin procesar fechas
        Útil para diagnosticar problemas de detección
        """
        try:
            args = upload_parser.parse_args()
            img = args['image']
            
            if not img or img.filename == '':
                return {"error": "No se envió ningún archivo"}, 400
            
            # Guardar imagen temporalmente
            file_name = random_string()
            file_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.jpeg')
            img.save(file_path)
            
            logger.info(f"Ejecutando test OCR en: {file_name}")
            
            # Cargar imagen
            # from PIL import Image # Ya está importado arriba
            import pytesseract
            pil_img = Image.open(file_path)
            
            # Ejecutar OCR con diferentes configuraciones
            results = {}
            
            configs = {
                'default': '',
                'psm_6': '--psm 6',
                'psm_3': '--psm 3',
                'psm_11': '--psm 11',
                'spanish': '--psm 6 -l spa',
                'spanish_english': '--psm 6 -l spa+eng',
            }
            
            for config_name, config_params in configs.items():
                try:
                    text = pytesseract.image_to_string(pil_img, config=config_params)
                    results[config_name] = {
                        'text': text,
                        'length': len(text),
                        'lines': len(text.split('\n')),
                        'config': config_params if config_params else 'default'
                    }
                except Exception as e:
                    results[config_name] = {
                        'error': str(e)
                    }
            
            # Limpiar archivo temporal
            try:
                os.remove(file_path)
            except:
                pass
            
            return {
                'success': True,
                'filename': img.filename,
                'image_size': f"{pil_img.size[0]}x{pil_img.size[1]}",
                'ocr_results': results,
                'recommendation': 'Usa la configuración que tenga más caracteres detectados'
            }, 200
            
        except Exception as e:
            logger.error(f"Error en test OCR: {str(e)}", exc_info=True)
            return {
                "error": "Error al procesar la imagen",
                "details": str(e)
            }, 500

@ns.route('/test/patterns')
class TestPatterns(Resource):
    @ns.expect(reqparse.RequestParser().add_argument('text', type=str, required=True, location='json', help='Texto donde buscar fechas'))
    @ns.response(200, 'Patrones probados exitosamente')
    def post(self):
        """
        Prueba todos los patrones de fecha en un texto dado
        Útil para verificar qué patrones detectan fechas en tu texto
        """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('text', type=str, required=True, location='json')
            args = parser.parse_args()
            text = args['text']
            
            import re
            from extract_date import DATE_PATTERNS
            
            results = []
            
            for i, pattern in enumerate(DATE_PATTERNS):
                regex = re.compile(pattern, flags=re.IGNORECASE)
                matches = list(re.finditer(regex, text))
                
                pattern_result = {
                    'pattern_index': i,
                    'pattern': pattern,
                    'matches_found': len(matches),
                    'matches': []
                }
                
                for match in matches:
                    pattern_result['matches'].append({
                        'text': match.group(0),
                        'position': match.start(),
                        'groups': match.groups()
                    })
                
                results.append(pattern_result)
            
            total_matches = sum(r['matches_found'] for r in results)
            
            return {
                'success': True,
                'text_analyzed': text,
                'text_length': len(text),
                'total_patterns_tested': len(DATE_PATTERNS),
                'total_matches_found': total_matches,
                'pattern_results': results
            }, 200
            
        except Exception as e:
            return {
                "error": "Error al procesar el texto",
                "details": str(e)
            }, 500

@ns.route('/test/full_diagnostic')
class FullDiagnostic(Resource):
    @ns.expect(upload_parser)
    @ns.response(200, 'Diagnóstico completo ejecutado')
    def post(self):
        """
        Ejecuta un diagnóstico completo: preprocesamiento, OCR, detección de patrones y extracción de fechas
        """
        try:
            args = upload_parser.parse_args()
            img = args['image']
            
            if not img or img.filename == '':
                return {"error": "No se envió ningún archivo"}, 400
            
            # Guardar imagen
            file_name = random_string()
            file_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.jpeg')
            img.save(file_path)
            
            logger.info(f"Ejecutando diagnóstico completo en: {file_name}")
            
            diagnostic_result = {
                'filename': img.filename,
                'steps': {}
            }
            
            # Paso 1: Información de la imagen
            # from PIL import Image # Ya importado
            import pytesseract
            import cv2
            
            pil_img = Image.open(file_path)
            diagnostic_result['steps']['1_image_info'] = {
                'size': f"{pil_img.size[0]}x{pil_img.size[1]}",
                'mode': pil_img.mode,
                'format': pil_img.format
            }
            
            # Paso 2: Preprocesamiento
            from utils import rescale_image, threshold, find_bbox, crop_img, remove_noise_and_smooth
            
            img_array = rescale_image(pil_img)
            diagnostic_result['steps']['2_preprocessing'] = {
                'rescaled': True,
                'size_after_rescale': f"{img_array.shape[1]}x{img_array.shape[0]}"
            }
            
            # Paso 3: OCR con múltiples configuraciones
            ocr_results = {}
            configs = {
                'default': '',
                'psm_6_spa_eng': '--psm 6 -l spa+eng',
                'psm_3_spa_eng': '--psm 3 -l spa+eng',
            }
            
            for config_name, config_params in configs.items():
                try:
                    text = pytesseract.image_to_string(Image.fromarray(img_array), config=config_params)
                    ocr_results[config_name] = {
                        'text': text[:500],  # Primeros 500 caracteres
                        'full_length': len(text),
                        'has_content': len(text.strip()) > 0
                    }
                except Exception as e:
                    ocr_results[config_name] = {'error': str(e)}
            
            diagnostic_result['steps']['3_ocr'] = ocr_results
            
            # Paso 4: Buscar fechas en cada resultado
            from extract_date import find_date
            import re
            
            dates_found = {}
            for config_name, ocr_data in ocr_results.items():
                if 'text' in ocr_data:
                    # Buscar con find_date
                    date = find_date(ocr_data['text'])
                    
                    # Buscar con regex simple para MM-YYYY
                    mm_yyyy_pattern = r'\b(\d{2})-(\d{4})\b'
                    mm_yyyy_matches = re.findall(mm_yyyy_pattern, ocr_data['text'])
                    
                    dates_found[config_name] = {
                        'find_date_result': date.strftime("%Y-%m-%d") if date else None,
                        'mm_yyyy_matches': mm_yyyy_matches,
                        'text_preview': ocr_data['text'][:200]
                    }
            
            diagnostic_result['steps']['4_date_detection'] = dates_found
            
            # Paso 5: Pipeline completo
            # (Usamos el pipeline original que lee de disco)
            try:
                final_date = pipeline(file_name)
                diagnostic_result['steps']['5_pipeline'] = {
                    'success': final_date is not None,
                    'date': final_date
                }
            except Exception as e:
                diagnostic_result['steps']['5_pipeline'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Limpiar
            try:
                os.remove(file_path)
            except:
                pass
            
            # Resumen
            dates_detected = [d for d in dates_found.values() if d.get('find_date_result')]
            diagnostic_result['summary'] = {
                'total_ocr_configs_tested': len(configs),
                'configs_with_text': sum(1 for r in ocr_results.values() if r.get('has_content')),
                'dates_detected': len(dates_detected),
                'final_result': diagnostic_result['steps']['5_pipeline'].get('date'),
                'success': diagnostic_result['steps']['5_pipeline'].get('success', False)
            }
            
            return {
                'success': True,
                'diagnostic': diagnostic_result
            }, 200
            
        except Exception as e:
            logger.error(f"Error en diagnóstico completo: {str(e)}", exc_info=True)
            return {
                "error": "Error en diagnóstico",
                "details": str(e)
            }, 500

# ==================================================================
# ENDPOINTS DE PRODUCCIÓN (MODIFICADOS)
# ==================================================================

@ns.route('/extract_date')
class SendB64Image(Resource):
    @ns.expect(b64_parser)
    @ns.response(200, 'Fecha extraída exitosamente')
    @ns.response(400, 'Error en los datos de entrada')
    @ns.response(422, 'No se pudo procesar la imagen')
    @ns.response(500, 'Error interno del servidor')
    def post(self):
        """
        Extrae la fecha de una imagen codificada en Base64 (en memoria)
        
        Envía un JSON con el campo 'base_64_image_content' conteniendo
        la imagen en Base64 (sin el prefijo data:image/...)
        """
        try:
            args = b64_parser.parse_args()
            b64_img = args['base_64_image_content']
            
            # Validar que no esté vacío
            if not b64_img or not b64_img.strip():
                logger.warning("Se recibió una cadena Base64 vacía")
                return {"error": "La imagen Base64 no puede estar vacía"}, 400
            
            # Remover posible prefijo data:image
            if 'base64,' in b64_img:
                b64_img = b64_img.split('base64,')[1]
            
            # Validar Base64
            is_valid, decoded_bytes = validate_base64(b64_img)
            if not is_valid:
                logger.error(f"Base64 inválido: {decoded_bytes}")
                return {
                    "error": "La cadena Base64 no es válida",
                    "details": decoded_bytes
                }, 400
            
            # --- INICIO DE MODIFICACIÓN ---
            # Cargar imagen desde bytes en memoria
            logger.info("Procesando imagen Base64 en memoria...")
            img = Image.open(io.BytesIO(decoded_bytes))
            
            # Procesar imagen en memoria
            date = process_image(img)
            # --- FIN DE MODIFICACIÓN ---
            
            if date is None:
                logger.warning(f"No se encontró fecha en la imagen Base64")
                return {
                    "error": "No se pudo encontrar una fecha válida en la imagen",
                    "suggestion": "Asegúrate de que la imagen contenga texto legible con fechas"
                }, 422
            
            logger.info(f"Fecha extraída exitosamente: {date}")
            return {
                "success": True,
                "date": date,
                "format": "YYYY-MM-DD"
            }, 200
            
        except Exception as e:
            logger.error(f"Error inesperado en extract_date: {str(e)}", exc_info=True)
            return {
                "error": "Error interno del servidor",
                "details": str(e)
            }, 500

@ns.route('/extract_date_from_image')
class UploadImage(Resource):
    @ns.expect(upload_parser)
    @ns.response(200, 'Fecha extraída exitosamente')
    @ns.response(400, 'Error en los datos de entrada')
    @ns.response(422, 'No se pudo procesar la imagen')
    @ns.response(500, 'Error interno del servidor')
    def post(self):
        """
        Extrae la fecha de un archivo de imagen cargado (en memoria)
        
        Envía un formulario multipart/form-data con el campo 'image'
        conteniendo el archivo de imagen
        """
        try:
            args = upload_parser.parse_args()
            img_file = args['image'] # Es un FileStorage
            
            # Validar que se envió un archivo
            if not img_file or img_file.filename == '':
                logger.warning("No se envió ningún archivo")
                return {"error": "No se envió ningún archivo"}, 400
            
            # Validar extensión
            if not allowed_file(img_file.filename):
                logger.warning(f"Extensión no permitida: {img_file.filename}")
                return {
                    "error": "Tipo de archivo no permitido",
                    "allowed_extensions": list(ALLOWED_EXTENSIONS)
                }, 400
            
            # --- INICIO DE MODIFICACIÓN ---
            # Cargar imagen desde el stream del archivo en memoria
            logger.info(f"Procesando imagen '{img_file.filename}' en memoria...")
            img = Image.open(img_file.stream)
            
            # Procesar imagen en memoria
            date = process_image(img)
            # --- FIN DE MODIFICACIÓN ---
            
            if date is None:
                logger.warning(f"No se encontró fecha en la imagen {img_file.filename}")
                return {
                    "error": "No se pudo encontrar una fecha válida en la imagen",
                    "suggestion": "Asegúrate de que la imagen contenga texto legible con fechas"
                }, 422
            
            logger.info(f"Fecha extraída exitosamente: {date}")
            return {
                "success": True,
                "date": date,
                "format": "YYYY-MM-DD",
                "original_filename": img_file.filename
            }, 200
            
        except Exception as e:
            logger.error(f"Error inesperado en extract_date_from_image: {str(e)}", exc_info=True)
            return {
                "error": "Error interno del servidor",
                "details": str(e)
            }, 500

if __name__ == "__main__":
    # Crear directorio de uploads si no existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        logger.info(f"Directorio creado: {UPLOAD_FOLDER}")
    
    # Información de inicio
    logger.info("=" * 60)
    logger.info("Iniciando OCR Date Extractor API v2.0")
    logger.info("=" * 60)
    logger.info("Documentación Swagger: http://127.0.0.1:5000/docs")
    logger.info("API Base URL: http://127.0.0.1:5000/api")
    logger.info("=" * 60)
    
    # Iniciar servidor
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )