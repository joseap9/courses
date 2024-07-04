import pandas as pd

def filter_rows_by_array(excel_path, srs_numbers, columns_to_return, output_path, sheet_number=1):
    # Leer el archivo Excel y la hoja especificada
    df = pd.read_excel(excel_path, sheet_name=sheet_number-1)

    # Crear un DataFrame vacío para almacenar las filas filtradas
    filtered_df = pd.DataFrame(columns=columns_to_return)

    # Iterar a través de los números en el array y buscar filas coincidentes
    for number in srs_numbers:
        filtered_row = df[df['SRS Contract Number'] == number]

        if not filtered_row.empty:
            # Seleccionar solo las columnas especificadas
            filtered_row = filtered_row[columns_to_return]
            filtered_df = pd.concat([filtered_df, filtered_row], ignore_index=True)
        else:
            # Crear una fila con el mensaje "No encontrado"
            not_found_row = {col: "No encontrado" for col in columns_to_return}
            not_found_row['SRS Contract Number'] = number
            filtered_df = filtered_df._append(not_found_row, ignore_index=True)

    # Guardar el DataFrame filtrado en un nuevo archivo Excel
    filtered_df.to_excel(output_path, index=False)

# Ejemplo de uso
excel_path = r'ruta_al_archivo_excel.xlsx'
srs_numbers = [123, 456, 789]  # Reemplaza estos números con los valores de tu array
columns_to_return =  ['SRS Contract Number',
'Customer Complete Name',
'Customer ID Number',
'Nationality (Country of birth)',
'Total Monthly Income',
'Occupation',
'Manufacturer Description', 
'Product Type /Account Type',
'Model Description',
'Vehicle Type',
'Vehicle Selling Price (Cash Selling Price)',
'Amount Financed',
'Company Employer (For employees only)',
'PEP mark',
'AML Risk Score',
'Term'] # Reemplaza con las columnas deseadas
output_path = r'filas_filtradas.xlsx'
sheet_number = 1  # Cambia este número para especificar la hoja (1 para la primera hoja, 2 para la segunda, etc.)

filter_rows_by_array(excel_path, srs_numbers, columns_to_return, output_path, sheet_number)
