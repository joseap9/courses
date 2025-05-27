# -*- coding: utf-8 -*-
import sys
import fitz  # pymupdf
import json

pdf_path = sys.argv[1]  # recibe la ruta como argumento

doc = fitz.open(pdf_path)
form_fields = {}

for page in doc:
    widgets = page.widgets()
    if widgets:
        for widget in widgets:
            form_fields[widget.field_name] = widget.field_value

doc.close()

# Imprimir resultado para que PAD pueda capturarlo
print(json.dumps(form_fields, ensure_ascii=False))
