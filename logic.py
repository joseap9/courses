import pandas as pd
from datetime import datetime, timedelta

def process_csv(csv_path):
    try:
        # Leer el CSV con delimitador ;
        df = pd.read_csv(csv_path, delimiter=';', dayfirst=True)
        
        # Depuración: Imprimir las columnas del DataFrame
        print("Columnas del DataFrame:", df.columns)

        # Filtrar los registros no completados (Completion Status en blanco)
        df_uncomplete = df[df['Completion Status'].isna()].copy()

        # Procesar las fechas
        current_date = datetime.now()
        one_week_later = current_date + timedelta(weeks=1)

        # Convertir las fechas
        df_uncomplete['Completion Date'] = pd.to_datetime(df_uncomplete['Completion Date'], format='%b %d, %Y, %I:%M %p', errors='coerce')

        # Filtrar las fechas
        df_past = df_uncomplete[df_uncomplete['Completion Date'] < current_date].copy()
        df_future = df_uncomplete[(df_uncomplete['Completion Date'] >= current_date) & (df_uncomplete['Completion Date'] <= one_week_later)].copy()

        # Mantener todas las columnas para el primer DataFrame
        df_all = df_uncomplete

        # Seleccionar columnas específicas para los DataFrames de fechas pasadas y futuras
        columns_to_display = ['Item ID', 'Item Title', 'User', 'Username', 'Last Name', 'First Name', 'Completion Status', 'Grade', 'Completion Date']
        df_past = df_past[columns_to_display]
        df_future = df_future[columns_to_display]

        return df_all, df_past, df_future

    except Exception as e:
        return str(e), str(e), str(e)