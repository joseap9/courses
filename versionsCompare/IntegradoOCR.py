# -*- coding: utf-8 -*-
import sys
import fitz  # PyMuPDF para PDF -> imagen
import cv2
import pytesseract
import numpy as np
import json
import os
import re

# -------------------- Argumentos desde PAD --------------------
if len(sys.argv) < 3:
    print(json.dumps({"error": "Faltan argumentos: archivo y ruta_tesseract"}, ensure_ascii=False))
    sys.exit(1)

file_path = sys.argv[1]        # PDF o imagen
tesseract_path = sys.argv[2]   # Ruta al ejecutable de Tesseract

# -------------------- Configuración OCR --------------------
pytesseract.pytesseract.tesseract_cmd = tesseract_path
max_width = 1500
ocr_config = r'--oem 3 --psm 6 -l spa'
ORDER_RIGHT_TO_LEFT = True

# -------------------- Funciones auxiliares --------------------
def es_pdf_texto(pdf_path, umbral=500):
    """Retorna True si el PDF contiene más texto que el umbral indicado."""
    doc = fitz.open(pdf_path)
    total_chars = 0
    for page in doc:
        total_chars += len(page.get_text())
    doc.close()
    return total_chars >= umbral


def extraer_campos_formulario(pdf_path):
    """Extrae campos de formulario editable."""
    doc = fitz.open(pdf_path)
    form_fields = {}
    for page in doc:
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                form_fields[widget.field_name] = widget.field_value
    doc.close()
    return form_fields

def filtrar_campos_interes(texto):
    """Devuelve solo campos de interés del texto plano."""
    campos_interes = ["Nombre", "Apellido", "RUT", "Dirección"]  # <-- Ajusta a tus necesidades
    resultado = {}
    for campo in campos_interes:
        patron = rf"{campo}\s*[:\-]?\s*(.*)"
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            resultado[campo] = m.group(1).strip()
    return resultado

def dpi_for_target_width(page, target_width_px=1500, min_dpi=120, max_dpi=300):
    w_pt = page.rect.width
    w_in = w_pt / 72.0 if w_pt else 0.0
    if w_in <= 0:
        return 200
    return int(np.clip(target_width_px / w_in, min_dpi, max_dpi))

def render_pdf_page_to_bgr(page, target_width_px=1500):
    dpi = dpi_for_target_width(page, target_width_px=target_width_px)
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

def cargar_imagen_o_pdf(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        return [render_pdf_page_to_bgr(p, target_width_px=max_width) for p in doc]
    else:
        im = cv2.imread(path)
        if im is None:
            raise RuntimeError("No se pudo cargar la imagen.")
        return [im]

def ordenar_por_filas_y_columnas(cajas, img_h, row_tol_ratio=0.02, right_to_left=True):
    if not cajas:
        return []
    cajas = sorted(
        cajas,
        key=lambda b: (b[1] + b[3] / 2.0, -(b[0] + b[2] / 2.0) if right_to_left else (b[0] + b[2] / 2.0))
    )
    row_tol = max(int(img_h * row_tol_ratio), 6)
    filas = []
    for box in cajas:
        x, y, w, h = box
        cy = y + h / 2.0
        placed = False
        for fila in filas:
            cys = [fy + fh / 2.0 for (_, fy, fw, fh) in fila]
            if abs(cy - (sum(cys) / len(cys))) <= row_tol:
                fila.append(box)
                placed = True
                break
        if not placed:
            filas.append([box])
    filas = sorted(filas, key=lambda fila: sum([fy + fh / 2.0 for (_, fy, fw, fh) in fila]) / len(fila))
    out = []
    for fila in filas:
        fila_ordenada = sorted(
            fila,
            key=lambda b: -(b[0] + b[2] / 2.0) if right_to_left else (b[0] + b[2] / 2.0)
        )
        out.extend(fila_ordenada)
    return out

def procesar_imagen_rectangulos_relativos(image_bgr):
    image = image_bgr.copy()
    original = image_bgr.copy()
    if image.shape[1] > max_width:
        scale_ratio = max_width / image.shape[1]
        image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)),
                           interpolation=cv2.INTER_AREA)
        original = cv2.resize(original, (int(original.shape[1] * scale_ratio), int(original.shape[0] * scale_ratio)),
                              interpolation=cv2.INTER_AREA)
    H, W = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    W_MIN = int(W * 0.03)
    W_MAX = int(W * 0.95)
    H_MIN = int(H * 0.006)
    H_MAX = int(H * 0.10)
    AREA_MIN = int(W * H * 0.0002)
    ASPECT_MIN = 2.2

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < AREA_MIN:
            continue
        if not (W_MIN <= w <= W_MAX and H_MIN <= h <= H_MAX):
            continue
        aspect = (w / float(h)) if h > 0 else 999.0
        if aspect < ASPECT_MIN:
            continue
        cajas.append((x, y, w, h))

    cajas = ordenar_por_filas_y_columnas(cajas, H, right_to_left=ORDER_RIGHT_TO_LEFT)
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)
    return valores

# -------------------- Lógica principal --------------------
resultado = {}

if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".heic")):
    resultado["tipo"] = "imagen"
    resultado["valores"] = procesar_imagen_rectangulos_relativos(cargar_imagen_o_pdf(file_path)[0])

elif file_path.lower().endswith(".pdf"):
    if es_pdf_texto(file_path):
        campos = extraer_campos_formulario(file_path)
        if campos:
            resultado["tipo"] = "pdf_formulario"
            resultado["valores"] = campos
        else:
            doc = fitz.open(file_path)
            texto = "\n".join([page.get_text() for page in doc])
            doc.close()
            resultado["tipo"] = "pdf_texto"
            resultado["valores"] = filtrar_campos_interes(texto)
    else:
        resultado["tipo"] = "pdf_escaneado"
        imagenes = cargar_imagen_o_pdf(file_path)
        vals = []
        for img in imagenes:
            vals.extend(procesar_imagen_rectangulos_relativos(img))
        resultado["valores"] = vals

# -------------------- Salida JSON para PAD --------------------
print(json.dumps(resultado, ensure_ascii=False))
