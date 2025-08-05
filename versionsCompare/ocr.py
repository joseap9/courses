import cv2
import pytesseract
from PIL import Image
import re

# Ruta a la imagen escaneada
image_path = "b0df7717-3255-4af6-a471-f727695a6e7a.jpeg"

# 1. Cargar imagen
image = cv2.imread(image_path)

# 2. Preprocesamiento de la imagen
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.medianBlur(gray, 3)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# 3. OCR con Tesseract
custom_config = r'--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6 (bloques de texto)
text = pytesseract.image_to_string(thresh, config=custom_config)

# 4. Limpieza básica del texto
lines = [line.strip() for line in text.split('\n') if line.strip()]

# 5. Extraer información relevante
form_data = []

# Diccionario de campos esperados
campos_interes = [
    "RUT/N° identificación", "Razón social", "Domicilio", "Ciudad", "Lugar/País de Constitución",
    "Domicilio tributario", "Teléfono", "Nombre representante legal 1", "Nombre representante legal 2",
    "Uso del Vehículo", "Tipo de entidad"
]

for campo in campos_interes:
    for line in lines:
        if campo.lower() in line.lower():
            form_data.append((campo, line.replace(campo, "").strip()))
            break

# 6. Agregar detección de tabla (gerencia)
for i, line in enumerate(lines):
    if "Cargo" in line and "Nombre" in line:
        form_data.append(("Gerencia", lines[i+1:i+4]))  # 3 filas por ejemplo

# 7. Mostrar resultado
for k, v in form_data:
    print(f"{k}: {v}")
