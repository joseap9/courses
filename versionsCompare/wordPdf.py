import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget,
    QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit,
    QButtonGroup, QFrame, QMessageBox, QTextEdit, QInputDialog, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
from docx import Document  # python-docx para manejar documentos Word


class DocumentComparer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Comparer")
        self.setGeometry(100, 100, 1650, 800)

        self.main_layout = QHBoxLayout()
        self.init_left_section()
        self.init_right_section()

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Variables de inicialización
        self.reset_all()

    def init_left_section(self):
        self.left_layout = QVBoxLayout()

        self.button1 = QPushButton("Select First Document", self)
        self.button1.clicked.connect(self.load_first_document)
        self.left_layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second Document", self)
        self.button2.clicked.connect(self.load_second_document)
        self.left_layout.addWidget(self.button2)

        self.splitter = QSplitter(Qt.Horizontal)
        self.pdf1_scroll = QScrollArea(self)
        self.pdf2_scroll = QScrollArea(self)

        self.pdf1_container = QWidget()
        self.pdf2_container = QWidget()

        self.pdf1_layout = QVBoxLayout()
        self.pdf2_layout = QVBoxLayout()

        self.pdf1_container.setLayout(self.pdf1_layout)
        self.pdf2_container.setLayout(self.pdf2_layout)

        self.pdf1_scroll.setWidget(self.pdf1_container)
        self.pdf2_scroll.setWidget(self.pdf2_container)

        self.splitter.addWidget(self.pdf1_scroll)
        self.splitter.addWidget(self.pdf2_scroll)

        self.left_layout.addWidget(self.splitter)
        self.main_layout.addLayout(self.left_layout)

    def init_right_section(self):
        self.right_frame = QFrame(self)
        self.right_frame.setFixedWidth(300)
        self.right_layout = QVBoxLayout(self.right_frame)

        self.page_diff_label = QLabel("Differences", self)
        self.page_diff_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.right_layout.addWidget(self.page_diff_label)

        self.main_layout.addWidget(self.right_frame)

    def reset_all(self):
        self.doc1_path = None
        self.doc2_path = None
        self.doc1_content = []
        self.doc2_content = []

    def load_first_document(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select First Document",
                                                   "", "Documents (*.pdf *.docx);;All Files (*)")
        if file_name:
            self.doc1_path = file_name
            self.process_document(file_name, is_first=True)

    def load_second_document(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Second Document",
                                                   "", "Documents (*.pdf *.docx);;All Files (*)")
        if file_name:
            self.doc2_path = file_name
            self.process_document(file_name, is_first=False)

    def process_document(self, file_path, is_first):
        content = []
        if file_path.endswith(".pdf"):
            content = self.extract_pdf_text(file_path)
        elif file_path.endswith(".docx"):
            content = self.extract_word_text(file_path)

        if is_first:
            self.doc1_content = content
        else:
            self.doc2_content = content

        self.compare_documents()

    def extract_pdf_text(self, file_path):
        document = fitz.open(file_path)
        content = [page.get_text() for page in document]
        return content

    def extract_word_text(self, file_path):
        document = Document(file_path)
        content = [paragraph.text for paragraph in document.paragraphs]
        return content

    def compare_documents(self):
        if self.doc1_content and self.doc2_content:
            differences = []
            max_length = max(len(self.doc1_content), len(self.doc2_content))

            for i in range(max_length):
                page1 = self.doc1_content[i] if i < len(self.doc1_content) else ""
                page2 = self.doc2_content[i] if i < len(self.doc2_content) else ""
                if page1 != page2:
                    differences.append((i + 1, page1, page2))

            self.display_differences(differences)

    def display_differences(self, differences):
        for widget in self.pdf1_layout.children():
            widget.deleteLater()
        for widget in self.pdf2_layout.children():
            widget.deleteLater()

        for diff in differences:
            page_num, text1, text2 = diff
            label1 = QLabel(f"Page {page_num}: {text1}", self)
            label2 = QLabel(f"Page {page_num}: {text2}", self)
            self.pdf1_layout.addWidget(label1)
            self.pdf2_layout.addWidget(label2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = DocumentComparer()
    comparer.show()
    sys.exit(app.exec_())
