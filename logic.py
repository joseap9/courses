import pandas as pd
from datetime import datetime, timedelta

def process_csv(csv_path):
    try:
        # Leer el CSV con delimitador ;
        df = pd.read_csv(csv_path, delimiter=';', dayfirst=True)
        
        # Depuración: Imprimir las columnas del DataFrame
        print("Columnas del DataFrame:", df.columns)

        df_uncomplete = df[df['status'] == 'uncomplete']

        current_date = datetime.now().date()
        one_week_later = current_date + timedelta(weeks=1)

        df_uncomplete['fecha'] = pd.to_datetime(df_uncomplete['fecha'], format='%d-%b-%y').dt.date

        df_past = df_uncomplete[df_uncomplete['fecha'] < current_date]
        df_future = df_uncomplete[(df_uncomplete['fecha'] >= current_date) & (df_uncomplete['fecha'] <= one_week_later)]

        df_past = df_past[['nombre', 'curso', 'fecha']]
        df_future = df_future[['nombre', 'curso', 'fecha']]

        return df_past, df_future

    except Exception as e:
        return str(e), str(e)
