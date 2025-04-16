import pandas as pd

ruta_archivo = r'xxx'

# Leer archivo
with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros = []

for i in range(0, len(lineas), 4):
    try:
        l1 = lineas[i].strip()
        l2 = lineas[i+1].strip()
        l3 = lineas[i+2].strip()
        l4 = lineas[i+3].strip()

        rut = l1[:20]
        apellido1 = l1[20:]

        registros.append([rut, apellido1, l2, l3, l4])
    except IndexError:
        print(f"Bloque incompleto comenzando en la línea {i+1}")
        continue

# Convertimos a DataFrame
df = pd.DataFrame(registros, columns=['RUT', 'Apellido 1', 'Apellido 2', 'Nombres', 'Apellido Final'])

# Ruta de salida
ruta_salida = r'C:\Users\fxb8co\Documents\salida_final.csv'

# Exportamos directamente usando pandas (sin with open)
df.to_csv(ruta_salida, index=False, encoding='utf-8')

print("Archivo CSV guardado con éxito en:", ruta_salida)
