import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, 
                             QHBoxLayout, QLabel, QScrollArea, QSplitter, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import fitz  # PyMuPDF
import tempfile

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1400, 800)

        self.layout = QHBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.layout.addWidget(self.button2)

        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

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

        self.diff_panel = QFrame(self)
        self.diff_panel.setFrameShape(QFrame.StyledPanel)
        self.diff_layout = QVBoxLayout()
        self.diff_panel.setLayout(self.diff_layout)

        self.diff_label = QLabel("Difference Description", self)
        self.diff_layout.addWidget(self.diff_label)

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_previous_difference)
        self.diff_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_difference)
        self.diff_layout.addWidget(self.next_button)

        self.splitter.addWidget(self.diff_panel)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None
        self.differences = []
        self.current_difference_index = -1

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

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
        document = fitz.open(file_path)
        text = []
        words = []

        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text.append(page.get_text())
            word_list = page.get_text("words")
            words.append(word_list)

        return text, words

    def compare_pdfs(self):
        if self.pdf1_path and self.pdf2_path:
            self.pdf1_text, self.pdf1_words = self.extract_text_and_positions(self.pdf1_path)
            self.pdf2_text, self.pdf2_words = self.extract_text_and_positions(self.pdf2_path)

            self.differences = self.find_differences(self.pdf1_words, self.pdf2_words)
            self.current_difference_index = 0 if self.differences else -1

            temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.differences, True)
            temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.differences, False)

            self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path)
            self.update_difference_panel()

    def find_differences(self, words1, words2):
        differences = []
        for page_num in range(min(len(words1), len(words2))):
            words1_set = set((word[4], word[:4]) for word in words1[page_num])
            words2_set = set((word[4], word[:4]) for word in words2[page_num])

            page_differences = words1_set.symmetric_difference(words2_set)
            differences.extend((page_num, word[1]) for word in page_differences)
        return differences

    def highlight_differences(self, file_path, words, differences, is_first_pdf):
        doc = fitz.open(file_path)

        for page_num, rect in differences:
            page = doc.load_page(page_num)
            highlight = fitz.Rect(rect)
            page.add_highlight_annot(highlight)
            if self.current_difference_index >= 0 and differences[self.current_difference_index] == (page_num, rect):
                page.add_rect_annot(highlight).set_colors(stroke=[1, 0, 0])  # Red rectangle

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

    def update_difference_panel(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            self.diff_label.setText(f"Difference {self.current_difference_index + 1}/{len(self.differences)}")
        else:
            self.diff_label.setText("No Differences")

    def show_previous_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.compare_pdfs()

    def show_next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.current_difference_index += 1
            self.compare_pdfs()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
