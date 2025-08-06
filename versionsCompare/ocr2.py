import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io

# Ruta a Tesseract (ajusta según tu instalación)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Ruta del PDF
pdf_path = "formulario.pdf"
doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    print(f"\n📄 Página {i+1}")
    image_list = page.get_images(full=True)

    if len(image_list) == 0:
        print("✅ Texto detectado. Extrayendo directamente...")
        text = page.get_text()
        print("="*40)
        print(text.strip())
        print("="*40)

    else:
        print(f"🖼️ Imagen escaneada detectada. Extrayendo y aplicando OCR...")
        xref = image_list[0][0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        # Convertir a imagen OpenCV
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        open_cv_image = np.array(pil_image)
        open_cv_image = open_cv_image[:, :, ::-1].copy()  # RGB a BGR
        original = open_cv_image.copy()

        # Preprocesamiento
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # Detección de cuadros/casillas
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 15, 10)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        campos_detectados = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if 10 < w < 150 and 10 < h < 150:  # Filtrar cuadros razonables
                campos_detectados += 1
                cv2.rectangle(original, (x, y), (x + w, y + h), (0, 0, 255), 2)

        print(f"🟥 Campos detectados: {campos_detectados}")

        # Mostrar la imagen con recuadros (opcional)
        cv2.imshow(f"Campos - Página {i+1}", original)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # OCR
        custom_config = r'--oem 3 --psm 4'
        text = pytesseract.image_to_string(gray, config=custom_config, lang="spa")

        print("="*40)
        print(text.strip())
        print("="*40)
