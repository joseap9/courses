import pandas as pd

# ========== RUTAS ==========
ruta_validacion = 'archivo_validacion.xlsx'
ruta_principal = 'archivo_principal.xlsx'

# ========== CARGA VALIDACIÓN ==========
df_val = pd.read_excel(ruta_validacion)
df_val['SRS Contract Number'] = df_val['SRS Contract Number'].astype(str)
df_val['Coupon Amount'] = pd.to_numeric(df_val['Coupon Amount'], errors='coerce')

# ========== CARGA ARCHIVO PRINCIPAL (todas las hojas) ==========
archivo_grande = pd.read_excel(ruta_principal, sheet_name=None)
df_list = []

for nombre_hoja, df_hoja in archivo_grande.items():
    # Limpieza de nombres de columnas
    df_hoja.columns = df_hoja.columns.str.strip()
    df_hoja.columns = df_hoja.columns.str.replace('\n', ' ', regex=True)
    df_hoja.columns = df_hoja.columns.str.replace(',', '', regex=False)

    # Normalizar columnas clave
    df_hoja['SRS Contract Number'] = df_hoja['SRS Contract Number'].astype(str)
    df_hoja['Coupon Amount'] = pd.to_numeric(df_hoja['Coupon Amount'], errors='coerce')
    df_list.append(df_hoja)

df_grande = pd.concat(df_list, ignore_index=True)

# ========== FILTRAR COINCIDENCIAS ==========
df_cruce = df_grande[df_grande['SRS Contract Number'].isin(df_val['SRS Contract Number'])].copy()

# ========== MERGE PARA VALIDACIÓN ==========
df_cruce = df_cruce.merge(df_val, on='SRS Contract Number', suffixes=('', '_correcto'))
df_cruce['validado'] = df_cruce['Coupon Amount'] == df_cruce['Coupon Amount_correcto']

# ========== HOJA 1: Validación Base ==========
df_val_base = df_val.copy()
monto_real = df_cruce.groupby('SRS Contract Number')['Coupon Amount'].first().reset_index()
df_val_base = df_val_base.merge(monto_real, on='SRS Contract Number', how='left')
df_val_base['validado'] = df_val_base['Coupon Amount'] == df_val_base['Coupon Amount_y']
df_val_base = df_val_base.rename(columns={
    'Coupon Amount_y': 'Coupon Amount (Archivo Principal)'
})

# ========== HOJA 3: Resumen Contratos ==========
resumen = df_cruce.groupby('SRS Contract Number').agg(
    total_filas=('validado', 'count'),
    correctos=('validado', 'sum'),
    incorrectos=('validado', lambda x: (~x).sum())
).reset_index()

# ========== EXPORTAR ARCHIVO FINAL ==========
with pd.ExcelWriter('resultado_validacion_final.xlsx') as writer:
    df_val_base.to_excel(writer, sheet_name='Validación Base', index=False)
    df_cruce.to_excel(writer, sheet_name='Cruce Detallado', index=False)
    resumen.to_excel(writer, sheet_name='Resumen Contratos', index=False)

print("✅ Proceso finalizado. Archivo generado: resultado_validacion_final.xlsx")
