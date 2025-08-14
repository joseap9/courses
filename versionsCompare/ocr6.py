import cv2
import pytesseract
import numpy as np
import json
import os
from pdf2image import convert_from_path
from PIL import Image

# Ruta a Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Ruta del archivo (puede ser imagen o PDF)
file_path = "documento.pdf"  # Cambia según el archivo a procesar

# Función para procesar una imagen
def procesar_imagen(image):
    original = image.copy()

    # Redimensionar si es necesario
    max_width = 1500
    if image.shape[1] > max_width:
        scale_ratio = max_width / image.shape[1]
        image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))
        original = cv2.resize(original, (int(original.shape[1] * scale_ratio), int(original.shape[0] * scale_ratio)))

    # Convertir a HSV y crear máscara azul
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Detectar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 40 < w < 500 and 10 < h < 300:
            cajas.append((x, y, w, h))

    # Ordenar cajas por posición
    cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

    # OCR
    ocr_config = r'--oem 3 --psm 6 -l spa'
    valores = []

    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    return valores

# Lista final de todos los textos
todos_los_valores = []

# Verificar si es PDF o imagen
if file_path.lower().endswith(".pdf"):
    paginas = convert_from_path(file_path, dpi=300)
    for i, pagina in enumerate(paginas):
        image = np.array(pagina.convert("RGB"))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        valores = procesar_imagen(image)
        todos_los_valores.extend(valores)
else:
    image = cv2.imread(file_path)
    if image is None:
        raise Exception("No se pudo cargar la imagen")
    valores = procesar_imagen(image)
    todos_los_valores.extend(valores)

# Imprimir resultados
print(json.dumps(todos_los_valores, ensure_ascii=False, indent=2))
