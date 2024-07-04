import pandas as pd

def check_srs_numbers(excel_path, srs_numbers, sheet_number=1):
    # Leer el archivo Excel y la hoja especificada
    df = pd.read_excel(excel_path, sheet_name=sheet_number-1)

    # Iterar a través de los números en el array y verificar si hay coincidencias
    for number in srs_numbers:
        if df[df['SRS Contract Number'] == number].empty:
            print("No")
        else:
            print("Si")

# Ejemplo de uso
excel_path = r'ruta_al_archivo_excel.xlsx'
srs_numbers = [123, 456, 789]  # Reemplaza estos números con los valores de tu array
sheet_number = 1  # Cambia este número para especificar la hoja (1 para la primera hoja, 2 para la segunda, etc.)

check_srs_numbers(excel_path, srs_numbers, sheet_number)
