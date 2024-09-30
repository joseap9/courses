Requisitos del Sistema y Dependencias
Dependencias necesarias:
Para ejecutar este proyecto, se deben instalar las siguientes dependencias:

Python 3.x
PyQt5: Para la interfaz gráfica de usuario.
fitz (PyMuPDF): Para manejar y comparar PDFs.
pandas: Para exportar las diferencias en un archivo Excel.
cx_Freeze: Para crear un ejecutable autónomo.
Puedes instalar las dependencias con el siguiente comando:

bash
Copiar código
pip install PyQt5 fitz pymupdf pandas cx_Freeze
Tabla de Funciones
Función	Descripción
__init__()	Inicializa la ventana principal y los layouts de la interfaz gráfica.
init_left_section()	Configura la sección izquierda que permite seleccionar los PDFs y navegar entre las páginas.
init_right_section()	Configura la sección derecha con las opciones para etiquetar diferencias y navegar entre ellas.
sync_scroll()	Sincroniza el desplazamiento vertical entre los dos visores de PDF.
load_first_pdf()	Permite al usuario seleccionar el primer archivo PDF y lo carga en la interfaz.
load_second_pdf()	Permite al usuario seleccionar el segundo archivo PDF y lo carga en la interfaz.
reset_comparison()	Reinicia las variables y la interfaz para comenzar una nueva comparación de PDFs.
extract_text_and_positions()	Extrae el texto y las posiciones de las palabras de un PDF en todas sus páginas.
compare_pdfs()	Compara los textos extraídos de ambos PDFs y resalta las diferencias encontradas.
highlight_differences()	Resalta las diferencias encontradas entre los PDFs, excluyendo ciertas áreas (como los márgenes superior e inferior).
load_page_pair()	Carga y muestra una página de ambos PDFs, resaltando las diferencias.
display_pdfs()	Muestra las páginas de los PDFs en el área de visualización.
highlight_current_difference()	Resalta la diferencia actual en rojo para que sea fácil de identificar.
update_navigation_buttons()	Actualiza el estado de los botones de navegación (habilita o deshabilita según la página y diferencia actual).
update_difference_labels()	Actualiza la etiqueta que muestra la página y la diferencia actual.
toggle_other_input()	Muestra o oculta el campo de entrada adicional cuando el usuario selecciona la opción "Otro".
next_difference()	Navega a la siguiente diferencia y, si es necesario, cambia de página o muestra el resumen.
prev_difference()	Navega a la diferencia anterior si es posible.
next_page()	Navega a la siguiente página de los PDFs, validando que todas las diferencias de la página actual hayan sido etiquetadas.
prev_page()	Navega a la página anterior de los PDFs.
save_current_label()	Guarda la etiqueta seleccionada (Aplica, No Aplica, Otro) para la diferencia actual.
show_summary()	Muestra un resumen de las diferencias encontradas y permite descargar un archivo Excel con los resultados.
download_excel()	Descarga las diferencias etiquetadas en un archivo Excel, solicitando primero el nombre del responsable.
reset_all()	Reinicia todas las variables y limpia la interfaz gráfica para realizar una nueva comparación de PDFs.
Explicación de Funciones Importantes
1. highlight_differences()
Esta función se encarga de resaltar las diferencias encontradas entre dos PDFs. Se basa en las palabras extraídas de cada PDF y compara sus posiciones en la página. Si una palabra está presente en un PDF pero no en el otro, se marca como una diferencia. Para evitar resaltados innecesarios en los márgenes, la función excluye las palabras que están demasiado cerca del borde superior e inferior de la página.

Parámetros:

doc: El documento PDF donde se aplicarán los resaltados.
words1: Las palabras extraídas del primer PDF.
words2: Las palabras extraídas del segundo PDF.
page_num: El número de página que se está procesando.
Funcionalidad:

Compara las palabras de la página actual en ambos PDFs.
Resalta las diferencias en amarillo, y si hay varias diferencias separadas por un pequeño número de palabras iguales, las agrupa.
Excluye palabras que están demasiado cerca del inicio o final de la página para evitar errores en el resaltado.
2. highlight_current_difference()
Esta función se utiliza para resaltar la diferencia actual en rojo, facilitando la navegación entre las diferencias. Tras llamar a highlight_differences() para generar los resaltados en amarillo, esta función busca la diferencia actual y la resalta en rojo.

Parámetros: Ninguno.

Funcionalidad:

Resalta la diferencia actual (en la posición del índice actual de diferencias) en rojo.
Vuelve a generar las imágenes de las páginas de los PDFs para mostrar los nuevos resaltados.
Actualiza los cuadros de texto que muestran las palabras diferentes de ambos PDFs.
Sección de Ejecutable en Producción
Para generar un ejecutable autónomo que no requiera instalación de Python ni de las dependencias, utilizamos cx_Freeze. A continuación se muestra el archivo setup.py que se usa para crear el ejecutable.

Contenido del setup.py:
python
Copiar código
import sys
from cx_Freeze import setup, Executable
import os

# Opciones de construcción para el ejecutable
build_exe_options = {
    "packages": ["os", "sys", "PyQt5", "tempfile", "fitz", "traceback", "pandas"],  # Incluye pandas para exportar a Excel
    "includes": ["PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui", "lief", "setuptools", "wheel", "pkg_resources"],
    "excludes": ["tkinter"],
    "include_files": [
        'app.log',
        (os.path.join('venv', 'Lib', 'site-packages', 'PyQt5'), 'PyQt5'),
        (os.path.join('venv', 'Lib', 'site-packages', 'pymupdf'), 'pymupdf'),
        (os.path.join('venv', 'Lib', 'site-packages', 'fitz'), 'fitz'),
        (os.path.join('venv', 'Lib', 'site-packages', 'lief'), 'lief'),
        (os.path.join('venv', 'Lib', 'site-packages', 'setuptools'), 'setuptools'),
        (os.path.join('venv', 'Lib', 'site-packages', 'wheel'), 'wheel'),
        (os.path.join('venv', 'Lib', 'site-packages', 'pkg_resources'), 'pkg_resources')
    ],
    "path": sys.path + [os.path.join('venv', 'Lib', 'site-packages')],
}

# Determina la base del ejecutable según el sistema operativo
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Configuración del setup para cx_Freeze
setup(
    name="PDFComparer",
    version="1.0",
    description="A simple PDF comparison tool",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],  # "main.py" es el archivo principal
)
Instrucciones para la creación del ejecutable:
Asegúrate de tener instaladas las dependencias mencionadas en la sección de dependencias, así como cx_Freeze:

bash
Copiar código
pip install cx_Freeze
Crea el ejecutable ejecutando el siguiente comando en la terminal desde el directorio donde se encuentra el archivo setup.py:

bash
Copiar código
python setup.py build
Esto generará una carpeta build con un ejecutable que puedes distribuir y ejecutar sin necesidad de tener Python instalado en el sistema.

Configuración de archivos adicionales:
Archivos incluidos: El archivo de registro app.log y los paquetes necesarios de PyQt5, fitz, y pandas se incluyen automáticamente en el ejecutable.
Exclusiones: Se excluye tkinter, ya que no se utiliza en este proyecto.
Con este archivo setup.py, puedes empaquetar la aplicación como un ejecutable y distribuirla fácilmente, incluyendo todas las dependencias necesarias en el entorno.