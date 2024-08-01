import sys
from cx_Freeze import setup, Executable
import os

build_exe_options = {
    "packages": ["os", "sys", "PyQt5", "tempfile", "fitz", "traceback"],
    "includes": ["PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui"],
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

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="PDFComparer",
    version="1.0",
    description="A simple PDF comparison tool",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
