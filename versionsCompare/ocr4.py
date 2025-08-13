# coding: utf-8
import sys
import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
import tempfile
import os
import json

# Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Ruta de entrada desde PAD
input_path = sys.argv[1]
result = {
    "tipo": "",
    "formulario": {},
    "texto": "",
    "ocr": []
}

def procesar_ocr_desde_imagen(img_path):
    image = cv2.imread(img_path)
    original = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 40 < w < 500 and 10 < h < 300:
            cajas.append((x, y, w, h))
    cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

    ocr_config = r'--oem 3 --psm 6 -l spa'
    textos = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            textos.append(text)
    return textos

def es_imagen(ruta):
    return ruta.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.heic'))

try:
    if es_imagen(input_path):
        result["tipo"] = "imagen"
        result["ocr"] = procesar_ocr_desde_imagen(input_path)

    else:
        doc = fitz.open(input_path)

        # 1. Campos interactivos
        for page in doc:
            widgets = page.widgets()
            if widgets:
                for widget in widgets:
                    result["formulario"][widget.field_name] = widget.field_value

        # 2. Texto plano
        texto = ""
        for page in doc:
            texto += page.get_text().strip() + "\n"
        result["texto"] = texto.strip()

        # 3. OCR si tiene 3 o más páginas
        if len(doc) >= 3:
            for i in range(len(doc)):
                pix = doc[i].get_pixmap(dpi=300)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    pix.save(tmp_img.name)
                    textos = procesar_ocr_desde_imagen(tmp_img.name)
                    if textos:
                        result["ocr"].append({
                            "pagina": i+1,
                            "valores": textos
                        })
                    os.unlink(tmp_img.name)

        if result["formulario"]:
            result["tipo"] = "formulario"
        elif result["texto"]:
            result["tipo"] = "texto"
        elif result["ocr"]:
            result["tipo"] = "ocr"
        else:
            result["tipo"] = "vacio"

        doc.close()

except Exception as e:
    result = {
        "tipo": "error",
        "mensaje": str(e)
    }

# Salida final para PAD
print(json.dumps(result, ensure_ascii=False))
