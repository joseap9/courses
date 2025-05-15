import pandas as pd

# ========== RUTAS ==========
ruta_validacion = r"C:\Users\fxb8co\Documents\prepagos 14-05.xlsx"
ruta_principal = r"C:\Users\fxb8co\Documents\Copy of SRS Payment Coupons Delivery Status Report - 2025-05-13132038.036.xlsx"

# ========== CARGA VALIDACIÓN ==========
df_val = pd.read_excel(ruta_validacion)
df_val['SRS Contract Number'] = df_val['SRS Contract Number'].astype(str)
df_val['Coupon Amount'] = pd.to_numeric(df_val['Coupon Amount'], errors='coerce')
df_val['Payment Date (Expiration Date)'] = pd.to_datetime(
    df_val['Payment Date (Expiration Date)'], dayfirst=True, errors='coerce'
)

# ========== CARGA ARCHIVO PRINCIPAL ==========
archivo_grande = pd.read_excel(ruta_principal, sheet_name=None)
df_grande = pd.concat(archivo_grande.values(), ignore_index=True)
df_grande = df_grande[df_grande['Payslip_Type'] == 'Termination'].copy()

df_grande['SRS Contract Number'] = df_grande['SRS Contract Number'].astype(str)
df_grande['Coupon Amount'] = pd.to_numeric(df_grande['Coupon Amount'], errors='coerce')
df_grande['Payment Date (Expiration Date)'] = pd.to_datetime(
    df_grande['Payment Date (Expiration Date)'], dayfirst=True, errors='coerce'
)

# ========== CRUCE DETALLADO ==========
df_cruce = df_grande[df_grande['SRS Contract Number'].isin(df_val['SRS Contract Number'])].copy()
df_cruce = df_cruce.merge(df_val, on='SRS Contract Number', suffixes=('', '_validacion'))

df_cruce['validado_monto'] = df_cruce['Coupon Amount'] == df_cruce['Coupon Amount_validacion']
df_cruce['validado_fecha'] = df_cruce['Payment Date (Expiration Date)'] == df_cruce['Payment Date (Expiration Date)_validacion']
df_cruce['Monto y Fecha coincide en la misma fila'] = df_cruce['validado_monto'] & df_cruce['validado_fecha']

# ========== VALIDACIÓN BASE ==========
df_val_base = df_val.copy()

# Validar si existe coincidencia de contrato + monto
val_monto = df_grande[['SRS Contract Number', 'Coupon Amount']].drop_duplicates()
val_monto['validado_monto'] = True
df_val_base = df_val_base.merge(val_monto, on=['SRS Contract Number', 'Coupon Amount'], how='left')

# Validar si existe coincidencia de contrato + fecha
val_fecha = df_grande[['SRS Contract Number', 'Payment Date (Expiration Date)']].drop_duplicates()
val_fecha['validado_fecha'] = True
df_val_base = df_val_base.merge(val_fecha, on=['SRS Contract Number', 'Payment Date (Expiration Date)'], how='left')

# Buscar coincidencia exacta contrato + monto + fecha
triple_match = df_grande.merge(
    df_val,
    on=['SRS Contract Number', 'Coupon Amount', 'Payment Date (Expiration Date)'],
    how='inner'
)
match_data = triple_match.groupby('SRS Contract Number').first().reset_index()
match_data = match_data[['SRS Contract Number', 'Coupon Amount', 'Payment Date (Expiration Date)']]
match_data = match_data.rename(columns={
    'Coupon Amount': 'Monto en Archivo Principal',
    'Payment Date (Expiration Date)': 'Fecha en Archivo Principal'
})

df_val_base = df_val_base.merge(match_data, on='SRS Contract Number', how='left')

# Validaciones
df_val_base['validado_monto'] = df_val_base['validado_monto'].fillna(False).astype(bool)
df_val_base['validado_fecha'] = df_val_base['validado_fecha'].fillna(False).astype(bool)
df_val_base['Monto y Fecha coincide en la misma fila'] = ~df_val_base['Monto en Archivo Principal'].isna()

# Conteo de coincidencias por contrato
conteo_contratos = df_grande['SRS Contract Number'].value_counts().reset_index()
conteo_contratos.columns = ['SRS Contract Number', 'coincidencias contrato']
df_val_base = df_val_base.merge(conteo_contratos, on='SRS Contract Number', how='left')
df_val_base['coincidencias contrato'] = df_val_base['coincidencias contrato'].fillna(0).astype(int)

# ========== EXPORTAR A EXCEL ==========
with pd.ExcelWriter('VALIDACION FINAL OK.xlsx') as writer:
    df_val_base.to_excel(writer, sheet_name='Validación Base', index=False)
    df_cruce.to_excel(writer, sheet_name='Cruce Detallado', index=False)

print("✅ Proceso finalizado. Archivo generado: resultado_validacion_final_ajusta.xlsx")
