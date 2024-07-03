import pandas as pd

def filter_rows_by_array(excel_path, srs_numbers, columns_to_return, output_path):
    # Leer el archivo Excel
    df = pd.read_excel(excel_path)

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
            filtered_df = filtered_df.append(not_found_row, ignore_index=True)

    # Guardar el DataFrame filtrado en un nuevo archivo Excel
    filtered_df.to_excel(output_path, index=False)

# Ejemplo de uso
excel_path = 'ruta_al_archivo_excel.xlsx'
srs_numbers = [123, 456, 789]  # Reemplaza estos números con los valores de tu array
columns_to_return = ['SRS Contract Number', 'Column1', 'Column2']  # Reemplaza con las columnas deseadas
output_path = 'filas_filtradas.xlsx'

filter_rows_by_array(excel_path, srs_numbers, columns_to_return, output_path)