import cv2
import pytesseract
import numpy as np

# Ruta de Tesseract si no está en el PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Leer la imagen
image_path = "81443c73-ed1c-4421-a4a3-13fe94fd848e.png"
image = cv2.imread(image_path)

# Preprocesamiento
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.bilateralFilter(gray, 11, 17, 17)
gray = cv2.equalizeHist(gray)  # mejora el contraste

# Umbral adaptativo para resaltar texto
thresh = cv2.adaptiveThreshold(gray, 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 15, 10)

# Configuración para español y formularios
custom_config = r'--oem 3 --psm 6 -l spa'

# OCR
text = pytesseract.image_to_string(thresh, config=custom_config)

# Mostrar resultado
print("TEXTO OCR DETECTADO:")
print("="*40)
print(text)
print("="*40)
