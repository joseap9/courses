def format_series(series):
    # Dividir la serie en líneas individuales
    numbers = series.split('\n')
    # Filtrar líneas vacías (en caso de que existan)
    numbers = [num for num in numbers if num.strip()]
    # Formatear cada número entre comillas simples
    formatted_numbers = [f"'{num.strip()}'" for num in numbers]
    # Unir todos los números formateados con comas y encerrarlos entre paréntesis
    result = f"({', '.join(formatted_numbers)})"
    return result

# Ejemplo de uso
input_series = """123
345
678"""

formatted_result = format_series(input_series)
print(formatted_result)