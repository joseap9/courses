import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json

# Ruta a Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Ruta del archivo (puede ser imagen o PDF)
file_path = "formulario.pdf"

# OCR config
ocr_config = r'--oem 3 --psm 6 -l spa'

# Procesar imagen (desde PDF o JPG)
def procesar_imagen(image):
    original = image.copy()

    # Redimensionar
    max_width = 1500
    if image.shape[1] > max_width:
        scale_ratio = max_width / image.shape[1]
        image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))
        original = cv2.resize(original, (int(original.shape[1] * scale_ratio), int(original.shape[0] * scale_ratio)))

    # Convertir a HSV y máscara azul
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 40 < w < 500 and 10 < h < 300:
            cajas.append((x, y, w, h))
    cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

    # OCR
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    return valores

# Leer PDF (si es PDF escaneado)
valores_totales = []
if file_path.lower().endswith('.pdf'):
    doc = fitz.open(file_path)
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        valores = procesar_imagen(img)
        valores_totales.extend(valores)
else:
    # Si es imagen directa
    image = cv2.imread(file_path)
    valores_totales = procesar_imagen(image)

# Mostrar resultados
print(json.dumps(valores_totales, ensure_ascii=False, indent=2))
