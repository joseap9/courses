import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.layout.addWidget(self.button2)

        self.result_text = QTextEdit(self)
        self.layout.addWidget(self.result_text)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None

    def load_first_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.pdf1_text = self.extract_text_from_pdf(fileName)
            self.compare_pdfs()

    def load_second_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.pdf2_text = self.extract_text_from_pdf(fileName)
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
            differences = self.find_differences(self.pdf1_text, self.pdf2_text)
            self.result_text.setText(differences)

    def find_differences(self, text1, text2):
        differences = ""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        len1, len2 = len(lines1), len(lines2)
        max_len = max(len1, len2)
        
        for i in range(max_len):
            line1 = lines1[i] if i < len1 else ""
            line2 = lines2[i] if i < len2 else ""
            if line1 != line2:
                differences += f"Line {i+1}:\nFile 1: {line1}\nFile 2: {line2}\n\n"
        
        return differences

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
