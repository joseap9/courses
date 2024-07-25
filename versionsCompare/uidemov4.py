import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QVBoxLayout, QWidget, QScrollArea, QSplitter, QPushButton
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QCursor, QImage, QPainter, QColor
import fitz  # PyMuPDF
import tempfile

class ClickableLabel(QLabel):
    def __init__(self, page_num, pdf_num, rects, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.pdf_num = pdf_num
        self.rects = rects
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        pos = event.pos()
        for rect in self.rects:
            if rect.contains(fitz.Point(pos.x(), pos.y())):
                self.parent().on_pdf_click(self.page_num, self.pdf_num, rect)
                break

    def mouseMoveEvent(self, event):
        pos = event.pos()
        for rect in self.rects:
            if rect.contains(fitz.Point(pos.x(), pos.y())):
                self.setCursor(QCursor(Qt.PointingHandCursor))
                return
        self.setCursor(QCursor(Qt.ArrowCursor))


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

        self.differences = []
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

            self.temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words)
            self.temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words)

            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_path, 1)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_path, 2)

    def find_differences(self, words1, words2):
        differences = []
        for page_num in range(min(len(words1), len(words2))):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))
            page_differences = [(page_num, word) for word in words1[page_num] if word[4] not in words2_set]
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

    def display_pdfs(self, layout, file_path, pdf_num):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            temp_image_path = tempfile.mktemp(suffix=".png")
            pix.save(temp_image_path)

            # Obtener las áreas resaltadas
            highlights = [fitz.Rect(annot.rect) for annot in page.annots() if annot.type == fitz.PDF_ANNOT_HIGHLIGHT]

            label = ClickableLabel(page_num, pdf_num, highlights, self)
            label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))
            label.setAlignment(Qt.AlignTop)
            layout.addWidget(label)

    def on_pdf_click(self, page_num, pdf_num, rect):
        if pdf_num == 1:
            self.temp_pdf1_path = self.add_highlight_to_pdf(self.temp_pdf1_path, page_num, rect)
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_path, 1)
            self.highlight_corresponding_difference(page_num, rect, 2)
        else:
            self.temp_pdf2_path = self.add_highlight_to_pdf(self.temp_pdf2_path, page_num, rect)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_path, 2)
            self.highlight_corresponding_difference(page_num, rect, 1)

    def add_highlight_to_pdf(self, file_path, page_num, rect):
        doc = fitz.open(file_path)
        page = doc.load_page(page_num)
        highlight = page.add_rect_annot(rect)
        highlight.set_colors(stroke=(1, 0, 0), fill=None)
        highlight.update()

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

    def highlight_corresponding_difference(self, page_num, rect, pdf_num):
        if pdf_num == 1:
            self.temp_pdf1_path = self.add_highlight_to_pdf(self.temp_pdf1_path, page_num, rect)
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_path, 1)
        else:
            self.temp_pdf2_path = self.add_highlight_to_pdf(self.temp_pdf2_path, page_num, rect)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_path, 2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
