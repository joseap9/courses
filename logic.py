import pandas as pd
from datetime import datetime, timedelta

def process_csv(csv_path):
    try:
        # Leer el CSV con delimitador ;
        df = pd.read_csv(csv_path, delimiter=',', dayfirst=True)

        # Filtrar los registros no completados (Completion Status en blanco o no)
        df_uncomplete = df[df['Completion Status'].isna() | (df['Completion Status'] == "")].copy()

        # Procesar las fechas
        current_date = datetime.now()
        one_week_later = current_date + timedelta(weeks=1)

        # Convertir las fechas
        df_uncomplete['Required Date'] = pd.to_datetime(df_uncomplete['Required Date'], format='%b %d, %Y, %I:%M %p', errors='coerce')

        # Filtrar las fechas
        df_past = df_uncomplete[df_uncomplete['Required Date'] < current_date].copy()
        df_future = df_uncomplete[(df_uncomplete['Required Date'] >= current_date) & (df_uncomplete['Required Date'] <= one_week_later)].copy()

        # Mantener todas las columnas para el primer DataFrame
        df_all = df

        # Seleccionar columnas específicas para los DataFrames de fechas pasadas y futuras
        columns_to_display = ['Item ID', 'Item Title', 'User', 'Username', 'Last Name', 'First Name', 'Completion Status', 'Grade', 'Completion Date']
        df_past = df_past[columns_to_display].groupby('Username').apply(lambda x: x.to_dict('records')).reset_index().rename(columns={0: 'Courses'})
        df_future = df_future[columns_to_display].groupby('Username').apply(lambda x: x.to_dict('records')).reset_index().rename(columns={0: 'Courses'})

        return df_all, df_past, df_future

    except Exception as e:
        return str(e), str(e), str(e)

def friendly_reminder_message(first_name, courses):
    message = f"Hola {first_name},\n\nTe recuerdo que tienes cursos por vencer, favor completar en el plazo:\n"
    message += "\n".join([f"- {course['Item Title']} (ID: {course['Item ID']})" for course in courses])
    return message

def delayed_reminder_message(first_name, courses):
    message = f"Hola {first_name},\n\nJunto con saludarte, te comento que tienes cursos vencidos, necesitamos que los curses a la brevedad en mysuccess:\n"
    message += "\n".join([f"- {course['Item Title']} (ID: {course['Item ID']}, Fecha requerida: {course['Completion Date'].strftime('%Y-%m-%d')})" for course in courses])
    return message
