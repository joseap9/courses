import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json
import os

# -------- Configuración --------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
file_path = "formulario.pdf"         # PDF o imagen
max_width = 1500                      # como tu pipeline original
ocr_config = r'--oem 3 --psm 6 -l spa'
EXPECTED_FIRST_PAGE_BOXES = 30        # primera página: objetivo 30

# Solo para mostrar sin cortar (no afecta OCR)
SHOW_MAX_W, SHOW_MAX_H = 1400, 900
def show_resized(title, img, max_w=SHOW_MAX_W, max_h=SHOW_MAX_H):
    h, w = img.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    cv2.imshow(title, img)

# ---------- Carga PDF a “ancho ≈ max_width” ----------
def dpi_for_target_width(page, target_width_px=1500, min_dpi=120, max_dpi=300):
    w_pt = page.rect.width
    w_in = w_pt / 72.0 if w_pt else 0.0
    if w_in <= 0:
        return 200
    return int(np.clip(target_width_px / w_in, min_dpi, max_dpi))

def render_pdf_page_to_bgr(page, target_width_px=1500):
    dpi = dpi_for_target_width(page, target_width_px=target_width_px)
    pix = page.get_pixmap(dpi=dpi, alpha=False)   # RGB sin alfa
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

def cargar_imagen_o_pdf(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        doc = fitz.open(file_path)
        return [render_pdf_page_to_bgr(p, target_width_px=max_width) for p in doc]
    else:
        im = cv2.imread(file_path)
        if im is None:
            raise RuntimeError("No se pudo cargar la imagen.")
        return [im]

# ---------- Orden: arriba→abajo, dentro de fila derecha→izquierda ----------
def ordenar_cajas_derecha_izquierda_arriba_abajo(cajas, img_h, row_tol_ratio=0.02, min_row_tol_px=6):
    if not cajas:
        return []
    # orden preliminar por Ycentro asc, Xcentro desc
    cajas = sorted(cajas, key=lambda b: (b[1] + b[3]/2.0, - (b[0] + b[2]/2.0)))
    row_tol = max(int(img_h * row_tol_ratio), min_row_tol_px)
    filas = []
    for box in cajas:
        x, y, w, h = box
        cy = y + h/2.0
        placed = False
        for fila in filas:
            cys = [fy + fh/2.0 for (_, fy, fw, fh) in fila]
            if abs(cy - (sum(cys)/len(cys))) <= row_tol:
                fila.append(box); placed = True; break
        if not placed:
            filas.append([box])
    filas = sorted(filas, key=lambda fila: sum([fy + fh/2.0 for (_, fy, fw, fh) in fila]) / len(fila))
    out = []
    for fila in filas:
        out.extend(sorted(fila, key=lambda b: -(b[0] + b[2]/2.0)))
    return out

# ---------- Detectar RECTÁNGULOS LARGOS ----------
def detectar_rectangulos_largos(mask_blue, img_shape, expected=None):
    """
    Filtra únicamente rectángulos horizontales largos (ancho ≫ alto).
    - Umbrales RELATIVOS (al tamaño de página) para tirar ruido.
    - Requiere relación de aspecto mínima (w/h).
    - Tiers (estricto→relajado) para no perder “cajas largas”.
    """
    H, W = img_shape[:2]

    # Limpieza leve de máscara
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Tiers: (min_area_rel, min_w_rel, min_h_rel, min_aspect_ratio, extent_low, extent_high)
    # * min_aspect_ratio alto para “rectángulos largos”
    tiers = [
        (0.0002, 0.10, 0.006, 4.0, 0.01, 0.55),  # estricto
        (0.00015,0.08, 0.005, 3.5, 0.01, 0.60),  # medio
        (0.00010,0.06, 0.004, 3.0, 0.01, 0.65),  # relajado
        (0.00005,0.04, 0.003, 2.5, 0.005,0.70),  # muy relajado (último recurso)
    ]

    best = []
    for (area_rel, w_rel, h_rel, ar_min, ext_low, ext_high) in tiers:
        min_area = int(H * W * area_rel)
        min_w_px = max(3, int(W * w_rel))
        min_h_px = max(2, int(H * h_rel))
        seleccion = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if w < min_w_px or h < min_h_px:
                continue

            # Solo horizontales largos
            ar = w / float(h) if h > 0 else 999.0
            if ar < ar_min:
                continue

            # Aproximación poligonal para rectangularidad básica
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if not cv2.isContourConvex(approx):
                continue
            if len(approx) < 4 or len(approx) > 10:
                continue

            # Extent: área/área_bbox — bordes azules suelen dar extent bajo
            extent = area / float(w * h)
            if not (ext_low <= extent <= ext_high):
                continue

            seleccion.append((x, y, w, h))

        # Orden y decisión por tier
        seleccion = ordenar_cajas_derecha_izquierda_arriba_abajo(seleccion, H)
        if expected is not None and len(seleccion) >= expected:
            return seleccion[:expected]
        if len(seleccion) > len(best):
            best = seleccion

    # Si no se llegó a expected, devuelve lo mejor encontrado ordenado
    best = ordenar_cajas_derecha_izquierda_arriba_abajo(best, H)
    if expected is not None and len(best) > expected:
        best = best[:expected]
    return best

# ---------- Pipeline (idéntico excepto el detector) ----------
def procesar_imagen(image_bgr, titulo="Página", expected=None):
    image = image_bgr.copy()
    original = image_bgr.copy()

    # Redimensionar si es necesario (igual que tu código)
    if image.shape[1] > max_width:
        scale_ratio = max_width / image.shape[1]
        image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)),
                           interpolation=cv2.INTER_AREA)
        original = cv2.resize(original, (int(original.shape[1] * scale_ratio), int(original.shape[0] * scale_ratio)),
                              interpolation=cv2.INTER_AREA)

    # Máscara azul (idéntico umbral)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Debug
    show_resized(f"{titulo} - Máscara Azul", mask)

    # >>> Rectángulos largos (en lugar de “cajas” genéricas)
    cajas = detectar_rectangulos_largos(mask, image.shape, expected=expected)

    # OCR (igual que antes)
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    # Visual (enumeración), mostrado a escala
    out = image.copy()
    for i, (x, y, w, h) in enumerate(cajas, start=1):
        cv2.rectangle(out, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(out, f"{i}", (x, max(12, y-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    show_resized(f"{titulo} - Rectángulos Largos Detectados", out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return valores

# --------- Flujo principal ---------
valores_totales = []
imagenes = cargar_imagen_o_pdf(file_path)

if file_path.lower().endswith(".pdf"):
    for idx, img_bgr in enumerate(imagenes, start=1):
        expected = EXPECTED_FIRST_PAGE_BOXES if idx == 1 else None
        valores_totales.extend(procesar_imagen(img_bgr, titulo=f"Página {idx}", expected=expected))
else:
    valores_totales = procesar_imagen(imagenes[0], titulo="Imagen", expected=None)

print(json.dumps(valores_totales, ensure_ascii=False))
