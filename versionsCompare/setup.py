from cx_Freeze import setup, Executable
import sys

# Incluir archivos adicionales (si tienes archivos como imágenes, etc.)
files = ['app.log']

# Construcción del ejecutable
setup(
    name='PDFComparer',
    version='1.0',
    description='PDF Comparison Tool',
    options={
        'build_exe': {
            'include_files': files,
            'packages': ['os', 'sys', 'PyQt5', 'fitz', 'tempfile']
        }
    },
    executables=[Executable('tu_script.py', base='Win32GUI' if sys.platform == 'win32' else None)]
)
