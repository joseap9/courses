import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QScrollArea, QSplitter, QLabel
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
        words = []

        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            word_list = page.get_text("words")
            words.append(word_list)

        return words

    def compare_pdfs(self):
        if self.pdf1_path and self.pdf2_path:
            self.pdf1_words = self.extract_text_and_positions(self.pdf1_path)
            self.pdf2_words = self.extract_text_and_positions(self.pdf2_path)

            self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words, self.pdf1_layout, "PDF1")
            self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words, self.pdf2_layout, "PDF2")

    def highlight_differences(self, file_path, words1, words2, layout, label):
        doc = fitz.open(file_path)
        opposite_label = "PDF1" if label == "PDF2" else "PDF2"

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            words1_page = words1[page_num] if page_num < len(words1) else []
            words2_page = words2[page_num] if page_num < len(words2) else []

            words1_set = set((word[4] for word in words1_page))
            words2_set = set((word[4] for word in words2_page))

            for word in words1_page:
                if word[4] not in words2_set:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)
                    self.add_label(layout, word[4], "SD", label)
                else:
                    opposite_word = next((w for w in words2_page if w[4] == word[4]), None)
                    if opposite_word and word[4] != opposite_word[4]:
                        highlight = fitz.Rect(word[:4])
                        page.add_highlight_annot(highlight)
                        opposite_highlight = fitz.Rect(opposite_word[:4])
                        opposite_page = doc.load_page(opposite_word[5])
                        opposite_page.add_highlight_annot(opposite_highlight)
                        self.add_label(layout, word[4], opposite_word[4], label)
            for word in words2_page:
                if word[4] not in words1_set:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)
                    self.add_label(layout, "SD", word[4], opposite_label)

        self.display_pdfs(layout, doc)

    def add_label(self, layout, text1, text2, label):
        label_text = QLabel(f"{label}: {text1} vs. {'PDF2' if label == 'PDF1' else 'PDF1'}: {text2}", self)
        layout.addWidget(label_text)

    def display_pdfs(self, layout, doc):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            label = QLabel(self)
            label.setPixmap(QPixmap.fromImage(img))
            layout.addWidget(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
