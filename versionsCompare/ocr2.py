# Redimensionar a ancho base
base_width = 1000
scale_ratio = base_width / image.shape[1]
image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))

# Convertir a HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Detectar color celeste
lower_blue = np.array([90, 30, 170])
upper_blue = np.array([130, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Morfología para unir regiones si hay cajas partidas
kernel = np.ones((3, 3), np.uint8)
mask = cv2.dilate(mask, kernel, iterations=1)

# Mostrar máscara
cv2.imshow("Máscara Azul", mask)

# Contornos sin filtrar por tamaño
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Ordenar por posición
cajas = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    cajas.append((x, y, w, h))

# Ordenar verticalmente
cajas = sorted(cajas, key=lambda b: (b[1], b[0]))

# Visualización + OCR
ocr_config = r'--oem 3 --psm 6 -l spa'
output_image = image.copy()
valores = []

for i, (x, y, w, h) in enumerate(cajas):
    roi = image[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config=ocr_config)
    valores.append(text.strip())

    cv2.rectangle(output_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(output_image, f"{i+1}", (x+2, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

# Mostrar cajas detectadas numeradas
cv2.imshow("Cajas Detectadas y Numeradas", output_image)

# Imprimir valores
print("=== TEXTOS DETECTADOS ===")
for i, val in enumerate(valores, 1):
    print(f"{i}. {val}")

cv2.waitKey(0)
cv2.destroyAllWindows()