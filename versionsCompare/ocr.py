import cv2
import pytesseract
from PIL import Image
import re

# Configurar ruta de Tesseract si no está en PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Ruta a la imagen escaneada
image_path = "b0df7717-3255-4af6-a471-f727695a6e7a.jpeg"

# 1. Cargar imagen
image = cv2.imread(image_path)

# 2. Preprocesamiento de la imagen
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.medianBlur(gray, 3)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# 3. OCR con Tesseract
custom_config = r'--oem 3 --psm 6'
text = pytesseract.image_to_string(thresh, config=custom_config)

# ✅ Ver texto completo sin limpiar
print("Texto extraído sin procesar:")
print("="*40)
print(text)
print("="*40)

# 4. Limpieza básica del texto
lines = [line.strip() for line in text.split('\n') if line.strip()]

# ... (resto del código sigue igual)
