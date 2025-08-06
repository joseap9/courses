import cv2
import pytesseract
import re
import json

# Ruta de Tesseract en tu equipo
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cargar imagen
image_path = "5907d5b7-9c7e-4311-a32b-5fa35016870a.png"
image = cv2.imread(image_path)

# Redimensionar imagen si es muy grande o muy pequeña
max_width = 1500
min_width = 1000

if image.shape[1] > max_width:
    scale_ratio = max_width / image.shape[1]
    image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))

elif image.shape[1] < min_width:
    scale_ratio = min_width / image.shape[1]
    image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))

# Preprocesamiento
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.bilateralFilter(gray, 11, 17, 17)
gray = cv2.equalizeHist(gray)
thresh = cv2.adaptiveThreshold(gray, 255,
                               cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 15, 10)

# OCR en español
custom_config = r'--oem 3 --psm 6 -l spa'
ocr_result = pytesseract.image_to_string(thresh, config=custom_config)

# Mostrar texto crudo (opcional)
print("==== TEXTO DETECTADO ====")
print(ocr_result)
print("==========================")

# Limpieza del texto
ocr_result = ocr_result.replace('\n\n', '\n').strip()

# Diccionario de campos con regex para detectar valores
campos = {
    "rut_identificacion": r"(?i)RUT/N[°ºo] identificación[:\s]*([a-zA-Z0-9\-.]+)",
    "razon_social": r"(?i)Raz[oó]n social[:\s]*([a-zA-Z0-9\s]+)",
    "domicilio": r"(?i)Domicilio[:\s]*([a-zA-Z0-9\s]+)",
    "ciudad": r"(?i)Ciudad[:\s]*([a-zA-Z0-9\s]+)",
    "lugar_constitucion": r"(?i)Lugar de constituci[oó]n[:\s]*([a-zA-Z0-9\s]+)",
    "telefono": r"(?i)Tel[eé]fono[:\s]*([\d\s]+)",
    "domicilio_tributario": r"(?i)Domicilio tributario[:\s]*([a-zA-Z0-9\s]+)",
    "rut_rep_legal": r"(?i)RUT/N[°ºo] identificación rep\.? legal[:\s]*([a-zA-Z0-9\-\.]+)",
    "nombre_rep_legal": r"(?i)Nombre representante legal[:\s]*([a-zA-Z\s]+)"
}

# Extraer campos
datos_extraidos = {}
for campo, patron in campos.items():
    match = re.search(patron, ocr_result)
    datos_extraidos[campo] = match.group(1).strip() if match else None

# Mostrar resultado estructurado
print("\n==== CAMPOS EXTRAÍDOS ====")
print(json.dumps(datos_extraidos, indent=4, ensure_ascii=False))
