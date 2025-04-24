import fitz  # PyMuPDF

def remove_restrictions_with_fitz(input_pdf, output_pdf):
    try:
        doc = fitz.open(input_pdf)  # open the PDF even if restricted
        doc.save(output_pdf)        # just saving it removes restrictions like copy/edit
        doc.close()
        print(f"✅ PDF saved without restrictions at: {output_pdf}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Ejemplo de uso
remove_restrictions_with_fitz("protegido.pdf", "libre.pdf")