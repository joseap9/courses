import fitz  # PyMuPDF para PDF -> imagen
import cv2
import pytesseract
import numpy as np
import json
import os

# ---------------- Configuración ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

file_path = "formulario.pdf"   # Puede ser .pdf o imagen (.png/.jpg/.heic si tu OpenCV lo soporta)
max_width = 1500               # Mismo criterio de tu pipeline original
ocr_config = r'--oem 3 --psm 6 -l spa'

# Orden dentro de la fila: True = derecha→izquierda, False = izquierda→derecha
ORDER_RIGHT_TO_LEFT = True

# Mostrar ventanas a escala (solo visual)
SHOW_MAX_W, SHOW_MAX_H = 1400, 900
def show_resized(title, img, max_w=SHOW_MAX_W, max_h=SHOW_MAX_H):
    h, w = img.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    cv2.imshow(title, img)

# ---------------- PDF → Imagen (ancho ≈ max_width) ----------------
def dpi_for_target_width(page, target_width_px=1500, min_dpi=120, max_dpi=300):
    w_pt = page.rect.width  # puntos (1/72")
    w_in = w_pt / 72.0 if w_pt else 0.0
    if w_in <= 0:
        return 200
    return int(np.clip(target_width_px / w_in, min_dpi, max_dpi))

def render_pdf_page_to_bgr(page, target_width_px=1500):
    dpi = dpi_for_target_width(page, target_width_px=target_width_px)
    pix = page.get_pixmap(dpi=dpi, alpha=False)  # RGB
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

# ---------------- Orden: filas y columnas ----------------
def ordenar_por_filas_y_columnas(cajas, img_h, row_tol_ratio=0.02, right_to_left=True):
    """
    Agrupa por filas (tolerancia vertical relativa) y ordena:
      - Filas: arriba→abajo
      - Dentro de la fila: derecha→izquierda (si right_to_left=True) o izquierda→derecha
    """
    if not cajas:
        return []

    # Orden preliminar por Ycentro asc y Xcentro (dirección inversa si R→L)
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

    # Filas por Y asc; dentro de la fila orden por X (según dirección)
    filas = sorted(filas, key=lambda fila: sum([fy + fh / 2.0 for (_, fy, fw, fh) in fila]) / len(fila))
    out = []
    for fila in filas:
        fila_ordenada = sorted(
            fila,
            key=lambda b: -(b[0] + b[2] / 2.0) if right_to_left else (b[0] + b[2] / 2.0)
        )
        out.extend(fila_ordenada)
    return out

# ---------------- Procesamiento principal (relativo) ----------------
def procesar_imagen_rectangulos_relativos(image_bgr, titulo="Página"):
    """
    Pipeline original con:
      - Redimensionado a max_width (si aplica)
      - Máscara HSV para azul
      - Filtro de rectángulos HORIZONTALES con umbrales RELATIVOS a W,H
      - OCR psm=6
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

    H, W = image.shape[:2]

    # Máscara azul (tus umbrales)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Debug
    show_resized(f"{titulo} - Máscara Azul (cajas detectables)", mask)

    # --- UMBRALES RELATIVOS (ajusta estos porcentajes a tu plantilla) ---
    # Rectángulos largos horizontales: w grande relativo, h pequeño-moderado, y área suficiente
    W_MIN = int(W * 0.03)   # 3% del ancho mínimo (evita puntitos)
    W_MAX = int(W * 0.95)   # 95% del ancho máximo (por si hay líneas largas)
    H_MIN = int(H * 0.006)  # 0.6% del alto (evita dos puntos muy finos)
    H_MAX = int(H * 0.10)   # 10% del alto (si tus rectángulos son más altos, sube a 0.12–0.15)
    AREA_MIN = int(W * H * 0.0002)  # 0.02% del área total (ruido fuera)
    ASPECT_MIN = 2.2         # Relación mínima w/h (más alto = más “largo”)

    # Contornos y filtro relativo
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

    # Orden (filas arriba→abajo, dentro de fila derecha→izquierda)
    cajas = ordenar_por_filas_y_columnas(cajas, H, right_to_left=ORDER_RIGHT_TO_LEFT)

    # OCR (igual)
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    # Visual final con enumeración (a escala para ver completo)
    out = image.copy()
    for i, (x, y, w, h) in enumerate(cajas, start=1):
        cv2.rectangle(out, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(out, f"{i}", (x, max(12, y-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
    show_resized(f"{titulo} - Rectángulos Detectados y Numerados", out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return valores

# ---------------- Ejecutar ----------------
imagenes = cargar_imagen_o_pdf(file_path)
valores_totales = []

if file_path.lower().endswith(".pdf"):
    for idx, img_bgr in enumerate(imagenes, start=1):
        valores_totales.extend(procesar_imagen_rectangulos_relativos(img_bgr, titulo=f"Página {idx}"))
else:
    valores_totales = procesar_imagen_rectangulos_relativos(imagenes[0], titulo="Imagen")

print(json.dumps(valores_totales, ensure_ascii=False))
