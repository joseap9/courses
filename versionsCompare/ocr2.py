import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io

# Ruta a Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Ruta del PDF
pdf_path = "formulario.pdf"

# Abrir PDF
doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    print(f"\n📄 Página {i+1}")
    image_list = page.get_images(full=True)
    
    if len(image_list) == 0:
        print("✅ Contiene texto o vectores. Extrayendo texto directamente...")
        text = page.get_text()
        print(text)
    else:
        print(f"🖼️ Contiene {len(image_list)} imagen(es). Aplicando OCR a la imagen...")
        xref = image_list[0][0]  # Tomamos la primera imagen (puedes iterar si hay más)
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        # Convertir los bytes a imagen OpenCV
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        open_cv_image = np.array(pil_image)
        open_cv_image = open_cv_image[:, :, ::-1].copy()  # Convertir RGB a BGR

        # (Opcional) Preprocesamiento
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # OCR
        custom_config = r'--oem 3 --psm 4'
        text = pytesseract.image_to_string(gray, config=custom_config, lang="spa")
        
        print("="*40)
        print(text)
        print("="*40)
