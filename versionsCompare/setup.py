from distutils.core import setup
import py2exe
import sys
import os

sys.argv.append('py2exe')

script_path = os.path.join('src', 'uidemo.py')

setup(
    options={
        'py2exe': {
            'includes': ['sip', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui'],
            'packages': ['os', 'sys', 'fitz', 'tempfile'],
        }
    },
    windows=[{
        'script': script_path,
    }],
)
