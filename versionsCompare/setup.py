from distutils.core import setup
import py2exe
import sys
import os

sys.argv.append('py2exe')

script_path = os.path.join('src', 'uidemo.py')

setup(
    options={
        'py2exe': {
            'includes': ['PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'fitz', 'tempfile'],
            'dll_excludes': ['MSVCP90.dll'],  # Excluir MSVC DLLs si es necesario
            'excludes': ['tkinter'],  # Excluir tkinter si no se usa
        }
    },
    windows=[{
        'script': script_path,
    }],
)
