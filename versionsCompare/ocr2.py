import cv2
import pytesseract
import numpy as np

# Ruta Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cargar imagen
image_path = "07d49400-86ea-4827-afb0-40b835b8de8c.heic"
image = cv2.imread(image_path)

# Redimensionar
max_width = 1500
if image.shape[1] > max_width:
    scale_ratio = max_width / image.shape[1]
    image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))

# Mostrar imagen original redimensionada
cv2.imshow("Imagen Original", image)

# Convertir a HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Definir rango de azul claro
lower_blue = np.array([90, 50, 180])
upper_blue = np.array([130, 255, 255])

# Máscara para detectar color azul
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Mostrar la máscara
cv2.imshow("Máscara Azul (cajas detectables)", mask)

# Encontrar contornos
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filtrar y ordenar
cajas = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 50 and h > 15:
        cajas.append((x, y, w, h))
cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

# OCR y visualización
ocr_config = r'--oem 3 --psm 6 -l spa'
valores = []

# Clonar imagen para dibujo final
output_image = image.copy()

for i, (x, y, w, h) in enumerate(cajas):
    roi = image[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config=ocr_config)
    valores.append(text.strip())

    # Dibujar recuadro y número
    cv2.rectangle(output_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(output_image, f"{i+1}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

# Mostrar imagen final con recuadros
cv2.imshow("Cajas Detectadas y Numeradas", output_image)

# Imprimir textos extraídos
print("== TEXTOS DETECTADOS EN LAS CAJAS ==")
for i, val in enumerate(valores, 1):
    print(f"{i}. {val}")

# Esperar tecla
cv2.waitKey(0)
cv2.destroyAllWindows()
