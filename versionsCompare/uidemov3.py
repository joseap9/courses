import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget,
    QScrollArea, QSplitter, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF

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

        self.label = QLabel("Description of the current difference will appear here", self)
        self.layout.addWidget(self.label)

        navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous Difference", self)
        self.prev_button.clicked.connect(self.prev_difference)
        self.next_button = QPushButton("Next Difference", self)
        self.next_button.clicked.connect(self.next_difference)
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(navigation_layout)

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

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None
        self.differences = []
        self.current_diff_index = 0

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

            self.differences = []
            self.find_differences()

            if self.differences:
                self.current_diff_index = 0
                self.display_current_difference()

    def find_differences(self):
        for page_num in range(len(self.pdf1_words)):
            if page_num < len(self.pdf2_words):
                words1_set = set((word[4] for word in self.pdf1_words[page_num]))
                words2_set = set((word[4] for word in self.pdf2_words[page_num]))

                for word1 in self.pdf1_words[page_num]:
                    if word1[4] not in words2_set:
                        self.differences.append((page_num, word1, None))
                for word2 in self.pdf2_words[page_num]:
                    if word2[4] not in words1_set:
                        self.differences.append((page_num, None, word2))
            elif page_num < len(self.pdf1_words):
                for word1 in self.pdf1_words[page_num]:
                    self.differences.append((page_num, word1, None))
            elif page_num < len(self.pdf2_words):
                for word2 in self.pdf2_words[page_num]:
                    self.differences.append((page_num, None, word2))

    def display_current_difference(self):
        if not self.differences:
            return

        page_num, word1, word2 = self.differences[self.current_diff_index]

        self.highlight_differences(self.pdf1_path, word1, self.pdf1_layout, is_pdf1=True)
        self.highlight_differences(self.pdf2_path, word2, self.pdf2_layout, is_pdf1=False)

        description = f"Page {page_num + 1}: "
        if word1 and word2:
            description += f"PDF1: '{word1[4]}' vs PDF2: '{word2[4]}'"
        elif word1:
            description += f"PDF1: '{word1[4]}' vs PDF2: 'SD'"
        elif word2:
            description += f"PDF1: 'SD' vs PDF2: '{word2[4]}'"

        self.label.setText(description)

    def highlight_differences(self, file_path, word, layout, is_pdf1):
        doc = fitz.open(file_path)

        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        if word:
            page = doc.load_page(word[5])
            highlight = fitz.Rect(word[:4])
            page.add_highlight_annot(highlight)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            label = QLabel(self)
            label.setPixmap(QPixmap.fromImage(img))
            layout.addWidget(label)

    def next_difference(self):
        if self.differences:
            self.current_diff_index = (self.current_diff_index + 1) % len(self.differences)
            self.display_current_difference()

    def prev_difference(self):
        if self.differences:
            self.current_diff_index = (self.current_diff_index - 1) % len(self.differences)
            self.display_current_difference()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
