import sys
from PyQt5.QtWidgets import QApplication
from ui import PDFComparer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())