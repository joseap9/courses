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
