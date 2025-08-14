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

# ---- Parámetros ajustables ----
MAX_WIDTH = 1500            # reescala si es más grande
PDF_RENDER_DPI = 200        # 200 suele ser suficiente y evita imágenes gigantes
# filtros relativos (proporciones de ancho/alto de la imagen)
MIN_W_REL, MAX_W_REL = 0.02, 0.50  # entre 2% y 50% del ancho
MIN_H_REL, MAX_H_REL = 0.01, 0.30  # entre 1% y 30% del alto
MIN_AREA_REL = 0.0001              # área mínima relativa (0.01% del área total)

def procesar_imagen(image, show_debug=True, titulo_pagina="Página"):
    """
    Procesa una imagen (BGR) detectando cajas azules y haciendo OCR.
    show_debug: si True, muestra ventanas con:
      - imagen original (antes de máscara)
      - máscara azul
      - resultado con enumeración
    """
    # Copias
    original = image.copy()
    img_for_view = image.copy()

    # Vista previa: Página antes de máscara (opcional)
    if show_debug:
        cv2.imshow(f"{titulo_pagina} - Antes de máscara", img_for_view)

    # Redimensionar si es necesario (manteniendo relación)
    if image.shape[1] > MAX_WIDTH:
        scale_ratio = MAX_WIDTH / image.shape[1]
        new_w = int(image.shape[1] * scale_ratio)
        new_h = int(image.shape[0] * scale_ratio)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        original = cv2.resize(original, (new_w, new_h), interpolation=cv2.INTER_AREA)

    H, W = image.shape[:2]

    # Convertir a HSV y crear máscara azul
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180], dtype=np.uint8)
    upper_blue = np.array([130, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # (opcional) pequeña apertura/cierre para limpiar ruido
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    if show_debug:
        cv2.imshow(f"{titulo_pagina} - Máscara Azul", mask)

    # Contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filtros relativos
    min_w = int(W * MIN_W_REL)
    max_w = int(W * MAX_W_REL)
    min_h = int(H * MIN_H_REL)
    max_h = int(H * MAX_H_REL)
    min_area = int(W * H * MIN_AREA_REL)

    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if (min_w <= w <= max_w) and (min_h <= h <= max_h) and (area >= min_area):
            cajas.append((x, y, w, h))

    # Ordenar por filas y luego columnas
    cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

    # OCR
    valores = []
    output_image = image.copy()
    for i, (x, y, w, h) in enumerate(cajas, start=1):
        # ROI y OCR
        roi = original[y:y+h, x:x+w]
        if roi.size == 0:
            continue
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)
        # Enumeración visible
        cv2.rectangle(output_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        y_text = max(15, y - 5)  # evita números fuera de imagen
        cv2.putText(output_image, str(i), (x, y_text), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    if show_debug:
        cv2.imshow(f"{titulo_pagina} - Cajas Detectadas y Numeradas", output_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return valores

valores_totales = []

if file_path.lower().endswith('.pdf'):
    doc = fitz.open(file_path)
    for idx, page in enumerate(doc, start=1):
        # Render con DPI controlado (evita imágenes gigantes)
        pix = page.get_pixmap(dpi=PDF_RENDER_DPI, alpha=False)  # alpha=False -> 3 canales
        # pix.samples ya viene en RGB contiguo
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        # Convertir a BGR para OpenCV
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        valores = procesar_imagen(img_bgr, show_debug=True, titulo_pagina=f"Página {idx}")
        valores_totales.extend(valores)
else:
    image = cv2.imread(file_path)
    if image is None:
        raise RuntimeError("No se pudo cargar la imagen.")
    valores_totales = procesar_imagen(image, show_debug=True, titulo_pagina="Imagen")

print(json.dumps(valores_totales, ensure_ascii=False, indent=2))
