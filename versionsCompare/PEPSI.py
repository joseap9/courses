import pandas as pd
import re

ruta_archivo = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENST2025010603.txt'

# Leer líneas
with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros = []

for linea in lineas:
    # Separar por 2 o más espacios
    partes = re.split(r'\s{2,}', linea.strip())
    if len(partes) < 12:
        print(f"Línea con datos insuficientes: {linea}")
        continue

    # Procesar RUT
    rut_num = partes[0]
    if not rut_num.isdigit() or len(rut_num) < 2:
        print(f"RUT inválido: {rut_num}")
        continue
    rut = rut_num[:-1] + '-' + rut_num[-1]

    # Extraer fecha + tipo movimiento (último campo)
    fecha_tipo = partes[-1]
    if re.match(r'\d{4}/\d{2}/\d{2}\d{2}', fecha_tipo):
        fecha = fecha_tipo[:-2]
        tipo_mov = fecha_tipo[-2:]
    else:
        print(f"Fecha+tipo inválidos: {fecha_tipo}")
        fecha = ""
        tipo_mov = ""

    # Armar fila
    fila = [
        rut,                      # 1. RUT formateado
        partes[1],                # 2. Apellido paterno
        partes[2],                # 3. Apellido materno
        f"{partes[1]} {partes[2]}",  # 4. Apellidos
        partes[3],                # 5. Nombres
        partes[4],                # 6. Apellido paterno (2)
        partes[5],                # 7. Apellido materno (2)
        partes[6],                # 8. Nombres (2)
        partes[7],                # 9. Institución
        partes[8],                # 10. Cargo
        fecha,                    # 11. Fecha
        tipo_mov                  # 12. Tipo Movimiento
    ]
    registros.append(fila)

# Crear DataFrame
df = pd.DataFrame(registros, columns=[
    'RUT', 'Apellido Paterno', 'Apellido Materno', 'Apellidos',
    'Nombres', 'Apellido Paterno (2)', 'Apellido Materno (2)', 'Nombres (2)',
    'Institución', 'Cargo', 'Fecha', 'Tipo Movimiento'
])

# Guardar CSV
ruta_salida = r'C:\Users\fxb8co\Documents\salida_final.csv'
df.to_csv(ruta_salida, index=False, encoding='utf-8-sig')

print("✅ Archivo CSV generado correctamente en:", ruta_salida)
