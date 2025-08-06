import cv2
import pytesseract
import numpy as np

# Ruta a Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cargar imagen
image_path = "07d49400-86ea-4827-afb0-40b835b8de8c.heic"
image = cv2.imread(image_path)
original = image.copy()

# Redimensionar si es necesario
max_width = 1500
if image.shape[1] > max_width:
    scale_ratio = max_width / image.shape[1]
    image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))
    original = cv2.resize(original, (int(original.shape[1] * scale_ratio), int(original.shape[0] * scale_ratio)))

# Convertir a HSV para detectar color azul claro
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
lower_blue = np.array([90, 50, 180])
upper_blue = np.array([130, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Mostrar la máscara para verificar detección
cv2.imshow("Máscara Azul (cajas detectables)", mask)

# Encontrar contornos sobre la máscara (zonas blancas)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Extraer regiones de interés (ROI) y aplicar OCR
ocr_config = r'--oem 3 --psm 6 -l spa'
valores = []
output_image = image.copy()

# Ordenar contornos por posición (primero por fila y luego por columna)
cajas = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 50 and h > 15:  # Filtro para evitar ruido
        cajas.append((x, y, w, h))

cajas = sorted(cajas, key=lambda b: (b[1], b[0]))  # Orden por fila, luego columna

# Aplicar OCR y dibujar resultados
for i, (x, y, w, h) in enumerate(cajas):
    roi = original[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config=ocr_config)
    valores.append(text.strip())

    # Dibujar recuadro y número
    cv2.rectangle(output_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(output_image, f"{i+1}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

# Mostrar resultados
cv2.imshow("Cajas Detectadas y Numeradas", output_image)

# Imprimir textos detectados
print("== TEXTOS DETECTADOS EN LAS CAJAS ==")
for i, val in enumerate(valores, 1):
    print(f"{i}. {val}")

cv2.waitKey(0)
cv2.destroyAllWindows()
