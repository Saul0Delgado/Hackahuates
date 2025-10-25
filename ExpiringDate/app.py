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
from pytesseract import Output

from extract_date import process_image, pipeline,process_image_diagnostic
from utils import (
    random_string,
    rescale_image, 
    threshold, 
    find_bbox, 
    four_point_transform,  
    remove_noise_and_smooth
)

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
Extraction = api.namespace('extraction', description='Operaciones de extracción de fechas')
Test = api.namespace('test', description='Operaciones de test para extracción de fechas')
Auto_Learning = api.namespace('auto-learning', description='Operaciones aprendizaje automatico de expresiones regulares para extracción de fechas')
Health = api.namespace('health', description='Verificacion de vida de la API')
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

@Health.route('/health')
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
# LOS ENDPOINTS DE DIAGNÓSTICO 
# SE MANTIENEN IGUALES. USAN EL pipeline() original
# ==================================================================
@Test.route('/test/tesseract')
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

@Test.route('/test/ocr')
class TestOCR(Resource):
    @Test.expect(upload_parser)
    @Test.response(200, 'OCR ejecutado exitosamente')
    @Test.response(400, 'Error en los datos de entrada')
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

@Test.route('/test/patterns')
class TestPatterns(Resource):
    @Test.expect(reqparse.RequestParser().add_argument('text', type=str, required=True, location='json', help='Texto donde buscar fechas'))
    @Test.response(200, 'Patrones probados exitosamente')
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
            from extract_date import get_all_patterns
            all_patterns = get_all_patterns()
            results = []
            
            for i, pattern in enumerate(all_patterns):
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
                'total_patterns_tested': len(all_patterns),
                'total_matches_found': total_matches,
                'pattern_results': results
            }, 200
            
        except Exception as e:
            return {
                "error": "Error al procesar el texto",
                "details": str(e)
            }, 500

@Test.route('/test/full_diagnostic')
class FullDiagnostic(Resource):
    @Test.expect(upload_parser)
    @Test.response(200, 'Diagnóstico completo ejecutado')
    def post(self):
        """
        Ejecuta un diagnóstico completo: preprocesamiento, OCR, detección de patrones y extracción de fechas
        """
        try:
            args = upload_parser.parse_args()
            img_file = args['image']
            
            if not img_file or img_file.filename == '':
                return {"error": "No se envió ningún archivo"}, 400
            
            # --- INICIO DE NUEVA LÓGICA ---
            
            # Importar la nueva función de diagnóstico
            
            logger.info(f"Ejecutando diagnóstico completo en: {img_file.filename}")

            # Cargar imagen en memoria
            img = Image.open(img_file.stream)
            
            # Ejecutar el pipeline de diagnóstico
            diagnostic_result = process_image_diagnostic(img)
            
            final_date = diagnostic_result.get("7_final_result", {}).get("date")
            
            return {
                'success': True,
                'final_result': final_date,
                'diagnostic_steps': diagnostic_result
            }, 200
            
            # --- FIN DE NUEVA LÓGICA ---
            
        except Exception as e:
            logger.error(f"Error en diagnóstico completo: {str(e)}", exc_info=True)
            return {
                "error": "Error en diagnóstico",
                "details": str(e)
            }, 500

# ==================================================================
# ENDPOINTS DE APRENDIZAJE DE PATRONES 
# ==================================================================
@Auto_Learning.route('/patterns/learned')
class LearnedPatterns(Resource):
    def get(self):
        """
        Lista todos los patrones aprendidos
        """
        from pattern_learner import pattern_learner
        
        patterns = pattern_learner.get_all_patterns()
        top_patterns = pattern_learner.get_top_patterns(20)
        
        return {
            'success': True,
            'total_learned': len(patterns),
            'patterns': patterns,
            'most_used': [
                {'pattern': p, 'usage_count': count}
                for p, count in top_patterns
            ]
        }, 200

@Auto_Learning.route('/patterns/prune')
class PrunePatterns(Resource):
    def post(self):
        """
        Elimina patrones poco usados
        """
        from pattern_learner import pattern_learner
        
        parser = reqparse.RequestParser()
        parser.add_argument('min_usage', type=int, default=3, location='json')
        args = parser.parse_args()
        
        before = len(pattern_learner.learned_patterns)
        pattern_learner.prune_unused_patterns(args['min_usage'])
        after = len(pattern_learner.learned_patterns)
        
        return {
            'success': True,
            'removed': before - after,
            'remaining': after
        }, 200

@Auto_Learning.route('/patterns/reset')
class ResetPatterns(Resource):
    def post(self):
        """
        Reinicia todos los patrones aprendidos (CUIDADO)
        """
        from pattern_learner import pattern_learner
        import os
        
        try:
            if os.path.exists(pattern_learner.LEARNED_PATTERNS_FILE):
                os.remove(pattern_learner.LEARNED_PATTERNS_FILE)
            
            pattern_learner.learned_patterns = []
            pattern_learner.pattern_usage.clear()
            
            return {
                'success': True,
                'message': 'Patrones aprendidos eliminados'
            }, 200
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500


# ==================================================================
# ENDPOINTS DE PRODUCCIÓN (MODIFICADOS)
# ==================================================================

@Extraction.route('/extract_date')
class SendB64Image(Resource):
    @Extraction.expect(b64_parser)
    @Extraction.response(200, 'Fecha extraída exitosamente')
    @Extraction.response(400, 'Error en los datos de entrada')
    @Extraction.response(422, 'No se pudo procesar la imagen')
    @Extraction.response(500, 'Error interno del servidor')
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

@Extraction.route('/extract_date_from_image')
class UploadImage(Resource):
    @Extraction.expect(upload_parser)
    @Extraction.response(200, 'Fecha extraída exitosamente')
    @Extraction.response(400, 'Error en los datos de entrada')
    @Extraction.response(422, 'No se pudo procesar la imagen')
    @Extraction.response(500, 'Error interno del servidor')
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