import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json
import os

# -------- Configuración --------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
file_path = "formulario.pdf"   # PDF o imagen
max_width = 1500               # igual que tu pipeline original
ocr_config = r'--oem 3 --psm 6 -l spa'

# Si quieres forzar 30 cajas en la primera página, deja 30. Para desactivar, usa None.
EXPECTED_FIRST_PAGE_BOXES = 30

# Ventanas de depuración escaladas (no afecta al OCR)
SHOW_MAX_W, SHOW_MAX_H = 1400, 900

def show_resized(title, img, max_w=SHOW_MAX_W, max_h=SHOW_MAX_H):
    h, w = img.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    cv2.imshow(title, img)

def dpi_for_target_width(page, target_width_px=1500, min_dpi=120, max_dpi=300):
    """DPI para que el ancho rasterizado quede ~target_width_px (calza con max_width)."""
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
    """Devuelve lista de imágenes BGR (una por página si es PDF)."""
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

def ordenar_cajas_derecha_izquierda_arriba_abajo(cajas, img_h, row_tol_ratio=0.02, min_row_tol_px=6):
    """
    Ordena por filas (arriba→abajo) y dentro de cada fila de derecha→izquierda.
    Agrupa filas por centro-Y con tolerancia adaptativa.
    """
    if not cajas:
        return []

    # Orden preliminar por Y (centro) asc y X (centro) desc
    cajas = sorted(cajas, key=lambda b: (b[1] + b[3] / 2.0, - (b[0] + b[2] / 2.0)))

    row_tol = max(int(img_h * row_tol_ratio), min_row_tol_px)
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

    # Filas por Y asc; dentro de cada fila X desc (derecha→izquierda)
    filas = sorted(filas, key=lambda fila: sum([fy + fh / 2.0 for (_, fy, fw, fh) in fila]) / len(fila))
    cajas_ordenadas = []
    for fila in filas:
        fila_ordenada = sorted(fila, key=lambda b: -(b[0] + b[2] / 2.0))
        cajas_ordenadas.extend(fila_ordenada)

    return cajas_ordenadas

def filtrar_cajas_por_percentil(contours, min_area=80, p_low=10, p_high=95):
    """
    Filtro ADAPTATIVO: calcula percentiles de w y h y acepta cajas dentro de [p_low, p_high].
    """
    ws, hs, bboxes = [], [], []
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        ws.append(w); hs.append(h); bboxes.append((x, y, w, h))

    if not bboxes:
        return []

    w_low, w_high = np.percentile(ws, p_low), np.percentile(ws, p_high)
    h_low, h_high = np.percentile(hs, p_low), np.percentile(hs, p_high)

    cajas = [(x, y, w, h) for (x, y, w, h) in bboxes
             if (w_low <= w <= w_high) and (h_low <= h <= h_high)]
    return cajas

def detectar_cajas_adaptativo(mask, img_shape, expected=None):
    """
    Detecta cajas con filtro por percentiles y (opcional) intenta alcanzar 'expected'
    relajando percentiles si es necesario. Orden final: arriba→abajo, derecha→izquierda.
    """
    H, W = img_shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Secuencia de parámetros (cada paso más permisivo)
    params_seq = [
        # (p_low, p_high, min_area)
        (10, 95, 80),   # base
        (5, 97, 60),    # más permisivo
        (3, 98, 40),    # aún más
        (1, 99, 20),    # casi todo
    ]

    best = []
    for p_low, p_high, min_area in params_seq:
        cajas = filtrar_cajas_por_percentil(contours, min_area=min_area, p_low=p_low, p_high=p_high)
        cajas = ordenar_cajas_derecha_izquierda_arriba_abajo(cajas, H)
        if expected is not None and len(cajas) >= expected:
            return cajas[:expected]
        if len(cajas) > len(best):
            best = cajas

    # Último recurso si no se alcanzó expected: acepta todo con área mínima pequeña
    if expected is not None and len(best) < expected:
        rough = []
        for cnt in contours:
            if cv2.contourArea(cnt) < 10:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            rough.append((x, y, w, h))
        rough = ordenar_cajas_derecha_izquierda_arriba_abajo(rough, H)
        if len(rough) > len(best):
            best = rough

    # Si hay expected y sobran, corta; si faltan, devuelve lo que hay
    if expected is not None and len(best) > expected:
        best = best[:expected]

    return best

def procesar_imagen_pipeline(image_bgr, titulo="Página", expected=None):
    """
    Tu pipeline original con filtro ADAPTATIVO:
    - Redimensionar si ancho > max_width
    - HSV -> máscara azul
    - Cajas por percentiles (y, si expected, relajación progresiva para alcanzarlo)
    - OCR psm=6 sobre cada caja
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

    # HSV y máscara azul (tus mismos umbrales)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Debug
    show_resized(f"{titulo} - Máscara Azul (cajas detectables)", mask)

    # Cajas ADAPTATIVAS (si expected no es None, intentará alcanzar ese número)
    cajas = detectar_cajas_adaptativo(mask, image.shape, expected=expected)

    # OCR (tu mismo flujo)
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    # Visual final con enumeración (igual, solo que mostramos escalado)
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
        # En la primera página intentamos llegar a EXACTAMENTE 30 (si así lo quieres)
        expected = EXPECTED_FIRST_PAGE_BOXES if idx == 1 else None
        valores_totales.extend(
            procesar_imagen_pipeline(img_bgr, titulo=f"Página {idx}", expected=expected)
        )
else:
    valores_totales = procesar_imagen_pipeline(imagenes[0], titulo="Imagen", expected=None)

print(json.dumps(valores_totales, ensure_ascii=False))
