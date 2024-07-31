from distutils.core import setup
import py2exe
import sys

sys.argv.append('py2exe')

# setup function to specify the details of the executable
setup(
    options={
        'py2exe': {
            'packages': ['sys', 'os', 'PyQt5', 'fitz', 'tempfile'],
        }
    },
    windows=[{
        'script': 'uidemo.py',
        'icon_resources': [(1, 'icon.ico')]  # opcional, si tienes un icono para tu app
    }],
)