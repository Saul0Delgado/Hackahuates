import cv2
import pytesseract
import re
import numpy as np
import argparse
from imutils.object_detection import non_max_suppression

# --- 1. CONFIGURACIÓN DE ARGUMENTOS ---
# Esto nos permite pasar la imagen y el modelo desde la terminal
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
    help="Ruta a la imagen de entrada")
ap.add_argument("-e", "--east", type=str,
    default="frozen_east_text_detection.pb",
    help="Ruta al detector EAST")
ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
    help="Probabilidad mínima para aceptar una región de texto")
ap.add_argument("-w", "--width", type=int, default=320,
    help="Ancho de la imagen (debe ser múltiplo de 32)")
ap.add_argument("-H", "--height", type=int, default=320,
    help="Alto de la imagen (debe ser múltiplo de 32)")
args = vars(ap.parse_args())

# --- 2. PATRONES DE FECHA (Regex) ---
# Lista de patrones de expresiones regulares para encontrar fechas.
# Puedes añadir más patrones aquí si es necesario.
date_patterns = [
    r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",  # Ej: 31/12/2025, 31-12-25, 1.1.2025
    r"(\d{2}(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2,4})", # Ej: 25DEC2025
    r"(EXP|VEN)\s*(\d{1,2}[./-]\d{2,4})", # Ej: EXP 12/25, VEN 12/2025
    r"(\d{2}/\d{2})" # MM/YY
]
# Compilamos los patrones para eficiencia
compiled_patterns = [re.compile(p, re.IGNORECASE) for p in date_patterns]

def find_dates_in_text(text):
    """
    Busca todos los patrones de fecha en un bloque de texto.
    """
    found_dates = []
    for pattern in compiled_patterns:
        matches = pattern.finditer(text)
        for match in matches:
            # Capturamos el grupo que contiene la fecha
            if len(match.groups()) > 0:
                 # Usamos el grupo 1, que es la fecha real
                 found_dates.append(match.group(1))
            else:
                 found_dates.append(match.group(0))
    
    # Limpieza simple de caracteres que Tesseract confunde
    cleaned_dates = []
    for date in found_dates:
        # Reemplazar 'O' por '0', 'l' o 'I' por '1'
        date = date.replace('O', '0').replace('o', '0')
        date = date.replace('l', '1').replace('I', '1')
        cleaned_dates.append(date)

    return list(set(cleaned_dates)) # Devolvemos fechas únicas

def decode_predictions(scores, geometry):
    """
    Decodifica los resultados del modelo EAST.
    """
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(0, numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):
            if scoresData[x] < args["min_confidence"]:
                continue

            (offsetX, offsetY) = (x * 4.0, y * 4.0)
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
    return (rects, confidences)

# --- 3. CARGAR IMAGEN Y MODELO ---
image = cv2.imread(args["image"])
orig = image.copy()
(origH, origW) = image.shape[:2]

# Calculamos la proporción para escalar las coordenadas de vuelta
rW = origW / float(args["width"])
rH = origH / float(args["height"])

# Redimensionamos la imagen al tamaño requerido por EAST
image = cv2.resize(image, (args["width"], args["height"]))
(H, W) = image.shape[:2]

# Cargamos el detector EAST
print("[INFO] Cargando el detector de texto EAST...")
net = cv2.dnn.readNet(args["east"])

# --- 4. EJECUTAR DETECCIÓN DE TEXTO (EAST) ---
# Nombres de las capas de salida que nos interesan
layerNames = [
    "feature_fusion/Conv_7/Sigmoid",
    "feature_fusion/concat_3"]

# Preparamos la imagen (blob) y la pasamos por el modelo
blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
    (123.68, 116.78, 103.94), swapRB=True, crop=False)
net.setInput(blob)
(scores, geometry) = net.forward(layerNames)

# Decodificamos las predicciones
(rects, confidences) = decode_predictions(scores, geometry)

# Aplicamos Non-Maximum Suppression (NMS) para eliminar cajas duplicadas
boxes = non_max_suppression(np.array(rects), probs=confidences)

# --- 5. BUCLE PRINCIPAL: OCR (Tesseract) + Regex ---
results = []
print("[INFO] Analizando regiones de texto...")

for (startX, startY, endX, endY) in boxes:
    # Escalamos las coordenadas de vuelta al tamaño original
    startX = int(startX * rW)
    startY = int(startY * rH)
    endX = int(endX * rW)
    endY = int(endY * rH)

    # Añadimos un pequeño "padding" a la caja
    # Esto ayuda a Tesseract a leer mejor los bordes
    padding = 0.05
    dX = int((endX - startX) * padding)
    dY = int((endY - startY) * padding)
    startX = max(0, startX - dX)
    startY = max(0, startY - dY)
    endX = min(origW, endX + (dX * 2))
    endY = min(origH, endY + (dY * 2))

    # Extraemos la Región de Interés (ROI)
    roi = orig[startY:endY, startX:endX]

    # --- Pre-procesamiento para Tesseract ---
    # Convertir a escala de grises
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Aplicar umbralización (thresholding) para binarizar la imagen
    # THRESH_OTSU encuentra el mejor umbral automáticamente
    thresh = cv2.threshold(gray, 0, 255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    
    # Opcional: Aplicar un desenfoque para eliminar ruido
    # thresh = cv2.medianBlur(thresh, 3)

    # --- Ejecutar Tesseract (OCR) ---
    # --psm 7: Trata la imagen como una sola línea de texto.
    config = "--psm 7"
    text = pytesseract.image_to_string(thresh, config=config, lang='eng') # Puedes añadir 'spa' si tienes fechas en español

    # --- Ejecutar Regex ---
    found_dates = find_dates_in_text(text)
    
    # Si encontramos fechas, las guardamos
    if found_dates:
        results.append(((startX, startY, endX, endY), text, found_dates))

# --- 6. MOSTRAR RESULTADOS ---
print("\n--- FECHAS ENCONTRADAS ---")
if not results:
    print("[INFO] No se encontraron fechas.")

for ((startX, startY, endX, endY), text, dates) in results:
    # Imprimimos el texto crudo y las fechas extraídas
    print(f"Texto Crudo: {text.strip()}")
    print(f"Fechas Regex: {', '.join(dates)}\n")

    # Dibujamos la caja en la imagen original
    cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
    
    # Ponemos la fecha encontrada sobre la caja
    y = startY - 10 if startY - 10 > 10 else startY + 10
    cv2.putText(orig, ", ".join(dates), (startX, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

# Mostramos la imagen final
cv2.imshow("Deteccion de Fechas", orig)
cv2.waitKey(0)
cv2.destroyAllWindows()