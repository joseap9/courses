import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json

# --- Configuración Tesseract ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# --- Archivo de entrada (PDF o imagen) ---
file_path = "formulario.pdf"

# --- Configuración OCR base ---
OCR_BASE = r'--oem 3 -l spa'  # psm se define en los intentos

# --- Debug: tamaño máx de ventana SOLO para mostrar (no afecta procesamiento) ---
SHOW_MAX_W = 1400
SHOW_MAX_H = 900

def show_resized(title, img, max_w=SHOW_MAX_W, max_h=SHOW_MAX_H):
    """Muestra 'img' en una ventana escalada para que quepa en pantalla."""
    h, w = img.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        img_disp = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        img_disp = img
    cv2.imshow(title, img_disp)

def dpi_for_page(page, target_width_px=1800, min_dpi=150, max_dpi=300):
    """DPI por página para que el ancho renderizado sea ~target_width_px, con límites."""
    w_pt = page.rect.width
    w_in = w_pt / 72.0 if w_pt else 0.0
    if w_in <= 0:
        return 200
    dpi = int(np.clip(target_width_px / w_in, min_dpi, max_dpi))
    return dpi

def quitar_azul_de_imagen(img_bgr, mask_blue):
    """Blanquea píxeles azules para no confundir al OCR."""
    cleaned = img_bgr.copy()
    cleaned[mask_blue > 0] = (255, 255, 255)
    return cleaned

def extraer_bboxes_desde_mask(mask_blue):
    """
    Encuentra TODAS las cajas azules a partir de la máscara.
    Sin filtros agresivos: solo descarta ruido minúsculo.
    Devuelve lista de bboxes (x,y,w,h) ordenadas por fila/columna.
    """
    contours, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bboxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= 100:  # descarta solo ruido muy pequeño
            bboxes.append((x, y, w, h))
    # Orden estable por fila/columna
    bboxes.sort(key=lambda b: (b[1], b[0]))
    return bboxes

def ocr_roi(gray, psm_sequence=(7, 6, 11)):
    """
    Intenta OCR con varios PSM y preprocesamientos.
    Devuelve el mejor texto encontrado.
    """
    # 1) Grayscale “limpio”
    for psm in psm_sequence:
        cfg = f"{OCR_BASE} --psm {psm}"
        txt = pytesseract.image_to_string(gray, config=cfg).strip()
        if txt:
            return txt

    # 2) Escalado x2 y contraste (CLAHE)
    big = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(big)
    for psm in psm_sequence:
        cfg = f"{OCR_BASE} --psm {psm}"
        txt = pytesseract.image_to_string(clahe, config=cfg).strip()
        if txt:
            return txt

    # 3) Binarización adaptativa
    bin_adapt = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 31, 10)
    for psm in psm_sequence:
        cfg = f"{OCR_BASE} --psm {psm}"
        txt = pytesseract.image_to_string(bin_adapt, config=cfg).strip()
        if txt:
            return txt

    return ""  # nada legible

def procesar_imagen(image_bgr, titulo="Página", debug=True):
    """
    - Muestra imagen original escalada (debug).
    - Crea máscara azul.
    - Toma TODAS las cajas de la máscara (sin excluir por tamaño relativo).
    - Recorta interior con margen porcentual (independiente de la escala).
    - Quita azul y hace OCR (con intentos).
    - Dibuja enumeración en todas las cajas.
    """
    if debug:
        show_resized(f"{titulo} - Antes de máscara", image_bgr)

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180], dtype=np.uint8)
    upper_blue = np.array([130, 255, 255], dtype=np.uint8)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # Limpieza leve (sin parámetros críticos)
    kernel = np.ones((3, 3), np.uint8)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel, iterations=1)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel, iterations=1)

    if debug:
        show_resized(f"{titulo} - Máscara Azul", mask_blue)

    # Imagen sin azul (para evitar que los bordes contaminen OCR)
    img_clean = quitar_azul_de_imagen(image_bgr, mask_blue)

    # TODAS las cajas (sin filtros de porcentaje/percentiles)
    bboxes = extraer_bboxes_desde_mask(mask_blue)

    valores = []
    vis = image_bgr.copy()

    for idx, (x, y, w, h) in enumerate(bboxes, start=1):
        # Margen interior porcentual (escala-agnóstico): 6% del menor lado
        m = max(1, int(0.06 * min(w, h)))
        x_in = x + m
        y_in = y + m
        w_in = max(1, w - 2 * m)
        h_in = max(1, h - 2 * m)

        roi = img_clean[y_in:y_in+h_in, x_in:x_in+w_in]
        if roi.size == 0:
            continue

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # OCR con intentos (psm 7→6→11 y distintos preprocesados)
        txt = ocr_roi(gray)
        if txt:
            valores.append(txt)

        # Dibujo y enumeración SIEMPRE, para ver que se procesa todo
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
        y_text = max(15, y - 5)
        cv2.putText(vis, str(idx), (x, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    if debug:
        show_resized(f"{titulo} - Cajas Detectadas y Numeradas", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return valores

# -------------------- Flujo principal --------------------
valores_totales = []

if file_path.lower().endswith(".pdf"):
    doc = fitz.open(file_path)
    for i, page in enumerate(doc, start=1):
        dpi = dpi_for_page(page)  # DPI adaptativo
        pix = page.get_pixmap(dpi=dpi, alpha=False)  # RGB
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        valores_totales.extend(procesar_imagen(img_bgr, titulo=f"Página {i}", debug=True))
else:
    img_bgr = cv2.imread(file_path)
    if img_bgr is None:
        raise RuntimeError("No se pudo cargar la imagen.")
    valores_totales = procesar_imagen(img_bgr, titulo="Imagen", debug=True)

print(json.dumps(valores_totales, ensure_ascii=False, indent=2))
