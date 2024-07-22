import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QScrollArea, QSplitter, QMessageBox, QDialog, QFormLayout, QRadioButton,
    QButtonGroup, QLineEdit
)
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

        self.differences = []  # Lista para almacenar las diferencias
        self.current_diff_index = -1  # Índice de la diferencia actual

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

            self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path)

            self.show_summary()

    def highlight_differences(self, file_path, words1, words2):
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
                        page.add_highlight_annot(highlight)
                        differences.append((page_num, word))

            elif page_num < len(words1):
                for word in words1[page_num]:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)
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
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Total Differences Found: {len(self.differences)}")
        msg.setWindowTitle("Summary of Differences")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

        self.current_diff_index = 0
        self.show_difference()

    def show_difference(self):
        if self.current_diff_index < 0 or self.current_diff_index >= len(self.differences):
            return

        diff = self.differences[self.current_diff_index]
        page_num, word = diff

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Difference {self.current_diff_index + 1} of {len(self.differences)}")

        layout = QFormLayout(dialog)

        description = QLabel(f"PDF 1: {self.pdf1_path.split('/')[-1]}\nPDF 2: {self.pdf2_path.split('/')[-1]}\nPage: {page_num + 1}\nWord: {word[4]}")
        layout.addRow(description)

        button_group = QButtonGroup(dialog)
        radio_no = QRadioButton("No Aplica")
        radio_yes = QRadioButton("Si Aplica")
        radio_other = QRadioButton("Otro")
        button_group.addButton(radio_no)
        button_group.addButton(radio_yes)
        button_group.addButton(radio_other)

        layout.addRow(radio_no)
        layout.addRow(radio_yes)
        layout.addRow(radio_other)

        next_button = QPushButton("Next", dialog)
        prev_button = QPushButton("Previous", dialog)
        close_button = QPushButton("Close", dialog)

        next_button.clicked.connect(lambda: self.navigate_difference(dialog, 1))
        prev_button.clicked.connect(lambda: self.navigate_difference(dialog, -1))
        close_button.clicked.connect(dialog.accept)

        layout.addRow(prev_button, next_button)
        layout.addRow(close_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def navigate_difference(self, dialog, step):
        dialog.accept()
        self.current_diff_index += step
        if self.current_diff_index < 0:
            self.current_diff_index = 0
        elif self.current_diff_index >= len(self.differences):
            self.current_diff_index = len(self.differences) - 1

        self.show_difference()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
