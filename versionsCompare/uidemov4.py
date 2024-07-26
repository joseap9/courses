import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QLabel, QScrollArea, QSplitter
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPixmap
import fitz  # PyMuPDF
import tempfile

class ClickableLabel(QLabel):
    clicked = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.highlighted_areas = []

    def mousePressEvent(self, event):
        for highlight in self.highlighted_areas:
            if highlight[0].contains(event.pos()):
                self.clicked.emit(highlight[1])
                break

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

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

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

            temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words)
            temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words)

            self.display_pdfs(self.pdf1_layout, temp_pdf1_path, 'first')
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path, 'second')

    def highlight_differences(self, file_path, words1, words2):
        doc = fitz.open(file_path)
        self.differences = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            if page_num < len(words1) and page_num < len(words2):
                words1_set = set((word[4] for word in words1[page_num]))
                words2_set = set((word[4] for word in words2[page_num]))

                for word in words1[page_num]:
                    if word[4] not in words2_set:
                        highlight = fitz.Rect(word[:4])
                        page.add_highlight_annot(highlight)
                        self.differences.append((page_num, highlight, file_path))
            elif page_num < len(words1):
                for word in words1[page_num]:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)
                    self.differences.append((page_num, highlight, file_path))

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

    def display_pdfs(self, layout, file_path, tag):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            temp_image_path = tempfile.mktemp(suffix=".png")
            pix.save(temp_image_path)
            label = ClickableLabel(self)
            label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))
            label.highlighted_areas = [(self.rect_to_qrect(rect), rect) for rect in self.get_page_differences(page_num, tag)]
            label.clicked.connect(self.highlight_selected)
            layout.addWidget(label)

    def get_page_differences(self, page_num, tag):
        return [diff[1] for diff in self.differences if diff[0] == page_num and diff[2] == tag]

    def rect_to_qrect(self, rect):
        return QRectF(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0).toRect()

    def highlight_selected(self, rect):
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)

        for diff in self.differences:
            if diff[1] == rect:
                page1 = doc1.load_page(diff[0])
                page2 = doc2.load_page(diff[0])

                if diff[2] == self.pdf1_path:
                    page1.add_rect_annot(rect, color=(1, 0, 0))
                    corresponding_rect = self.find_corresponding_rect(diff[0], rect, self.pdf2_words)
                    if corresponding_rect:
                        page2.add_rect_annot(corresponding_rect, color=(1, 0, 0))
                else:
                    page2.add_rect_annot(rect, color=(1, 0, 0))
                    corresponding_rect = self.find_corresponding_rect(diff[0], rect, self.pdf1_words)
                    if corresponding_rect:
                        page1.add_rect_annot(corresponding_rect, color=(1, 0, 0))

        temp_pdf1_path = tempfile.mktemp(suffix=".pdf")
        doc1.save(temp_pdf1_path)
        temp_pdf2_path = tempfile.mktemp(suffix=".pdf")
        doc2.save(temp_pdf2_path)
        self.display_pdfs(self.pdf1_layout, temp_pdf1_path, 'first')
        self.display_pdfs(self.pdf2_layout, temp_pdf2_path, 'second')

    def find_corresponding_rect(self, page_num, rect, words):
        for word in words[page_num]:
            word_rect = fitz.Rect(word[:4])
            if word_rect == rect:
                return word_rect
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())