import cv2
import pytesseract
import numpy as np

# Ruta de Tesseract
pytesseract.pytesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cargar imagen
image_path = "07d49400-86ea-4827-afb0-40b835b8de8c.heic"
image = cv2.imread(image_path)

# Redimensionar a base conocida
base_width = 1500
scale_ratio = base_width / image.shape[1]
image = cv2.resize(
    image,
    (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio))
)

# Mostrar imagen original (opcional)
cv2.imshow("Imagen Original", image)

# Convertir a HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Definir rango de azul claro (el color de tus cajas)
lower_blue = np.array([90, 50, 180])
upper_blue = np.array([130, 255, 255])

# Crear máscara
mask = cv2.inRange(hsv, lower_blue, upper_blue)
cv2.imshow("Máscara Azul", mask)

# Encontrar TODOS los contornos (sin filtro de tamaño)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Extraer bounding boxes
cajas = [cv2.boundingRect(cnt) for cnt in contours]

# Ordenar por posición (y luego x por si hay filas múltiples)
cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

# Preparar imagen para visualizar
output_image = image.copy()
ocr_config = r'--oem 3 --psm 6 -l spa'
valores = []

# Extraer texto y dibujar
for i, (x, y, w, h) in enumerate(cajas):
    roi = image[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config=ocr_config)
    valores.append(text.strip())

    # Dibujar recuadro y número
    cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(output_image, f"{i+1}", (x + 2, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

# Mostrar imagen con todas las cajas numeradas
cv2.imshow("Cajas Detectadas y Numeradas", output_image)

# Imprimir el resultado
print("== TEXTOS DETECTADOS EN ORDEN ==")
for i, texto in enumerate(valores, 1):
    print(f"{i}. {texto}")

cv2.waitKey(0)
cv2.destroyAllWindows()
