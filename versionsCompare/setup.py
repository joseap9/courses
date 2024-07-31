import sys
from cx_Freeze import setup, Executable
import os

# Configurar las opciones de build_exe
build_exe_options = {
    "packages": ["os", "sys", "PyQt5", "tempfile", "pymupdf"],
    "includes": ["PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui"],
    "excludes": ["tkinter"],  # Excluir tkinter si no se usa
    "include_files": [
        os.path.join('venv', 'Lib', 'site-packages', 'PyQt5'),
        os.path.join('venv', 'Lib', 'site-packages', 'pymupdf'),
    ],
    "path": sys.path + [os.path.join('venv', 'Lib', 'site-packages')],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Esto asegura que no se abra una consola de comandos

setup(
    name="PDFComparer",
    version="1.0",
    description="A simple PDF comparison tool",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
