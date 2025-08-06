import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io

# Ruta a Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Ruta del PDF escaneado
pdf_path = "DeclaraciónBFJun2025_giwIbRd.pdf"
doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    print(f"\n📄 Página {i+1}")
    image_list = page.get_images(full=True)

    if len(image_list) == 0:
        print("❌ No hay imagen embebida, probablemente no es un PDF escaneado.")
        continue

    # Extraer la primera imagen embebida
    xref = image_list[0][0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]

    # Convertir a imagen OpenCV
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = np.array(pil_image)[:, :, ::-1].copy()  # RGB a BGR
    original = image.copy()

    # Convertir a escala de grises y suavizar
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Detectar líneas horizontales y verticales (líneas largas de formularios)
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (100, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

    lines_h = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_h)
    lines_v = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_v)

    combined = cv2.add(lines_h, lines_v)

    # Detectar contornos
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    campos_detectados = 0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 40 and h > 10:  # ajusta según tamaño de campos
            campos_detectados += 1
            cv2.rectangle(original, (x, y), (x + w, y + h), (0, 0, 255), 2)

    print(f"🟥 Se detectaron {campos_detectados} campos en la página {i+1}.")

    # Mostrar imagen con campos detectados
    cv2.imshow(f"Campos detectados - Página {i+1}", original)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # OCR para extraer texto (manuscrito o impreso)
    config = r'--oem 3 --psm 4'
    ocr_text = pytesseract.image_to_string(gray, config=config, lang='spa')

    print("📄 Texto extraído con OCR:")
    print("=" * 40)
    print(ocr_text.strip())
    print("=" * 40)
