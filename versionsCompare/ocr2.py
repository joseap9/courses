import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
import cv2
import os

# Ruta a Tesseract si es necesario
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

pdf_path = "formulario.pdf"

# Abrir PDF
doc = fitz.open(pdf_path)

def es_pdf_escaneado(doc):
    texto_total = ""
    for page in doc:
        texto = page.get_text()
        texto_total += texto.strip()
    return len(texto_total.strip()) < 20  # umbral: si no hay casi nada de texto, es escaneado

# Verificar si es PDF escaneado o texto normal
if es_pdf_escaneado(doc):
    print("🔍 PDF parece ser escaneado. Aplicando OCR...")

    # Convertir cada página del PDF a imagen
    pages = convert_from_path(pdf_path, dpi=300)

    for i, page in enumerate(pages):
        image_path = f"temp_page_{i}.jpg"
        page.save(image_path, "JPEG")

        # Leer imagen
        image = cv2.imread(image_path)

        # Preprocesamiento
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # OCR
        custom_config = r'--oem 3 --psm 4'
        text = pytesseract.image_to_string(gray, config=custom_config, lang="spa")

        print(f"\n🧾 TEXTO OCR - Página {i+1}")
        print("=" * 40)
        print(text)
        print("=" * 40)

        os.remove(image_path)

else:
    print("✅ PDF contiene texto seleccionable. Extrayendo sin OCR...")
    for i, page in enumerate(doc):
        text = page.get_text()
        print(f"\n🧾 TEXTO EXTRAÍDO - Página {i+1}")
        print("=" * 40)
        print(text)
        print("=" * 40)
