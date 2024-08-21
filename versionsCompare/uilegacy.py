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

            pdf1_paragraphs = pdf1_text.split('\n\n')
            pdf2_paragraphs = pdf2_text.split('\n\n')

            differences = self.compare_paragraphs(pdf1_paragraphs, pdf2_paragraphs)
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

    def compare_paragraphs(self, pdf1_paragraphs, pdf2_paragraphs):
        differences = []
        index = 1
        for i, para1 in enumerate(pdf1_paragraphs):
            if i < len(pdf2_paragraphs):
                para2 = pdf2_paragraphs[i]
                diff = self.compare_words(para1, para2, index)
                if diff:
                    differences.append(diff)
                    index += 1
            else:
                differences.append(f"Index {index}:\nPDF 1: {para1}\nPDF 2: <no corresponding paragraph>\n")
                index += 1
        return differences

    def compare_words(self, para1, para2, index):
        words1 = para1.split()
        words2 = para2.split()

        result = []
        i, j = 0, 0
        while i < len(words1) and j < len(words2):
            if words1[i] == words2[j]:
                result.append(words1[i])
                i += 1
                j += 1
            else:
                if words1[i] not in words2[j:]:
                    result.append(f"<nou: {words1[i]}>")
                    i += 1
                elif words2[j] not in words1[i:]:
                    result.append(f"<siu: {words2[j]}>")
                    j += 1
                else:
                    result.append(f"<diff: {words1[i]} | {words2[j]}>")
                    i += 1
                    j += 1

        while i < len(words1):
            result.append(f"<nou: {words1[i]}>")
            i += 1

        while j < len(words2):
            result.append(f"<siu: {words2[j]}>")
            j += 1

        if result:
            return f"Index {index}:\n{' '.join(result)}\n"
        return None

    def display_differences(self, differences):
        diff_text = '\n'.join(differences)
        self.result_text.setText(diff_text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
