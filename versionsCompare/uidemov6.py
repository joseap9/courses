import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter
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

        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Prev Page", self)
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        self.navigation_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next Page", self)
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        self.navigation_layout.addWidget(self.next_button)

        self.diff_navigation_layout = QHBoxLayout()
        self.prev_diff_button = QPushButton("Prev Different", self)
        self.prev_diff_button.clicked.connect(self.prev_diff)
        self.prev_diff_button.setEnabled(False)
        self.diff_navigation_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Different", self)
        self.next_diff_button.clicked.connect(self.next_diff)
        self.next_diff_button.setEnabled(False)
        self.diff_navigation_layout.addWidget(self.next_diff_button)

        self.layout.addLayout(self.navigation_layout)
        self.layout.addLayout(self.diff_navigation_layout)

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

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.current_page = 0
        self.total_pages = 0
        self.temp_pdf1_paths = []
        self.temp_pdf2_paths = []

        self.differences = []
        self.current_diff = -1

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
            self.reset_comparison()

    def load_second_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.button2.setText(fileName.split('/')[-1])
            self.pdf2_path = fileName
            self.reset_comparison()

    def reset_comparison(self):
        self.current_page = 0
        self.temp_pdf1_paths = []
        self.temp_pdf2_paths = []
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_diff_button.setEnabled(False)
        self.next_diff_button.setEnabled(False)
        self.pdf1_layout.update()
        self.pdf2_layout.update()
        self.differences = []
        self.current_diff = -1
        if self.pdf1_path and self.pdf2_path:
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

            self.total_pages = min(len(self.pdf1_words), len(self.pdf2_words))
            self.load_page_pair(self.current_page)
            self.next_button.setEnabled(True)
            self.find_differences()

    def find_differences(self):
        for page_num in range(self.total_pages):
            page_diffs = []
            words1_set = set((word[4] for word in self.pdf1_words[page_num]))
            words2_set = set((word[4] for word in self.pdf2_words[page_num]))

            for word in self.pdf1_words[page_num]:
                if word[4] not in words2_set:
                    page_diffs.append(word[:4])
            for word in self.pdf2_words[page_num]:
                if word[4] not in words1_set:
                    page_diffs.append(word[:4])

            if page_diffs:
                self.differences.append((page_num, page_diffs))

        if self.differences:
            self.next_diff_button.setEnabled(True)
            self.load_differences()

    def load_differences(self):
        if self.differences:
            self.current_diff = 0
            self.highlight_difference()

    def highlight_difference(self):
        if self.current_diff >= 0 and self.current_diff < len(self.differences):
            page_num, diff_positions = self.differences[self.current_diff]
            self.current_page = page_num
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page])
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page])
            self.highlight_positions(self.pdf1_layout, diff_positions, self.pdf1_path)
            self.highlight_positions(self.pdf2_layout, diff_positions, self.pdf2_path)
            self.prev_diff_button.setEnabled(self.current_diff > 0)
            self.next_diff_button.setEnabled(self.current_diff < len(self.differences) - 1)

    def highlight_positions(self, layout, positions, file_path):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        page = doc.load_page(self.current_page)
        pix = page.get_pixmap()
        temp_image_path = tempfile.mktemp(suffix=".png")
        pix.save(temp_image_path)
        label = QLabel(self)
        label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))

        for position in positions:
            rect = fitz.Rect(position)
            highlight = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
            page.add_highlight_annot(highlight)

        layout.addWidget(label)

    def highlight_differences(self, file_path, words1, words2, page_num):
        doc = fitz.open(file_path)

        if page_num < len(words1) and page_num < len(words2):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word in words1[page_num]:
                if word[4] not in words2_set:
                    highlight = fitz.Rect(word[:4])
                    doc[page_num].add_highlight_annot(highlight)
        elif page_num < len(words1):
            for word in words1[page_num]:
                highlight = fitz.Rect(word[:4])
                doc[page_num].add_highlight_annot(highlight)

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

    def load_page_pair(self, page_num):
        temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words, page_num)
        temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words, page_num)

        if len(self.temp_pdf1_paths) <= page_num:
            self.temp_pdf1_paths.append(temp_pdf1_path)
            self.temp_pdf2_paths.append(temp_pdf2_path)
        else:
            self.temp_pdf1_paths[page_num] = temp_pdf1_path
            self.temp_pdf2_paths[page_num] = temp_pdf2_path

        self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
        self.display_pdfs(self.pdf2_layout, temp_pdf2_path)

    def display_pdfs(self, layout, file_path):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        page = doc.load_page(self.current_page)
        pix = page.get_pixmap()
        temp_image_path = tempfile.mktemp(suffix=".png")
        pix.save(temp_image_path)
        label = QLabel(self)
        label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))
        layout.addWidget(label)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.prev_button.setEnabled(True)
            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page])
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page])
            if self.current_page == self.total_pages - 1:
                self.next_button.setEnabled(False)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.next_button.setEnabled(True)
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page])
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page])
            if self.current_page == 0:
                self.prev_button.setEnabled(False)

    def next_diff(self):
        if self.current_diff < len(self.differences) - 1:
            self.current_diff += 1
            self.highlight_difference()

    def prev_diff(self):
        if self.current_diff > 0:
            self.current_diff -= 1
            self.highlight_difference()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
