import sys
from cx_Freeze import setup, Executable

# Incluir las librerías necesarias
build_exe_options = {
    "packages": ["os", "sys", "PyQt5", "fitz", "tempfile"],
    "includes": ["PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui"],
    "excludes": ["tkinter"],  # Excluir tkinter si no se usa
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Esto asegura que no se abra una consola de comandos

setup(
    name="PDFComparer",
    version="1.0",
    description="A simple PDF comparison tool",
    options={"build_exe": build_exe_options},
    executables=[Executable("src/uidemo.py", base=base)],
)
