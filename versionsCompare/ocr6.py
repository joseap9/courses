import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json
import os

# -------- Configuración --------
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
file_path = "formulario.pdf"  # puede ser PDF o imagen
max_width = 1500               # mismo valor que tu pipeline original
ocr_config = r'--oem 3 --psm 6 -l spa'

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

def procesar_imagen_pipeline_antiguo(image_bgr, titulo="Página"):
    """
    Tu pipeline original intacto:
    - Redimensionar si ancho > max_width
    - HSV -> máscara azul
    - Contornos
    - Filtros: 40<w<500 y 10<h<300
    - OCR con psm=6
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

    # HSV y máscara azul (idéntico a tu código)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 180])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Debug (escala solo para mostrar)
    show_resized(f"{titulo} - Máscara Azul (cajas detectables)", mask)

    # Contornos (idéntico)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filtro por tamaño (idéntico)
    cajas = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 40 < w < 500 and 10 < h < 300:
            cajas.append((x, y, w, h))

    # Orden por fila/columna (idéntico)
    cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

    # OCR (idéntico)
    valores = []
    for x, y, w, h in cajas:
        roi = original[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config=ocr_config).strip()
        if text:
            valores.append(text)

    # Visual final con enumeración (idéntico, pero mostrado a escala)
    output_image = image.copy()
    for i, (x, y, w, h) in enumerate(cajas):
        cv2.rectangle(output_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(output_image, f"{i+1}", (x, max(12, y - 5)),
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
        valores_totales.extend(
            procesar_imagen_pipeline_antiguo(img_bgr, titulo=f"Página {idx}")
        )
else:
    valores_totales = procesar_imagen_pipeline_antiguo(imagenes[0], titulo="Imagen")

# Salida
print(json.dumps(valores_totales, ensure_ascii=False))
