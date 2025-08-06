import cv2

# Cargar imagen
image_path = "839398e1-8eb0-40c6-a166-d8bd627dfe78.png"
image = cv2.imread(image_path)

# Redimensionar a base 1000px de ancho para mantener proporciones
base_width = 1000
scale_ratio = base_width / image.shape[1]
image = cv2.resize(image, (int(image.shape[1] * scale_ratio), int(image.shape[0] * scale_ratio)))

# Zonas en base a proporciones aproximadas
zonas = {
    "rut_identificacion": (0.035, 0.273, 0.18, 0.04),
    "razon_social": (0.265, 0.273, 0.27, 0.04),
    "domicilio": (0.035, 0.335, 0.18, 0.04),
    "ciudad": (0.265, 0.335, 0.18, 0.04),
    "lugar_constitucion": (0.545, 0.335, 0.18, 0.04),
    "telefono": (0.545, 0.390, 0.18, 0.04),
    "domicilio_tributario": (0.035, 0.390, 0.45, 0.04),
    "rut_rep_legal": (0.035, 0.460, 0.18, 0.04),
    "nombre_rep_legal": (0.265, 0.460, 0.27, 0.04)
}

# Dibujar cada zona
h, w = image.shape[:2]
for campo, (x_pct, y_pct, w_pct, h_pct) in zonas.items():
    x = int(x_pct * w)
    y = int(y_pct * h)
    w_box = int(w_pct * w)
    h_box = int(h_pct * h)
    cv2.rectangle(image, (x, y), (x + w_box, y + h_box), (0, 0, 255), 2)
    cv2.putText(image, campo, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36,255,12), 1)

# Mostrar imagen con recuadros
cv2.imshow("Zonas de OCR", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
