import pandas as pd

# ========== RUTAS ==========
ruta_validacion = r"C:\Users\\Documents\prepagos 14-05.xlsx"
ruta_principal = r"C:\Users\\Documents\Copy of SRS Payment Coupons Delivery Status Report - 2025-05-13132038.036.xlsx"

# ========== CARGA VALIDACIÓN ==========
df_val = pd.read_excel(ruta_validacion)
df_val['SRS Contract Number'] = df_val['SRS Contract Number'].astype(str)
df_val['Coupon Amount'] = pd.to_numeric(df_val['Coupon Amount'], errors='coerce')

# Convertir fechas (formato DD/MM/AAAA)
df_val['Payment Date (Expiration Date)'] = pd.to_datetime(
    df_val['Payment Date (Expiration Date)'], dayfirst=True, errors='coerce'
)

# ========== CARGA ARCHIVO PRINCIPAL ==========
archivo_grande = pd.read_excel(ruta_principal, sheet_name=None)
df_grande = pd.concat(archivo_grande.values(), ignore_index=True)

# Filtrar por tipo "Termination"
df_grande = df_grande[df_grande['Payslip_Type'] == 'Termination'].copy()

df_grande['SRS Contract Number'] = df_grande['SRS Contract Number'].astype(str)
df_grande['Coupon Amount'] = pd.to_numeric(df_grande['Coupon Amount'], errors='coerce')

# Convertir fechas con dayfirst
df_grande['Payment Date (Expiration Date)'] = pd.to_datetime(
    df_grande['Payment Date (Expiration Date)'], dayfirst=True, errors='coerce'
)

# ========== HOJA 2: CRUCE DETALLADO ==========
df_cruce = df_grande[df_grande['SRS Contract Number'].isin(df_val['SRS Contract Number'])].copy()
df_cruce = df_cruce.merge(df_val, on='SRS Contract Number', suffixes=('', '_validacion'))
df_cruce['validado_monto'] = df_cruce['Coupon Amount'] == df_cruce['Coupon Amount_validacion']
df_cruce['validado_fecha'] = df_cruce['Payment Date (Expiration Date)'] == df_cruce['Payment Date (Expiration Date)_validacion']
df_cruce['validado_total'] = df_cruce['validado_monto'] & df_cruce['validado_fecha']

# ========== HOJA 1: VALIDACIÓN BASE ==========
conteo_contratos = df_grande['SRS Contract Number'].value_counts().reset_index()
conteo_contratos.columns = ['SRS Contract Number', 'coincidencias contrato']

# Coincidencias exactas de contrato + monto + fecha
cruces_exactos = df_grande.merge(
    df_val,
    on=['SRS Contract Number', 'Coupon Amount', 'Payment Date (Expiration Date)'],
    how='inner'
)
primer_monto_fecha = cruces_exactos.groupby('SRS Contract Number')[['Coupon Amount', 'Payment Date (Expiration Date)']].first().reset_index()
primer_monto_fecha = primer_monto_fecha.rename(columns={
    'Coupon Amount': 'Coupon Amount (Archivo Principal)',
    'Payment Date (Expiration Date)': 'Fecha (Archivo Principal)'
})

# Unir todo al archivo base
df_val_base = df_val.copy()
df_val_base = df_val_base.merge(primer_monto_fecha, on='SRS Contract Number', how='left')
df_val_base = df_val_base.merge(conteo_contratos, on='SRS Contract Number', how='left')

# Rellenar faltantes
df_val_base['Coupon Amount (Archivo Principal)'] = df_val_base['Coupon Amount (Archivo Principal)'].fillna("NO ENCONTRADO")
df_val_base['Fecha (Archivo Principal)'] = pd.to_datetime(df_val_base['Fecha (Archivo Principal)'], errors='coerce')
df_val_base['coincidencias contrato'] = df_val_base['coincidencias contrato'].fillna(0).astype(int)

# Validaciones
df_val_base['validado_monto'] = df_val_base['Coupon Amount'] == df_val_base['Coupon Amount (Archivo Principal)']
df_val_base['validado_fecha'] = df_val_base['Payment Date (Expiration Date)'] == df_val_base['Fecha (Archivo Principal)']
df_val_base['validado_total'] = df_val_base['validado_monto'] & df_val_base['validado_fecha']

# ========== EXPORTAR A EXCEL ==========
with pd.ExcelWriter('resultado_validacion_final_ajusta.xlsx') as writer:
    df_val_base.to_excel(writer, sheet_name='Validación Base', index=False)
    df_cruce.to_excel(writer, sheet_name='Cruce Detallado', index=False)

print("✅ Proceso finalizado. Archivo generado: resultado_validacion_final_ajusta.xlsx")
