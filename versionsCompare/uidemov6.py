import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
import fitz  # PyMuPDF
import tempfile

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1600, 800)

        self.layout = QVBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.layout.addWidget(self.button2)

        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Prev", self)
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        self.navigation_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        self.navigation_layout.addWidget(self.next_button)

        self.layout.addLayout(self.navigation_layout)

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

        self.differences_navigation_layout = QVBoxLayout()
        self.prev_diff_button = QPushButton("Prev Different", self)
        self.prev_diff_button.clicked.connect(self.prev_difference)
        self.prev_diff_button.setEnabled(False)
        self.differences_navigation_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Different", self)
        self.next_diff_button.clicked.connect(self.next_difference)
        self.next_diff_button.setEnabled(False)
        self.differences_navigation_layout.addWidget(self.next_diff_button)

        self.splitter2 = QSplitter(Qt.Vertical)
        self.splitter2.addWidget(self.splitter)
        self.diff_navigation_widget = QWidget()
        self.diff_navigation_widget.setLayout(self.differences_navigation_layout)
        self.splitter2.addWidget(self.diff_navigation_widget)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(self.splitter2)

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
        self.current_difference = 0
        self.differences = []

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
        self.current_difference = 0
        self.differences = []
        self.pdf1_layout.update()
        self.pdf2_layout.update()
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
            self.update_differences_navigation()

    def highlight_differences(self, file_path, words1, words2, page_num):
        doc = fitz.open(file_path)
        page_differences = []

        if page_num < len(words1) and page_num < len(words2):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word in words1[page_num]:
                if word[4] not in words2_set:
                    highlight = fitz.Rect(word[:4])
                    doc[page_num].add_highlight_annot(highlight)
                    page_differences.append(highlight)
        elif page_num < len(words1):
            for word in words1[page_num]:
                highlight = fitz.Rect(word[:4])
                doc[page_num].add_highlight_annot(highlight)
                page_differences.append(highlight)

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path, page_differences

    def load_page_pair(self, page_num):
        temp_pdf1_path, pdf1_differences = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words, page_num)
        temp_pdf2_path, pdf2_differences = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words, page_num)

        if len(self.temp_pdf1_paths) <= page_num:
            self.temp_pdf1_paths.append(temp_pdf1_path)
            self.temp_pdf2_paths.append(temp_pdf2_path)
            self.differences.append(pdf1_differences)
        else:
            self.temp_pdf1_paths[page_num] = temp_pdf1_path
            self.temp_pdf2_paths[page_num] = temp_pdf2_path
            self.differences[page_num] = pdf1_differences

        self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
        self.display_pdfs(self.pdf2_layout, temp_pdf2_path)
        self.update_differences_navigation()

    def display_pdfs(self, layout, file_path, highlight_rect=None):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        page = doc.load_page(self.current_page)
        pix = page.get_pixmap()
        temp_image_path = tempfile.mktemp(suffix=".png")
        pix.save(temp_image_path)

        pixmap = QPixmap(temp_image_path)
        if highlight_rect:
            painter = QPainter(pixmap)
            pen = QPen(QColor("red"))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(highlight_rect.x0, highlight_rect.y0, highlight_rect.width, highlight_rect.height)
            painter.end()

        label = QLabel(self)
        label.setPixmap(pixmap.scaled(600, 800, Qt.KeepAspectRatio))
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
            self.current_difference = 0
            self.update_differences_navigation()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.next_button.setEnabled(True)
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page])
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page])
            if self.current_page == 0:
                self.prev_button.setEnabled(False)
            self.current_difference = 0
            self.update_differences_navigation()

    def next_difference(self):
        if self.current_difference < len(self.differences[self.current_page]) - 1:
            self.current_difference += 1
            self.update_differences_navigation()
        self.update_difference_highlight()

    def prev_difference(self):
        if self.current_difference > 0:
            self.current_difference -= 1
            self.update_differences_navigation()
        self.update_difference_highlight()

    def update_differences_navigation(self):
        if self.differences[self.current_page]:
            self.next_diff_button.setEnabled(self.current_difference < len(self.differences[self.current_page]) - 1)
            self.prev_diff_button.setEnabled(self.current_difference > 0)
        else:
            self.next_diff_button.setEnabled(False)
            self.prev_diff_button.setEnabled(False)

    def update_difference_highlight(self):
        if self.differences[self.current_page]:
            highlight_rect = self.differences[self.current_page][self.current_difference]
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], highlight_rect)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], highlight_rect)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
