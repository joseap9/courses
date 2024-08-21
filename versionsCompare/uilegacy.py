import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QLabel, QPushButton, QVBoxLayout,
    QWidget, QScrollArea, QTextEdit, QHBoxLayout
)
from PyQt5.QtGui import QFont
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF Comparer')
        self.setGeometry(100, 100, 1000, 700)

        layout = QVBoxLayout()

        self.label = QLabel("Load two PDFs to compare", self)
        self.label.setFont(QFont("Arial", 14))
        layout.addWidget(self.label)

        buttons_layout = QHBoxLayout()

        self.load_pdf1_button = QPushButton("Load PDF 1", self)
        self.load_pdf1_button.clicked.connect(self.load_pdf1)
        buttons_layout.addWidget(self.load_pdf1_button)

        self.load_pdf2_button = QPushButton("Load PDF 2", self)
        self.load_pdf2_button.clicked.connect(self.load_pdf2)
        buttons_layout.addWidget(self.load_pdf2_button)

        self.compare_button = QPushButton("Compare PDFs", self)
        self.compare_button.clicked.connect(self.compare_pdfs)
        buttons_layout.addWidget(self.compare_button)

        layout.addLayout(buttons_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Courier", 12))

        self.scroll_area.setWidget(self.result_text)
        layout.addWidget(self.scroll_area)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_pdf1(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load PDF 1", "", "PDF Files (*.pdf)", options=options)
        if file_name:
            self.pdf1_path = file_name
            self.label.setText(f"PDF 1 Loaded: {file_name}")

    def load_pdf2(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load PDF 2", "", "PDF Files (*.pdf)", options=options)
        if file_name:
            self.pdf2_path = file_name
            self.label.setText(f"PDF 2 Loaded: {file_name}")

    def compare_pdfs(self):
        if hasattr(self, 'pdf1_path') and hasattr(self, 'pdf2_path'):
            pdf1_text = self.extract_text(self.pdf1_path)
            pdf2_text = self.extract_text(self.pdf2_path)

            pdf1_words = pdf1_text.split()
            pdf2_words = pdf2_text.split()

            differences = self.compare_words(pdf1_words, pdf2_words)
            self.display_differences(differences)
        else:
            self.label.setText("Please load both PDFs first")

    def extract_text(self, pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")
        return text

    def compare_words(self, words1, words2):
        differences = []
        i, j = 0, 0
        index = 1
        while i < len(words1) and j < len(words2):
            if words1[i] == words2[j]:
                i += 1
                j += 1
            else:
                start_i, start_j = i, j
                while i < len(words1) and (j >= len(words2) or words1[i] != words2[j]):
                    i += 1
                while j < len(words2) and (i >= len(words1) or words1[i] != words2[j]):
                    j += 1
                if start_i < i:
                    differences.append(f"Index {index}:\nPDF 2 NOTHING\nPDF 1: {' '.join(words1[start_i:i])}\n")
                if start_j < j:
                    differences.append(f"Index {index}:\nPDF 1 NOTHING\nPDF 2: {' '.join(words2[start_j:j])}\n")
                if i < len(words1) and j < len(words2) and words1[i] != words2[j]:
                    differences.append(f"Index {index}:\nPDF 1: {words1[i]} PDF 2: {words2[j]}")
                index += 1
                i += 1
                j += 1

        while i < len(words1):
            differences.append(f"Index {index}:\nPDF 2 NOTHING\nPDF 1: {words1[i]}")
            i += 1
            index += 1

        while j < len(words2):
            differences.append(f"Index {index}:\nPDF 1 NOTHING\nPDF 2: {words2[j]}")
            j += 1
            index += 1

        return differences

    def display_differences(self, differences):
        diff_text = '\n'.join(differences)
        self.result_text.setText(diff_text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
