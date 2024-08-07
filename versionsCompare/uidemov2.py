import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QTextEdit, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
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

        self.diff_navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous Difference", self)
        self.prev_button.clicked.connect(self.prev_difference)
        self.next_button = QPushButton("Next Difference", self)
        self.next_button.clicked.connect(self.next_difference)
        self.diff_navigation_layout.addWidget(self.prev_button)
        self.diff_navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(self.diff_navigation_layout)

        self.diff_desc = QLabel(self)
        self.diff_desc.setFixedHeight(40)  # Ajustar la altura a 5% de la altura total (800px * 0.05 = 40px)
        self.layout.addWidget(self.diff_desc)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.differences = []
        self.current_diff_index = -1

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

            temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words)
            temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words)

            self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path)

            self.current_diff_index = -1
            self.next_difference()

    def find_differences(self, words1, words2):
        differences = []
        for page_num in range(min(len(words1), len(words2))):
            page_differences = []
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word in words1[page_num]:
                if word[4] not in words2_set:
                    page_differences.append((page_num, word[:4], 'pdf1', word[4]))
            for word in words2[page_num]:
                if word[4] not in words1_set:
                    page_differences.append((page_num, word[:4], 'pdf2', word[4]))

            differences.extend(page_differences)
        return differences

    def highlight_differences(self, file_path, words1, words2):
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            if page_num < len(words1) and page_num < len(words2):
                words1_set = set((word[4] for word in words1[page_num]))
                words2_set = set((word[4] for word in words2[page_num]))

                for word in words1[page_num]:
                    if word[4] not in words2_set:
                        highlight = fitz.Rect(word[:4])
                        page.add_highlight_annot(highlight)
            elif page_num < len(words1):
                for word in words1[page_num]:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)

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

    def next_difference(self):
        if self.differences:
            self.current_diff_index = (self.current_diff_index + 1) % len(self.differences)
            self.scroll_to_difference()

    def prev_difference(self):
        if self.differences:
            self.current_diff_index = (self.current_diff_index - 1) % len(self.differences)
            self.scroll_to_difference()

    def scroll_to_difference(self):
        if self.current_diff_index != -1:
            page_num, word_rect, pdf_source, word_text = self.differences[self.current_diff_index]
            self.diff_desc.setText(f"Page: {page_num+1}, Source: {pdf_source}, Word: {word_text}")

            if pdf_source == 'pdf1':
                self.pdf1_scroll.verticalScrollBar().setValue(int(word_rect[1]) - 50)
                self.pdf2_scroll.verticalScrollBar().setValue(int(word_rect[1]) - 50)
            else:
                self.pdf2_scroll.verticalScrollBar().setValue(int(word_rect[1]) - 50)
                self.pdf1_scroll.verticalScrollBar().setValue(int(word_rect[1]) - 50)

            self.highlight_current_difference(page_num, word_rect)

    def highlight_current_difference(self, page_num, word_rect):
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)

        highlight = fitz.Rect(word_rect)

        doc1[page_num].draw_rect(highlight, color=(1, 0, 0), width=2)
        doc2[page_num].draw_rect(highlight, color=(1, 0, 0), width=2)

        icon_rect = fitz.Rect(
            highlight.x0, highlight.y0 - 10, highlight.x0 + 10, highlight.y0
        )
        icon_text = ">"
        doc1[page_num].insert_text(icon_rect.br, icon_text, color=(1, 0, 0), fontsize=12)
        doc2[page_num].insert_text(icon_rect.br, icon_text, color=(1, 0, 0), fontsize=12)

        self.display_pdfs(self.pdf1_layout, self.save_temp_pdf(doc1))
        self.display_pdfs(self.pdf2_layout, self.save_temp_pdf(doc2))

    def save_temp_pdf(self, doc):
        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
