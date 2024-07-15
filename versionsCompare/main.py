from PyQt5.QtWidgets import QApplication
from ui import MainWindow

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()