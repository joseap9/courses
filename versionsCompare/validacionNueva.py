import pandas as pd

# ========== RUTAS ==========
ruta_validacion = r"C:\Users\fxb8co\Documents\archivo_validacion_con_opciones.xlsx"
ruta_principal = r"C:\Users\fxb8co\Documents\archivo_principal.xlsx"

# ========== CARGA VALIDACIÓN ==========
df_val = pd.read_excel(ruta_validacion)
df_val['SRS Contract Number'] = df_val['SRS Contract Number'].astype(str)

# Convertir fechas y montos
for i in range(1, 5):
    df_val[f'Payment Date (Expiration Date) {i}'] = pd.to_datetime(
        df_val[f'Payment Date (Expiration Date) {i}'], dayfirst=True, errors='coerce'
    )
    df_val[f'Coupon Amount {i}'] = pd.to_numeric(df_val[f'Coupon Amount {i}'], errors='coerce')

# ========== CARGA ARCHIVO PRINCIPAL ==========
archivo_grande = pd.read_excel(ruta_principal, sheet_name=None)
df_grande = pd.concat(archivo_grande.values(), ignore_index=True)

df_grande = df_grande[df_grande['Payslip_Type'] == 'Termination'].copy()
df_grande['SRS Contract Number'] = df_grande['SRS Contract Number'].astype(str)
df_grande['Coupon Amount'] = pd.to_numeric(df_grande['Coupon Amount'], errors='coerce')
df_grande['Payment Date (Expiration Date)'] = pd.to_datetime(
    df_grande['Payment Date (Expiration Date)'], dayfirst=True, errors='coerce'
)

# ========== VALIDACIÓN POR OPCIONES ==========
for i in range(1, 5):
    col_monto = f'Coupon Amount {i}'
    col_fecha = f'Payment Date (Expiration Date) {i}'
    nombre_columna = f'Coincide Opción {i}'

    df_val[nombre_columna] = df_val.apply(
        lambda row: any(
            (df_grande['SRS Contract Number'] == row['SRS Contract Number']) &
            (df_grande['Coupon Amount'] == row[col_monto]) &
            (df_grande['Payment Date (Expiration Date)'] == row[col_fecha])
        ),
        axis=1
    )

# ========== COLUMNA DE VALIDADO TOTAL ==========
df_val['Validado Total'] = df_val[[f'Coincide Opción {i}' for i in range(1, 5)]].any(axis=1)

# ========== PRIMERA OPCIÓN COINCIDENTE ==========
def obtener_primera_opcion(row):
    for i in range(1, 5):
        if row[f'Coincide Opción {i}']:
            return f'Opción {i}'
    return "NO"

df_val['Primera Opción Coincidente'] = df_val.apply(obtener_primera_opcion, axis=1)

# ========== EXPORTAR ==========
with pd.ExcelWriter('resultado_validacion_opciones.xlsx') as writer:
    df_val.to_excel(writer, sheet_name='Validación Opciones', index=False)

print("✅ Proceso completado. Archivo generado: resultado_validacion_opciones.xlsx")
