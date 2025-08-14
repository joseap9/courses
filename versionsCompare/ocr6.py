import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json
import os

# -------- Configuración --------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
file_path = "formulario.pdf"   # PDF o imagen
max_width = 1500               # mismo valor que tu pipeline original
ocr_config = r'--oem 3 --psm 6 -l spa'
EXPECTED_FIRST_PAGE_BOXES = 30 # garantía en la primera página

# Solo para mostrar en pantalla sin que se "corten" las ventanas (no afecta al OCR)
SHOW_MAX_W, SHOW_MAX_H = 1400, 900

def show_resized(title, img, max_w=SHOW_MAX_W, max_h=SHOW_MAX_H):
    h, w = img.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    cv2.imshow(title, img)

def dpi_for_target_width(page, target_width_px=1500, min_dpi=120, max_dpi=300):
    """
    Calcula un DPI para que el ANCHO rasterizado de la página quede ~target_width_px.
    Así el PDF 'calza' con tu redimensión de imágenes y no cambia el pipeline.
    """
    w_pt = page.rect.width  # puntos (1/72")
    w_in = w_pt / 72.0 if w_pt else 0.0
    if w_in <= 0:
        return 200
    dpi = int(np.clip(target_width_px / w_in, min_dpi, max_dpi))
    return dpi

def render_pdf_page_to_bgr(page, target_width_px=1500):
    dpi = dpi_for_target_width(page, target_width_px=target_width_px)
    pix = page.get_pixmap(dpi=dpi, alpha=False)   # RGB sin alfa
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img_bgr

def cargar_imagen_o_pdf(file_path):
    """
    Devuelve una lista de imágenes BGR.
    - Si es imagen: [imagen]
    - Si es PDF: [página1, página2, ...] rasterizadas a un ancho ≈ max_width
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        imgs = []
        doc = fitz.open(file_path)
        for page in doc:
            img_bgr = render_pdf_page_to_bgr(page, target_width_px=max_width)
            imgs.append(img_bgr)
        return imgs
    else:
        img = cv2.imread(file_path)
        if img is None:
            raise RuntimeError("No se pudo cargar la imagen.")
        return [img]

def filtrar_cajas_por_rango(contours, rango_w, rango_h, min_area=0):
    """Devuelve bboxes (x,y,w,h) que cumplan rangos de w, h y área mínima."""
    w_min, w_max = rango_w
    h_min, h_max = rango_h
    cajas = []
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if (w_min < w < w_max) and (h_min < h < h_max):
            cajas.append((x, y, w, h))
    return cajas

def ordenar_cajas_derecha_izquierda_arriba_abajo(cajas, img_h, row_tol_ratio=0.02, min_row_tol_px=6):
    """
    Ordena por filas (arriba→abajo) y dentro de cada fila de derecha→izquierda.
    Agrupa por centro Y con una tolerancia adaptativa.
    """
    if not cajas:
        return []

    # Orden preliminar por Y asc, luego X desc (para ayudar al agrupado)
    cajas = sorted(cajas, key=lambda b: (b[1] + b[3] / 2.0, - (b[0] + b[2] / 2.0)))

    # Tolerancia vertical p/ agrupar filas
    row_tol = max(int(img_h * row_tol_ratio), min_row_tol_px)

    filas = []
    for box in cajas:
        x, y, w, h = box
        cy = y + h / 2.0
        colocado = False
        for fila in filas:
            # usa el promedio de la fila para decidir pertenencia
            cys = [fy + fh / 2.0 for (_, fy, fw, fh) in fila]
            if abs(cy - (sum(cys) / len(cys))) <= row_tol:
                fila.append(box)
                colocado = True
                break
        if not colocado:
            filas.append([box])

    # Orden final: filas por Y asc y dentro de cada fila por X desc (derecha→izquierda)
    filas = sorted(filas, key=lambda fila: sum([fy + fh / 2.0 for (_, fy, fw, fh) in fila]) / len(fila))
    cajas_ordenadas = []
    for fila in filas:
        fila_ordenada = sorted(fila, key=lambda b: -(b[0] + b[2] / 2.0))  # X centro descendente
        cajas_ordenadas.extend(fila_ordenada)

    return cajas_ordenadas

def detectar_cajas_con_garantia_primera_pagina(mask, img_shape, expected=30):
    """
    Intenta obtener 'expected' cajas desde la máscara, probando rangos en cascada.
    Si hay más de expected, se recorta a las 30 primeras según el orden solicitado.
    Si hay menos, toma todas las candidatas posibles.
    """
    H, W = img_shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Secuencia de rangos (tu original primero)
    rangos = [
        ((40, 500), (10, 300), 80),    # original
        ((30, 600), (9, 350), 60),     # leve relajación
        ((20, 800), (8, 400), 40),     # relajado
        ((10, 1200), (5, 600), 20),    # muy relajado
    ]

    candidatas = []
    for (rw, rh, min_area) in rangos:
        cajas = filtrar_cajas_por_rango(contours, rw, rh, min_area=min_area)
        cajas = ordenar_cajas_derecha_izquierda_arriba_abajo(cajas, H)
        if len(cajas) >= expected:
            candidatas = cajas
            break
        # Mantén la mejor hasta ahora (más cercana a expected)
        if len(cajas) > len(candidatas):
            candidatas = cajas

    # Último recurso: si seguimos por debajo, acepta TODO lo razonable (área >= 10)
    if len(candidatas) < expected:
        cajas_all = filtrar_cajas_por_rango(contours, (1, W), (1, H), min_area=10)
        cajas_all = ordenar_cajas_derecha_izquierda_arriba_abajo(cajas_all, H)
        if len(cajas_all) > len(candidatas):
            candidatas = cajas_all

    # Deja exactamente 'expected' si hay de sobra
    if len(candidatas) > expected:
        candidatas = candidatas[:expected]

    return candidatas  # puede devolver < expected si realmente no hay suficientes cajas

def procesar_imagen_pipeline_antiguo(image_bgr, titulo="Página", force_30=False, expected=30):
    """
    Tu pipeline original; si force_30=True, aplica la garantía de 30 cajas (1ª página).
    """
    image = image_bgr.copy()
    original = image_bgr.copy()

    # Redimensionar si es necesario (igual que tu código)
    if image.shape[1] > max_width:
        scale_ratio = max_width / image.shape[1]
        image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)),
                           interpolation=cv2.INTER_AREA)
        original = cv2.resize(original, (int(original.shape[1] * scale_ratio), int(original.shape[0] * scale_ratio)),
                              interpolation=cv2.INTER_AREA)

    # HSV y máscara azul (idéntico)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Debug (escala solo para mostrar)
    show_resized(f"{titulo} - Máscara Azul (cajas detectables)", mask)

    # Contornos
    if force_30:
        cajas = detectar_cajas_con_garantia_primera_pagina(mask, image.shape, expected=expected)
    else:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cajas = filtrar_cajas_por_rango(contours, (40, 500), (10, 300), min_area=80)
        # Orden estándar: arriba→abajo y derecha→izquierda (según lo pediste)
        cajas = ordenar_cajas_derecha_izquierda_arriba_abajo(cajas, image.shape[0])

    # OCR
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    # Visual final con enumeración (idéntico, pero mostrado a escala)
    output_image = image.copy()
    for i, (x, y, w, h) in enumerate(cajas, start=1):
        cv2.rectangle(output_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(output_image, f"{i}", (x, max(12, y - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    show_resized(f"{titulo} - Cajas Detectadas y Numeradas", output_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return valores

# --------- Flujo principal ---------
valores_totales = []
imagenes = cargar_imagen_o_pdf(file_path)

if file_path.lower().endswith(".pdf"):
    for idx, img_bgr in enumerate(imagenes, start=1):
        # Primera página: forzar 30 cajas
        force = (idx == 1)
        valores_totales.extend(
            procesar_imagen_pipeline_antiguo(
                img_bgr, titulo=f"Página {idx}",
                force_30=force, expected=EXPECTED_FIRST_PAGE_BOXES
            )
        )
else:
    # Imagen suelta: no forzamos 30, mantenemos tu flujo original
    valores_totales = procesar_imagen_pipeline_antiguo(imagenes[0], titulo="Imagen", force_30=False)

# Salida
print(json.dumps(valores_totales, ensure_ascii=False))
