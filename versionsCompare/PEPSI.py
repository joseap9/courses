import csv

# Cambia esta ruta por la tuya
ruta_archivo = r'xxxxx'

# Abrimos el archivo y leemos las líneas
with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
    lineas = archivo.readlines()

registros = []

# Recorremos cada bloque de 4 líneas
for i in range(0, len(lineas), 4):
    try:
        l1 = lineas[i].strip()
        l2 = lineas[i+1].strip()
        l3 = lineas[i+2].strip()
        l4 = lineas[i+3].strip()

        # Extraer RUT (primeros 20 caracteres de la primera línea)
        rut = l1[:20]
        apellido1 = l1[20:]

        registros.append([rut, apellido1, l2, l3, l4])
    except IndexError:
        print(f"Bloque incompleto comenzando en la línea {i+1}")
        continue

# Escribimos el resultado en CSV (si lo necesitas)
ruta_salida = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\salida.csv'
with open(ruta_salida, 'w', newline='', encoding='utf-8') as salida:
    writer = csv.writer(salida)
    writer.writerow(['RUT', 'Apellido 1', 'Apellido 2', 'Nombres', 'Apellido Final'])
    writer.writerows(registros)

print("Conversión finalizada correctamente.")