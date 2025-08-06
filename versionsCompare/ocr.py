import cv2
import pytesseract

# Ruta de Tesseract si no está en el PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cargar imagen original
image_path = "b0df7717-3255-4af6-a471-f727695a6e7a.jpeg"
image = cv2.imread(image_path)

# Preprocesamiento mejorado
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.bilateralFilter(gray, 11, 17, 17)  # suaviza sin perder bordes
# Aumentar contraste
gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

# Puedes probar también con esta línea si lo anterior falla:
# gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 10)

# Mostrar para depurar (opcional)
# cv2.imshow("Procesada", gray); cv2.waitKey(0); cv2.destroyAllWindows()

# OCR con config ajustada
custom_config = r'--oem 3 --psm 4'  # 4 = layout fluido, bueno para formularios
text = pytesseract.image_to_string(gray, config=custom_config, lang="spa")

# Mostrar resultado crudo
print("TEXTO OCR:")
print("="*40)
print(text)
print("="*40)

########################
import cv2
import pytesseract
import json

# Ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# OCR de la imagen
image_path = "b0df7717-3255-4af6-a471-f727695a6e7a.jpeg"
image = cv2.imread(image_path)

# Preprocesamiento
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.bilateralFilter(gray, 11, 17, 17)
gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

custom_config = r'--oem 3 --psm 4'
text = pytesseract.image_to_string(gray, config=custom_config, lang="spa")

# Separar por líneas y eliminar vacías
lines = [line.strip() for line in text.split('\n') if line.strip()]

# Campos esperados en orden y sus claves destino
campos = {
    "RUT": ["rut", "rutin"],
    "Razón social": ["razon social"],
    "Domicilio": ["domicilio"],
    "Ciudad": ["ciudad"],
    "País": ["pais", "constitucion"],
    "Teléfono": ["telefono"],
    "Representante legal 1": ["rep. legal 1", "representante legal 1"],
    "Representante legal 2": ["rep. legal 2", "representante legal 2"],
    "Uso del Vehículo": ["uso del vehiculo"],
    "Tipo de entidad": ["tipo de entidad"],
    "Alta gerencia": ["cargo nombre", "rut identificacion cargo nombre"]
}

resultado = {}
i = 0
while i < len(lines) - 1:
    linea = lines[i].lower()

    for key, keywords in campos.items():
        if any(k in linea for k in keywords):
            # Línea siguiente contiene el valor
            valor = lines[i+1].strip()

            # Casos especiales como "RUT y Razón social" juntos
            if key == "RUT" and " " in valor:
                rut, razon = valor.split(" ", 1)
                resultado["RUT"] = rut
                resultado["Razón social"] = razon
            elif key == "Domicilio" and "." in valor:
                # PORTUGAL 373 SANTIAGO. CHILE
                partes = valor.split()
                resultado["Domicilio"] = " ".join(partes[:-2])
                resultado["Ciudad"] = partes[-2].replace(".", "")
                resultado["País"] = partes[-1].replace(".", "")
            else:
                resultado[key] = valor
            i += 1  # saltamos la línea siguiente porque ya la usamos
            break
    i += 1

# Mostrar JSON resultante
print("\nResultado en JSON:")
print(json.dumps(resultado, indent=2, ensure_ascii=False))

================================================

import cv2
import pytesseract
import numpy as np
import json

# Configurar ruta a Tesseract si es necesario
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TuUsuario\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Cargar imagen
image_path = "b0df7717-3255-4af6-a471-f727695a6e7a.jpeg"
image = cv2.imread(image_path)

# Convertir a HSV para detectar color azul claro
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Rango para azul claro (ajustable según tu formulario)
lower_blue = np.array([85, 30, 100])
upper_blue = np.array([140, 255, 255])

# Crear máscara para regiones azul claro
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Encontrar contornos de las cajas azules
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Ordenar contornos de arriba hacia abajo
contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

# Extraer texto de cada contorno
resultados = []
for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    if w > 100 and h > 20:  # filtrar cajas pequeñas/no útiles
        roi = image[y:y+h, x:x+w]

        # Preprocesamiento
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # OCR
        texto = pytesseract.image_to_string(gray, config='--oem 3 --psm 7', lang='spa')

        # Reemplazos comunes de OCR
        texto = texto.replace("?", "7").replace("©", "0").strip()

        resultados.append(texto)

# Mostrar resultados como lista
print("\nResultados por caja azul:")
for i, t in enumerate(resultados):
    print(f"{i+1}: {t}")

# Opcional: Guardar como JSON
json_data = {f"campo_{i+1}": texto for i, texto in enumerate(resultados)}
with open("resultados_ocr.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print("\nGuardado en resultados_ocr.json")


