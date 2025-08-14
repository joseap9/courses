# coding: utf-8
import sys
import os
import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
import tempfile
import json

# Ruta a Tesseract (ajústala si es necesario)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def procesar_ocr_desde_imagen(img_path):
    image = cv2.imread(img_path)
    if image is None:
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 40 < w < 800 and 10 < h < 300:
            cajas.append((x, y, w, h))
    cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

    textos = []
    for x, y, w, h in cajas:
        roi = gray[y:y+h, x:x+w]
        text = pytesseract.image_to_string(roi, config='--oem 3 --psm 6 -l spa').strip()
        if text:
            textos.append(text)

    return textos

def procesar_pdf_con_ocr(pdf_path):
    resultados = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                pix.save(tmp_img.name)
                textos = procesar_ocr_desde_imagen(tmp_img.name)
                resultados.extend(textos)
            os.remove(tmp_img.name)
    return resultados

def main():
    file_path = sys.argv[1]

    if file_path.lower().endswith(".pdf"):
        resultado = procesar_pdf_con_ocr(file_path)
    else:
        resultado = procesar_ocr_desde_imagen(file_path)

    print(json.dumps(resultado, ensure_ascii=False))

if __name__ == "__main__":
    main()
