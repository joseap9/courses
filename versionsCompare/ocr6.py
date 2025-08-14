import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json

# --- Configuración Tesseract ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# --- Archivo de entrada (PDF o imagen) ---
file_path = "formulario.pdf"

# --- Configuración OCR ---
ocr_config = r'--oem 3 --psm 6 -l spa'

# --- Debug: tamaño máximo de ventana solo para mostrar (no afecta al procesamiento) ---
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
    """
    Calcula un DPI por página para que el ancho renderizado sea ~target_width_px,
    manteniendo límites razonables.
    """
    w_pt = page.rect.width      # ancho en puntos (1 punto = 1/72")
    w_in = w_pt / 72.0
    if w_in <= 0:
        return 200
    dpi = int(np.clip(target_width_px / w_in, min_dpi, max_dpi))
    return dpi

def quitar_azul_de_imagen(img_bgr, mask_blue):
    """Blanquea píxeles azules para no confundir al OCR."""
    cleaned = img_bgr.copy()
    cleaned[mask_blue > 0] = (255, 255, 255)
    return cleaned

def extraer_rectangulos_desde_mask(mask_blue):
    """
    Encuentra rectángulos (4 vértices convexos) de la máscara azul.
    Filtrado adaptativo por percentiles de área (evita tamaños fijos).
    Devuelve lista de tuplas: (polígono_4p, bbox(x,y,w,h)).
    """
    contours, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []

    areas = np.array([cv2.contourArea(c) for c in contours], dtype=np.float32)
    if len(areas) > 4:
        p10 = np.percentile(areas, 10)  # quita ruido pequeño
        p99 = np.percentile(areas, 99)  # quita outliers enormes
    else:
        p10, p99 = 0.0, float('inf')

    rects = []
    for c, a in zip(contours, areas):
        if a < max(1.0, p10) or a > p99:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            x, y, w, h = cv2.boundingRect(approx)
            rects.append((approx.reshape(-1, 2), (x, y, w, h)))

    # Orden estable por fila/columna
    rects.sort(key=lambda r: (r[1][1], r[1][0]))
    return rects

def recorte_interior_por_grosor(mask_blue, bbox):
    """
    Estima el grosor típico del borde azul en la bbox y recorta hacia adentro ese grosor.
    Usa distanceTransform para no depender de márgenes fijos.
    """
    x, y, w, h = bbox
    roi_mask = mask_blue[y:y+h, x:x+w]
    if roi_mask.size == 0:
        return x, y, w, h

    dist = cv2.distanceTransform(roi_mask, cv2.DIST_L2, 3)
    vals = dist[roi_mask > 0]
    if vals.size == 0:
        return x, y, w, h

    t = int(np.median(vals))
    t = max(1, t)

    x_in = x + t
    y_in = y + t
    w_in = max(1, w - 2 * t)
    h_in = max(1, h - 2 * t)
    return x_in, y_in, w_in, h_in

def procesar_imagen(image_bgr, titulo="Página", debug=True):
    """
    - Muestra imagen original (escalada solo para visualizar).
    - Crea máscara azul.
    - Detecta rectángulos adaptativamente.
    - Quita azul dentro de cada ROI y corre OCR.
    - Dibuja enumeración para ver qué se leyó.
    """
    if debug:
        show_resized(f"{titulo} - Antes de máscara", image_bgr)

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180], dtype=np.uint8)
    upper_blue = np.array([130, 255, 255], dtype=np.uint8)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # Limpieza suave de la máscara
    kernel = np.ones((3, 3), np.uint8)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel, iterations=1)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel, iterations=1)

    if debug:
        show_resized(f"{titulo} - Máscara Azul", mask_blue)

    # Imagen limpia (sin azul) para OCR
    img_clean = quitar_azul_de_imagen(image_bgr, mask_blue)

    rects = extraer_rectangulos_desde_mask(mask_blue)

    valores = []
    vis = image_bgr.copy()
    for idx, (poly, bbox) in enumerate(rects, start=1):
        x_in, y_in, w_in, h_in = recorte_interior_por_grosor(mask_blue, bbox)
        roi = img_clean[y_in:y_in+h_in, x_in:x_in+w_in]
        if roi.size == 0:
            continue

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        txt = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if txt:
            valores.append(txt)

        # Visualización (polígono y numeración)
        cv2.polylines(vis, [poly.astype(np.int32)], True, (0, 255, 0), 2)
        cv2.putText(vis, str(idx), (bbox[0], max(15, bbox[1]-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

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
        # DPI adaptativo para que el ancho renderizado sea consistente
        dpi = dpi_for_page(page)  # p.ej. ~1800 px de ancho
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
