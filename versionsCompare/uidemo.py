import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import fitz  # PyMuPDF
import tempfile

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        self.layout = QVBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.layout.addWidget(self.button2)

        self.pdf_layout = QHBoxLayout()
        self.pdf1_label = QLabel(self)
        self.pdf2_label = QLabel(self)
        self.pdf1_label.setAlignment(Qt.AlignTop)
        self.pdf2_label.setAlignment(Qt.AlignTop)
        self.pdf_layout.addWidget(self.pdf1_label)
        self.pdf_layout.addWidget(self.pdf2_label)
        self.layout.addLayout(self.pdf_layout)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

    def load_first_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.pdf1_text, self.pdf1_words = self.extract_text_and_positions(fileName)
            self.pdf1_path = fileName
            self.compare_pdfs()

    def load_second_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.pdf2_text, self.pdf2_words = self.extract_text_and_positions(fileName)
            self.pdf2_path = fileName
            self.compare_pdfs()

    def extract_text_and_positions(self, file_path):
        document = fitz.open(file_path)
        text = ""
        words = []

        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text += page.get_text()
            word_list = page.get_text("words")
            words.extend(word_list)

        return text, words

    def compare_pdfs(self):
        if self.pdf1_text and self.pdf2_text:
            temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words)
            temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words)

            self.display_pdf(self.pdf1_label, temp_pdf1_path)
            self.display_pdf(self.pdf2_label, temp_pdf2_path)

    def highlight_differences(self, file_path, words1, words2):
        doc = fitz.open(file_path)
        words2_set = set((word[4] for word in words2))  # Set of words in the second document

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            for word in words1:
                if word[4] not in words2_set:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

    def display_pdf(self, label, file_path):
        doc = fitz.open(file_path)
        page = doc.load_page(0)
        pix = page.get_pixmap()
        temp_image_path = tempfile.mktemp(suffix=".png")
        pix.save(temp_image_path)
        label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
