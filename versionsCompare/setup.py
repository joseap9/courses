from distutils.core import setup
import py2exe
import sys
import os

sys.argv.append('py2exe')

script_path = os.path.join('src', 'uidemo.py')

setup(
    options={
        'py2exe': {
            'packages': ['sys', 'os', 'PyQt5', 'fitz', 'tempfile'],
        }
    },
    windows=[{
        'script': script_path,
    }],
)
