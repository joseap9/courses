import fitz  # PyMuPDF
import re

# Abre el archivo PDF
doc = fitz.open("archivo.pdf")

# Función para limpiar el texto extraído
def clean_text(text):
    text = text.replace('\xa0', ' ')  # Reemplaza los espacios no separables por espacios normales
    text = text.replace('\n', '\n\n')  # Asegura que cada línea se considere un párrafo separado por un salto de línea doble
    return text

# Itera sobre todas las páginas del documento
for page_num in range(len(doc)):
    page = doc[page_num]
    
    # Extrae el texto de la página
    raw_text = page.get_text("text")
    cleaned_text = clean_text(raw_text)
    
    # Imprime el texto limpio y con saltos de línea visibles
    print(f"Texto limpio de la página {page_num + 1}:")
    print(cleaned_text)
    print("-----")

def delimit_paragraphs(text):
    # Usa una expresión regular para encontrar finales de párrafo típicos seguidos de un salto de línea
    paragraph_endings = r'(\.\s|\.\n|:\s|:\n)'
    
    # Divide el texto usando los puntos de finalización de párrafos
    paragraphs = re.split(paragraph_endings, text)
    
    # Reconstruye los párrafos correctamente sin perder los delimitadores
    reconstructed_paragraphs = []
    current_paragraph = ""
    
    for segment in paragraphs:
        if re.match(paragraph_endings, segment):
            current_paragraph += segment
            reconstructed_paragraphs.append(current_paragraph.strip())
            current_paragraph = ""
        else:
            current_paragraph += segment
    
    if current_paragraph:  # Añadir el último párrafo si existe
        reconstructed_paragraphs.append(current_paragraph.strip())
    
    return reconstructed_paragraphs

# Aplicar la delimitación de párrafos
for page_num in range(len(doc)):
    page = doc[page_num]
    
    # Extrae y limpia el texto
    raw_text = page.get_text("text")
    cleaned_text = clean_text(raw_text)
    
    # Delimita los párrafos
    paragraphs = delimit_paragraphs(cleaned_text)
    
    # Imprime cada párrafo por separado
    for i, paragraph in enumerate(paragraphs, start=1):
        print(f"Párrafo {i} de la página {page_num + 1}:")
        print(paragraph)
        print("-----")


