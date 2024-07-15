from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTextEdit
import fitz
import difflib

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Comparator")
        self.setGeometry(100, 100, 1200, 800)

        self.layout = QVBoxLayout()

        self.label = QLabel("Seleccione dos archivos PDF para comparar")
        self.layout.addWidget(self.label)

        self.button = QPushButton("Seleccionar archivos PDF")
        self.button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.button)

        self.result_label = QLabel("")
        self.layout.addWidget(self.result_label)

        self.pdf1_text = QTextEdit()
        self.pdf1_text.setReadOnly(True)
        self.layout.addWidget(self.pdf1_text)

        self.pdf2_text = QTextEdit()
        self.pdf2_text.setReadOnly(True)
        self.layout.addWidget(self.pdf2_text)

        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.layout.addWidget(self.diff_text)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos PDF", "", "Archivos PDF (*.pdf)", options=options)
        if len(file_names) == 2:
            pdf1_text = self.extract_text_from_pdf(file_names[0])
            pdf2_text = self.extract_text_from_pdf(file_names[1])
            self.pdf1_text.setPlainText(pdf1_text)
            self.pdf2_text.setPlainText(pdf2_text)
            diff_text = self.get_diff(pdf1_text, pdf2_text)
            self.diff_text.setPlainText(diff_text)
        else:
            self.result_label.setText("Por favor seleccione exactamente dos archivos PDF.")

    def extract_text_from_pdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def get_diff(self, text1, text2):
        diff = difflib.ndiff(text1.splitlines(), text2.splitlines())
        return '\n'.join(diff)
