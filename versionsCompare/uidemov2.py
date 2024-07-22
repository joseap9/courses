import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QScrollArea, QSplitter, QFormLayout, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import fitz  # PyMuPDF
import tempfile


class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1400, 800)

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

        self.summary_container = QWidget()
        self.summary_layout = QVBoxLayout()
        self.summary_container.setLayout(self.summary_layout)
        self.splitter.addWidget(self.summary_container)
        self.splitter.setSizes([500, 500, 400])  # Adjust sizes of the columns

        self.summary_label = QLabel(self)
        self.summary_layout.addWidget(self.summary_label)

        self.tagging_container = QWidget()
        self.tagging_layout = QVBoxLayout()
        self.tagging_container.setLayout(self.tagging_layout)
        self.summary_layout.addWidget(self.tagging_container)

        self.next_button = QPushButton("Next", self)
        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(lambda: self.navigate_difference(-1))
        self.next_button.clicked.connect(lambda: self.navigate_difference(1))
        self.summary_layout.addWidget(self.prev_button)
        self.summary_layout.addWidget(self.next_button)

        self.save_button = QPushButton("Save Tags", self)
        self.save_button.clicked.connect(self.save_tags)
        self.summary_layout.addWidget(self.save_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.differences = []  # Lista para almacenar las diferencias
        self.current_diff_index = -1  # Índice de la diferencia actual
        self.tagged_differences = []  # Lista para almacenar las etiquetas de diferencias

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

            temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words, (1, 1, 0))
            temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words, (1, 1, 0))

            self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path)

            self.show_summary()

    def highlight_differences(self, file_path, words1, words2, color):
        doc = fitz.open(file_path)
        differences = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            if page_num < len(words1) and page_num < len(words2):
                words1_set = set((word[4] for word in words1[page_num]))
                words2_set = set((word[4] for word in words2[page_num]))

                for word in words1[page_num]:
                    if word[4] not in words2_set:
                        highlight = fitz.Rect(word[:4])
                        annot = page.add_highlight_annot(highlight)
                        annot.set_colors(stroke=color)
                        annot.update()
                        differences.append((page_num, word))

            elif page_num < len(words1):
                for word in words1[page_num]:
                    highlight = fitz.Rect(word[:4])
                    annot = page.add_highlight_annot(highlight)
                    annot.set_colors(stroke=color)
                    annot.update()
                    differences.append((page_num, word))

        self.differences.extend(differences)

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

    def show_summary(self):
        self.summary_label.setText(f"Total Differences Found: {len(self.differences)}")

        self.current_diff_index = 0
        self.show_difference()

    def show_difference(self):
        if self.current_diff_index < 0 or self.current_diff_index >= len(self.differences):
            return

        diff = self.differences[self.current_diff_index]
        page_num, word = diff

        # Clear previous tagging content
        for i in reversed(range(self.tagging_layout.count())):
            widget = self.tagging_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        description = QLabel(f"PDF 1: {self.pdf1_path.split('/')[-1]}\nPDF 2: {self.pdf2_path.split('/')[-1]}\nPage: {page_num + 1}\nWord: {word[4]}")
        self.tagging_layout.addWidget(description)

        button_group = QButtonGroup(self.tagging_container)
        radio_no = QRadioButton("No Aplica")
        radio_yes = QRadioButton("Si Aplica")
        radio_other = QRadioButton("Otro")
        button_group.addButton(radio_no)
        button_group.addButton(radio_yes)
        button_group.addButton(radio_other)

        self.tagging_layout.addWidget(radio_no)
        self.tagging_layout.addWidget(radio_yes)
        self.tagging_layout.addWidget(radio_other)

        # Save current selection
        radio_no.clicked.connect(lambda: self.save_tag(word, "No Aplica"))
        radio_yes.clicked.connect(lambda: self.save_tag(word, "Si Aplica"))
        radio_other.clicked.connect(lambda: self.save_tag(word, "Otro"))

        self.highlight_specific_difference(page_num, word)

    def navigate_difference(self, step):
        if 0 <= self.current_diff_index < len(self.differences):
            self.highlight_specific_difference(self.differences[self.current_diff_index][0], self.differences[self.current_diff_index][1], False)

        self.current_diff_index += step
        if self.current_diff_index < 0:
            self.current_diff_index = 0
        elif self.current_diff_index >= len(self.differences):
            self.current_diff_index = len(self.differences) - 1

        self.show_difference()

    def highlight_specific_difference(self, page_num, word, highlight=True):
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)

        color = (1, 0, 0) if highlight else (1, 1, 0)  # Rojo si se está resaltando, amarillo si no

        for doc, words in [(doc1, self.pdf1_words), (doc2, self.pdf2_words)]:
            page = doc.load_page(page_num)
            for w in words[page_num]:
                if w == word:
                    annot = page.add_highlight_annot(fitz.Rect(w[:4]))
                    annot.set_colors(stroke=color)
                    annot.update()

        temp_pdf1_path = tempfile.mktemp(suffix=".pdf")
        temp_pdf2_path = tempfile.mktemp(suffix=".pdf")
        doc1.save(temp_pdf1_path)
        doc2.save(temp_pdf2_path)
        doc1.close()
        doc2.close()

        self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
        self.display_pdfs(self.pdf2_layout, temp_pdf2_path)

    def save_tag(self, word, tag):
        self.tagged_differences.append((word, tag))

    def save_tags(self):
        for word, tag in self.tagged_differences:
            print(f"Word: {word[4]}, Tag: {tag}")

        QMessageBox.information(self, "Saved", "Tags have been saved and printed to the console.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
