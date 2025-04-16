import csv

# Abrimos el archivo original
with open('PTGENST2025010603.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Agrupamos cada 4 líneas como un registro
records = []
for i in range(0, len(lines), 4):
    try:
        linea1 = lines[i].strip()
        linea2 = lines[i+1].strip()
        linea3 = lines[i+2].strip()
        linea4 = lines[i+3].strip()

        # Extraemos los primeros 20 dígitos como ID/RUT
        rut = linea1[:20]
        apellido1 = linea1[20:]  # El resto es el primer apellido

        records.append([rut, apellido1, linea2, linea3, linea4])
    except IndexError:
        print(f"Línea incompleta en el bloque que comienza en línea {i}")
        continue

# Escribimos los datos en un archivo CSV
with open('salida.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['RUT', 'Apellido 1', 'Apellido 2', 'Nombres', 'Apellido Final'])
    writer.writerows(records)

print("Archivo CSV generado con éxito.")