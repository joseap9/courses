import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import fitz  # PyMuPDF
import difflib
from pdfminer.high_level import extract_text
import tempfile

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        self.main_layout = QVBoxLayout()

        # Top layout for select buttons
        self.top_layout = QHBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.top_layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.top_layout.addWidget(self.button2)

        self.main_layout.addLayout(self.top_layout)

        # Middle layout for PDFs and navigation buttons
        self.middle_layout = QHBoxLayout()

        # Left layout for PDFs
        self.left_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)
        self.left_layout.addWidget(self.splitter)

        self.pdf1_scroll = QScrollArea(self)
        self.pdf1_container = QWidget()
        self.pdf1_layout = QVBoxLayout()
        self.pdf1_container.setLayout(self.pdf1_layout)
        self.pdf1_scroll.setWidget(self.pdf1_container)
        self.pdf1_scroll.setWidgetResizable(True)

        self.pdf2_scroll = QScrollArea(self)
        self.pdf2_container = QWidget()
        self.pdf2_layout = QVBoxLayout()
        self.pdf2_container.setLayout(self.pdf2_layout)
        self.pdf2_scroll.setWidget(self.pdf2_container)
        self.pdf2_scroll.setWidgetResizable(True)

        self.splitter.addWidget(self.pdf1_scroll)
        self.splitter.addWidget(self.pdf2_scroll)

        # Right layout for navigation buttons
        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignBottom)

        self.difference_label = QLabel(self)
        self.right_layout.addWidget(self.difference_label)

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.prev_difference)
        self.prev_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.next_difference)
        self.next_button.setEnabled(False)
        self.right_layout.addWidget(self.next_button)

        self.middle_layout.addLayout(self.left_layout, 8)
        self.middle_layout.addLayout(self.right_layout, 1)

        self.main_layout.addLayout(self.middle_layout)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.differences = []
        self.current_difference_index = -1
        self.temp_pdf1_path = None
        self.temp_pdf2_path = None

    def sync_scroll(self, value):
        if self.sender() == self.pdf1_scroll.verticalScrollBar():
            self.pdf2_scroll.verticalScrollBar().setValue(value)
        elif self.sender() == self.pdf2_scroll.verticalScrollBar():
            self.pdf1_scroll.verticalScrollBar().setValue(value)

    def load_first_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.button1.setText(fileName.split('/')[-1])
            self.pdf1_path = fileName
            self.compare_pdfs()

    def load_second_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.button2.setText(fileName.split('/')[-1])
            self.pdf2_path = fileName
            self.compare_pdfs()

    def extract_text_and_positions(self, file_path):
        text = extract_text(file_path)
        return text.split()

    def compare_pdfs(self):
        if self.pdf1_path and self.pdf2_path:
            self.pdf1_text = self.extract_text_and_positions(self.pdf1_path)
            self.pdf2_text = self.extract_text_and_positions(self.pdf2_path)

            self.differences = self.find_differences(self.pdf1_text, self.pdf2_text)
            if self.differences:
                self.current_difference_index = 0
                self.update_navigation_buttons()

            self.temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_text, self.pdf2_text)
            self.temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_text, self.pdf1_text)

            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_path)

            self.highlight_current_difference()

    def find_differences(self, text1, text2):
        d = difflib.Differ()
        differences = list(d.compare(text1, text2))
        return [(i, diff) for i, diff in enumerate(differences) if diff[0] in ('-', '+')]

    def highlight_differences(self, file_path, text1, text2):
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Lógica para resaltar diferencias basada en text1 y text2
            # ...

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

    def display_pdfs(self, layout, file_path):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            temp_image_path = tempfile.mktemp(suffix=".png")
            pix.save(temp_image_path)
            label = QLabel(self)
            label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))
            layout.addWidget(label)

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_difference_index > 0)
        self.next_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.update_difference_label()

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            index, diff = self.differences[self.current_difference_index]
            # Resaltar la diferencia actual en los PDFs
            # ...

            self.update_difference_label()

    def update_difference_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            index, diff = self.differences[self.current_difference_index]
            self.difference_label.setText(f"Difference {self.current_difference_index + 1} of {len(self.differences)}: {diff}")

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
