import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        # Layout principal
        self.main_layout = QVBoxLayout()

        # Sección de botones para cargar PDFs
        self.button_layout = QHBoxLayout()

        self.load_pdf1_button = QPushButton("Load First PDF", self)
        self.load_pdf1_button.clicked.connect(self.load_first_pdf)
        self.button_layout.addWidget(self.load_pdf1_button)

        self.load_pdf2_button = QPushButton("Load Second PDF", self)
        self.load_pdf2_button.clicked.connect(self.load_second_pdf)
        self.button_layout.addWidget(self.load_pdf2_button)

        self.main_layout.addLayout(self.button_layout)

        # Sección del visualizador de PDF
        self.pdf_view = QWebEngineView(self)
        self.main_layout.addWidget(self.pdf_view)

        # Sección de navegación entre páginas y diferencias
        self.navigation_layout = QHBoxLayout()

        self.prev_page_button = QPushButton("Previous Page", self)
        self.prev_page_button.clicked.connect(self.prev_page)
        self.navigation_layout.addWidget(self.prev_page_button)

        self.next_page_button = QPushButton("Next Page", self)
        self.next_page_button.clicked.connect(self.next_page)
        self.navigation_layout.addWidget(self.next_page_button)

        self.prev_diff_button = QPushButton("Previous Difference", self)
        self.prev_diff_button.clicked.connect(self.prev_difference)
        self.navigation_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Difference", self)
        self.next_diff_button.clicked.connect(self.next_difference)
        self.navigation_layout.addWidget(self.next_diff_button)

        self.main_layout.addLayout(self.navigation_layout)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Inicialización de variables
        self.pdf1_path = None
        self.pdf2_path = None
        self.current_page = 0
        self.total_pages = 0
        self.differences = []
        self.current_difference_index = -1

    def load_first_pdf(self):
        self.pdf1_path, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf)")
        if self.pdf1_path:
            self.current_page = 0
            self.pdf_view.setUrl(QUrl.fromLocalFile(self.pdf1_path))
            self.extract_differences()

    def load_second_pdf(self):
        self.pdf2_path, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf)")
        if self.pdf2_path:
            self.current_page = 0
            self.pdf_view.setUrl(QUrl.fromLocalFile(self.pdf2_path))
            self.extract_differences()

    def extract_differences(self):
        if self.pdf1_path and self.pdf2_path:
            doc1 = fitz.open(self.pdf1_path)
            doc2 = fitz.open(self.pdf2_path)
            self.total_pages = min(len(doc1), len(doc2))

            # Lógica simplificada para extraer diferencias
            self.differences = []
            for i in range(self.total_pages):
                text1 = doc1[i].get_text()
                text2 = doc2[i].get_text()
                if text1 != text2:
                    self.differences.append(i)

            if self.differences:
                self.current_difference_index = 0
                self.go_to_difference()

    def go_to_difference(self):
        if self.differences:
            diff_page = self.differences[self.current_difference_index]
            self.current_page = diff_page
            self.pdf_view.setUrl(QUrl.fromLocalFile(self.pdf1_path if self.current_difference_index % 2 == 0 else self.pdf2_path))
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_page_button.setEnabled(self.current_page > 0)
        self.next_page_button.setEnabled(self.current_page < self.total_pages - 1)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.pdf_view.setUrl(QUrl.fromLocalFile(self.pdf1_path if self.current_page % 2 == 0 else self.pdf2_path))

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.pdf_view.setUrl(QUrl.fromLocalFile(self.pdf1_path if self.current_page % 2 == 0 else self.pdf2_path))

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.current_difference_index += 1
            self.go_to_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.go_to_difference()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
