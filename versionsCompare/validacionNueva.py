import fitz  # PyMuPDF
import json

# Ruta al archivo PDF (puedes usar un parámetro dinámico de PAD si quieres)
pdf_path = r"C:\ruta\del\archivo.pdf"

# Abrir el PDF
doc = fitz.open(pdf_path)

# Diccionario para almacenar los campos del formulario
form_fields = {}

# Iterar sobre cada página para buscar widgets (campos)
for page in doc:
    widgets = page.widgets()
    if widgets:
        for widget in widgets:
            field_name = widget.field_name
            field_value = widget.field_value
            form_fields[field_name] = field_value

doc.close()

# Imprimir como JSON para que PAD lo pueda interpretar
print(json.dumps(form_fields))



========
# -*- coding: utf-8 -*-
pdf_path = r"C:\ruta\del\archivo.pdf"

with open(pdf_path, "rb") as f:
    content = f.read()

# Convertimos a texto (intentando decodificar como latin-1 para evitar errores con caracteres especiales)
text = content.decode("latin-1")

# Buscar campos del formulario (simplificado)
import re
campos = re.findall(r"/T\s*\((.*?)\)\s*/V\s*\((.*?)\)", text)

# Mostrar resultados como diccionario
form_fields = {k: v for k, v in campos}
print(form_fields)