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
            self.pdf1_text = self.extract_text_from_pdf(fileName)
            self.pdf1_path = fileName
            self.compare_pdfs()

    def load_second_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.pdf2_text = self.extract_text_from_pdf(fileName)
            self.pdf2_path = fileName
            self.compare_pdfs()

    def extract_text_from_pdf(self, file_path):
        document = fitz.open(file_path)
        text = ""
        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text += page.get_text()
        return text

    def compare_pdfs(self):
        if self.pdf1_text and self.pdf2_text:
            temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_text, self.pdf2_text)
            temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_text, self.pdf1_text)

            self.display_pdf(self.pdf1_label, temp_pdf1_path)
            self.display_pdf(self.pdf2_label, temp_pdf2_path)

    def highlight_differences(self, file_path, text1, text2):
        doc = fitz.open(file_path)
        words1 = text1.split()
        words2 = text2.split()
        highlight_format = {"color": (1, 1, 0), "opacity": 0.5}

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("blocks")
            for b in blocks:
                for line in b[4].split('\n'):
                    for word in line.split():
                        if word in words1 and word not in words2:
                            highlight = fitz.Rect(b[:4])
                            page.add_highlight_annot(highlight)
                        elif word in words2 and word not in words1:
                            highlight = fitz.Rect(b[:4])
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
