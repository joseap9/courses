import fitz  # PyMuPDF

# Abre el archivo PDF
doc = fitz.open("archivo.pdf")

# Itera sobre todas las páginas del documento
for page_num in range(len(doc)):
    page = doc[page_num]
    
    # Extrae el texto de la página
    text = page.get_text("text")  # Método "text" conserva la estructura con saltos de línea
    
    # Imprime el texto extraído de la página
    print(f"Texto extraído de la página {page_num + 1}:")
    print(repr(text))  # Usa repr para ver los saltos de línea explícitamente
    print("-----")

# Cierra el documento PDF
doc.close()
