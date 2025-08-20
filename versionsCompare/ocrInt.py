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
DELIM = "§§§"

# -------------------- Campos de formulario en orden fijo --------------------
FIELDS_ORDER = [
    "ID",
    "Razon social",
    "RUT",
    "Lugar",
    "Ciudad",
    "Domicilio",
    "Telefono",
    "Domicilio Tributario",
    "Nombre representante legal 1",
    "RUT Rep Legal 1",
    "Nombre representante legal 2",
    "RUT Rep Legal 2",
    "TE Otra",
]

# Normalización básica de claves (sin acentos/espacios/guiones/underscores, minúsculas)
_TRANS = str.maketrans({
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
    "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "Ü": "u",
    "ñ": "n", "Ñ": "n",
})
def norm_key(s: str) -> str:
    if not s:
        return ""
    s = s.translate(_TRANS)
    s = re.sub(r"[^a-zA-Z0-9]+", "", s)  # quitar todo lo que no sea alfanumérico
    return s.lower()

# Mapeo de alias -> clave canónica (normalizada) para mayor tolerancia
ALIASES = {
    norm_key("ID"): {"id", "folio", "numeroid"},
    norm_key("Razon social"): {"razonsocial", "razonsoc", "rsocial"},
    norm_key("RUT"): {"rut", "run"},
    norm_key("Lugar"): {"lugar", "localidad", "lcl"},
    norm_key("Ciudad"): {"ciudad", "comuna"},
    norm_key("Domicilio"): {"domicilio", "direccion", "direccionparticular"},
    norm_key("Telefono"): {"telefono", "fono", "tel", "te"},
    norm_key("Domicilio Tributario"): {"domiciliotributario", "direcciontributaria"},
    norm_key("Nombre representante legal 1"): {"nombrerepresentantelegal1", "representante1", "rep1nombre"},
    norm_key("RUT Rep Legal 1"): {"rutreplegal1", "rutrepresentantelegal1", "rep1rut"},
    norm_key("Nombre representante legal 2"): {"nombrerepresentantelegal2", "representante2", "rep2nombre"},
    norm_key("RUT Rep Legal 2"): {"rutreplegal2", "rutrepresentantelegal2", "rep2rut"},
    norm_key("TE Otra"): {"teotra", "telefonoextra", "telotro"},
}
def canonical_norm_from_incoming(nkey: str) -> str:
    canon_norms = [norm_key(k) for k in FIELDS_ORDER]
    for cn in canon_norms:
        if nkey == cn:
            return cn
    for cn, aliases in ALIASES.items():
        if nkey in aliases:
            return cn
    return ""

# -------------------- Funciones auxiliares --------------------
def es_pdf_texto(pdf_path, umbral=500):
    """Retorna True si el PDF contiene más texto que el umbral indicado."""
    doc = fitz.open(pdf_path)
    total_chars = 0
    for page in doc:
        total_chars += len(page.get_text())
        if total_chars >= umbral:
            doc.close()
            return True
    doc.close()
    return False

def extraer_campos_formulario(pdf_path):
    """Extrae campos de formulario editable y los indexa por clave NORMALIZADA canónica."""
    doc = fitz.open(pdf_path)
    out = {}
    for page in doc:
        widgets = page.widgets()
        if not widgets:
            continue
        for w in widgets:
            k = (w.field_name or "").strip()
            v = (getattr(w, "field_value", "") or "")
            nkey = norm_key(k)
            canon = canonical_norm_from_incoming(nkey)
            if canon:
                out[canon] = str(v).strip()
    doc.close()
    return out  # claves normalizadas canónicas

def filtrar_campos_interes(texto):
    """(PDF de texto) Devuelve solo campos de interés del texto plano. Ajusta si lo necesitas."""
    campos_interes = ["Nombre", "Apellido", "RUT", "Dirección"]
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
    pix = page.get_pixmap(dpi=dpi, alpha=False)  # RGB
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

def cargar_imagen_o_pdf(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        imgs = [render_pdf_page_to_bgr(p, target_width_px=max_width) for p in doc]
        doc.close()
        return imgs
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

# --- OCR original que devuelve SOLO textos para cajas azules ---
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

# -------------------- Agrupación por filas y columnas (tabla 3 cols) --------------------
def agrupar_en_filas_por_y(cajas, img_h, row_tol_ratio=0.02):
    """Devuelve una lista de filas, cada fila es una lista de índices de 'cajas'."""
    if not cajas:
        return []

    # Ordenar por Y-centro
    indices = list(range(len(cajas)))
    indices.sort(key=lambda i: (cajas[i][1] + cajas[i][3] / 2.0))

    row_tol = max(int(img_h * row_tol_ratio), 6)
    filas = []
    for i in indices:
        x, y, w, h = cajas[i]
        cy = y + h / 2.0
        placed = False
        for fila in filas:
            cys = []
            for j in fila:
                _, fy, fw, fh = cajas[j]
                cys.append(fy + fh / 2.0)
            if abs(cy - (sum(cys) / len(cys))) <= row_tol:
                fila.append(i)
                placed = True
                break
        if not placed:
            filas.append([i])

    # Ordenar filas por Y y dentro de cada fila por X-centro ascendente
    filas.sort(key=lambda fila: sum([(cajas[j][1] + cajas[j][3] / 2.0) for j in fila]) / len(fila))
    for fila in filas:
        fila.sort(key=lambda j: (cajas[j][0] + cajas[j][2] / 2.0))
    return filas

def asignar_columna_por_x(cx, W, bands=(0.33, 0.66)):
    """Devuelve 'L' (izq), 'C' (centro) o 'R' (der) según el X-centro en bandas."""
    b1 = W * bands[0]
    b2 = W * bands[1]
    if cx < b1:
        return 'L'   # izquierda: RUT
    elif cx < b2:
        return 'C'   # centro: Cargo
    else:
        return 'R'   # derecha: Nombre

def extraer_tabla_3cols_por_posicion(cajas, textos, W, H, row_tol_ratio=0.02, bands=(0.33, 0.66), min_filas=2):
    """
    Dada la lista de cajas (x,y,w,h) y sus textos OCR emparejados, intenta
    armar filas de 3 columnas por X: L=RUT, C=Cargo, R=Nombre.
    Retorna lista de strings "Nombre_i Cargo_i Rut_i".
    """
    paired = [(cajas[i], (textos[i] if i < len(textos) else "").strip()) for i in range(len(cajas))]
    paired = [(box, txt) for (box, txt) in paired if txt]
    if not paired:
        return []

    cajas_nonempty = [p[0] for p in paired]
    textos_nonempty = [p[1] for p in paired]

    filas_idx = agrupar_en_filas_por_y(cajas_nonempty, H, row_tol_ratio=row_tol_ratio)

    filas_out = []
    for fila in filas_idx:
        col_map = {'L': None, 'C': None, 'R': None}
        for j in fila:
            x, y, w, h = cajas_nonempty[j]
            cx = x + w / 2.0
            col = asignar_columna_por_x(cx, W, bands=bands)
            if col_map[col] is None:
                col_map[col] = textos_nonempty[j]

        if col_map['L'] and col_map['C'] and col_map['R']:
            fila_txt = f"{col_map['R']} {col_map['C']} {col_map['L']}"  # Nombre Cargo RUT
            filas_out.append(fila_txt)

    if len(filas_out) < min_filas:
        return []

    return filas_out

# --- Variante para detectar cajas y textos (necesaria para tabla por posición) ---
def detectar_cajas_y_textos(image_bgr):
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
    textos = []
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

    # Ordenar por filas/columnas como tu flujo original (derecha->izquierda dentro de la fila)
    cajas = ordenar_por_filas_y_columnas(cajas, H, right_to_left=ORDER_RIGHT_TO_LEFT)

    for (x, y, w, h) in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        txt = pytesseract.image_to_string(gray, config=ocr_config).strip()
        textos.append(txt if txt else "")

    return (cajas, textos, W, H)

# -------------------- Lógica principal --------------------
resultado = {}

ext = os.path.splitext(file_path)[1].lower()
if ext in (".png", ".jpg", ".jpeg", ".heic"):
    resultado["tipo"] = "imagen"
    resultado["valores"] = procesar_imagen_rectangulos_relativos(cargar_imagen_o_pdf(file_path)[0])

elif ext == ".pdf":
    if es_pdf_texto(file_path):
        # Intentar primero como formulario editable (orden fijo)
        campos_norm = extraer_campos_formulario(file_path)  # claves normalizadas canónicas
        if campos_norm:
            resultado["tipo"] = "pdf_formulario"
            ordered_vals = []
            for label in FIELDS_ORDER:
                cn = norm_key(label)
                val = campos_norm.get(cn, "")
                ordered_vals.append(val)
            resultado["valores"] = ordered_vals
        else:
            # Texto normal: se mantiene tu lógica actual (si quieres, luego estandarizas igual que formulario)
            doc = fitz.open(file_path)
            texto = "\n".join([page.get_text() for page in doc])
            doc.close()
            resultado["tipo"] = "pdf_texto"
            resultado["valores"] = filtrar_campos_interes(texto)
    else:
        # -------- PDF ESCANEADO: primero intentamos extraer la TABLA 3 columnas por posición X --------
        resultado["tipo"] = "pdf_escaneado"
        imagenes = cargar_imagen_o_pdf(file_path)

        salida_final = []
        tabla_encontrada = False

        for img in imagenes:
            cajas, textos, W, H = detectar_cajas_y_textos(img)
            filas_tabla = extraer_tabla_3cols_por_posicion(
                cajas, textos, W, H,
                row_tol_ratio=0.02,     # tolerancia vertical
                bands=(0.33, 0.66),     # tercios (ajusta si tus columnas no están centradas)
                min_filas=2             # al menos 2 filas “válidas” para considerarlo tabla
            )
            if filas_tabla:
                tabla_encontrada = True
                salida_final.extend(filas_tabla)
            else:
                # fallback: si no hay tabla confiable, deja los textos “planos” como antes
                salida_final.extend([t for t in textos if t])

        resultado["valores"] = salida_final

# -------------------- Salida para PAD --------------------
if isinstance(resultado.get("valores"), dict):
    salida = DELIM.join(str(v) for v in resultado["valores"].values())
elif isinstance(resultado.get("valores"), list):
    salida = DELIM.join(str(v) for v in resultado["valores"])
else:
    salida = str(resultado.get("valores", ""))

print(salida)
