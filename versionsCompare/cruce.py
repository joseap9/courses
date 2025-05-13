import pandas as pd

# 1. Cargar archivo de validación (contratos únicos con monto correcto)
df_val = pd.read_excel('archivo_validacion.xlsx')
df_val['cc'] = df_val['nro_contrato'].astype(str)
df_val['monto'] = pd.to_numeric(df_val['monto'], errors='coerce')

# 2. Cargar archivo grande (todas las hojas combinadas)
archivo_grande = pd.read_excel('archivo_principal.xlsx', sheet_name=None)
df_grande = pd.concat(archivo_grande.values(), ignore_index=True)
df_grande['nro_contrato'] = df_grande['nro_contrato'].astype(str)
df_grande['monto'] = pd.to_numeric(df_grande['monto'], errors='coerce')

# 3. Filtrar filas del archivo grande que coinciden con contratos del archivo de validación
df_cruce = df_grande[df_grande['nro_contrato'].isin(df_val['nro_contrato'])].copy()

# 4. Agregar monto correcto al cruce
df_cruce = df_cruce.merge(df_val, on='nro_contrato', suffixes=('', '_correcto'))

# 5. Validar si el monto coincide
df_cruce['validado'] = df_cruce['monto'] == df_cruce['monto_correcto']

# 6. Crear resumen por contrato
resumen = df_cruce.groupby('nro_contrato').agg(
    total_filas=('validado', 'count'),
    correctos=('validado', 'sum'),
    incorrectos=('validado', lambda x: (~x).sum())
).reset_index()

# 7. Exportar a Excel con múltiples hojas
with pd.ExcelWriter('resultado_validacion_final.xlsx') as writer:
    df_cruce.to_excel(writer, sheet_name='Cruce_Detallado', index=False)
    resumen.to_excel(writer, sheet_name='Resumen_Contratos', index=False)

print("✅ Proceso finalizado. Archivo guardado como 'resultado_validacion_final.xlsx'")