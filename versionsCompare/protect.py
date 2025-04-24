import pikepdf

def remove_pdf_restrictions(input_pdf, output_pdf):
    try:
        # Abrir el PDF ignorando las restricciones de propietario
        pdf = pikepdf.open(input_pdf)
        pdf.save(output_pdf)
        pdf.close()
        print(f"Restrictions removed. Unlocked PDF saved to: {output_pdf}")
    except Exception as e:
        print("Failed to remove restrictions:", e)

# Ejemplo de uso
remove_pdf_restrictions("protegido.pdf", "liberado.pdf")