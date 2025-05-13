import pandas as pd

# ========== RUTAS ==========
ruta_validacion = 'archivo_validacion.xlsx'
ruta_principal = 'archivo_principal.xlsx'

# ========== CARGA VALIDACIÓN ==========
df_val = pd.read_excel(ruta_validacion)
df_val['SRS Contract Number'] = df_val['SRS Contract Number'].astype(str)
df_val['Coupon Amount'] = pd.to_numeric(df_val['Coupon Amount'], errors='coerce')

# ========== CARGA ARCHIVO PRINCIPAL (TODAS LAS HOJAS) ==========
archivo_grande = pd.read_excel(ruta_principal, sheet_name=None)
df_grande = pd.concat(archivo_grande.values(), ignore_index=True)
df_grande['SRS Contract Number'] = df_grande['SRS Contract Number'].astype(str)
df_grande['Coupon Amount'] = pd.to_numeric(df_grande['Coupon Amount'], errors='coerce')

# ========== HOJA 2: CRUCE DETALLADO ==========
df_cruce = df_grande[df_grande['SRS Contract Number'].isin(df_val['SRS Contract Number'])].copy()
df_cruce = df_cruce.merge(df_val, on='SRS Contract Number', suffixes=('', '_correcto'))
df_cruce['validado'] = df_cruce['Coupon Amount'] == df_cruce['Coupon Amount_correcto']

# ========== HOJA 1: VALIDACIÓN BASE ==========
# Contar cuántas veces aparece cada contrato en el archivo principal
conteo_contratos = df_grande['SRS Contract Number'].value_counts().reset_index()
conteo_contratos.columns = ['SRS Contract Number', 'coincidencias contrato']

# Buscar coincidencias exactas de contrato + monto
cruces_exactos = df_grande.merge(df_val, on=['SRS Contract Number', 'Coupon Amount'], how='inner')
primer_monto = cruces_exactos.groupby('SRS Contract Number')['Coupon Amount'].first().reset_index()
primer_monto = primer_monto.rename(columns={'Coupon Amount': 'Coupon Amount (Archivo Principal)'})

# Unir todo al archivo base
df_val_base = df_val.copy()
df_val_base = df_val_base.merge(primer_monto, on='SRS Contract Number', how='left')
df_val_base = df_val_base.merge(conteo_contratos, on='SRS Contract Number', how='left')

# Reemplazar NaN por "NO ENCONTRADO" y 0
df_val_base['Coupon Amount (Archivo Principal)'] = df_val_base['Coupon Amount (Archivo Principal)'].fillna('NO ENCONTRADO')
df_val_base['coincidencias contrato'] = df_val_base['coincidencias contrato'].fillna(0).astype(int)

# Calcular validación final
df_val_base['validado'] = df_val_base['Coupon Amount'] == df_val_base['Coupon Amount (Archivo Principal)']

# ========== HOJA 3: RESUMEN CONTRATOS ==========
resumen = df_cruce.groupby('SRS Contract Number').agg(
    total_filas=('validado', 'count'),
    correctos=('validado', 'sum'),
    incorrectos=('validado', lambda x: (~x).sum())
).reset_index()

# ========== EXPORTAR RESULTADO A EXCEL ==========
with pd.ExcelWriter('resultado_validacion_final.xlsx') as writer:
    df_val_base.to_excel(writer, sheet_name='Validación Base', index=False)     # Hoja 1
    df_cruce.to_excel(writer, sheet_name='Cruce Detallado', index=False)        # Hoja 2
    resumen.to_excel(writer, sheet_name='Resumen Contratos', index=False)       # Hoja 3

print("✅ Proceso finalizado. Archivo generado: resultado_validacion_final.xlsx")
