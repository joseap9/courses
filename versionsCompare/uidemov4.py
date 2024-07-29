import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import fitz  # PyMuPDF
import tempfile

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        self.main_layout = QVBoxLayout()  # Main layout with vertical alignment

        # Top layout for select buttons
        self.top_layout = QHBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.top_layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.top_layout.addWidget(self.button2)

        self.main_layout.addLayout(self.top_layout)

        # Middle layout for PDFs and navigation buttons
        self.middle_layout = QHBoxLayout()

        # Left layout for PDFs
        self.left_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)
        self.left_layout.addWidget(self.splitter)

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

        # Right layout for navigation buttons and labels
        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignBottom)  # Align buttons to the bottom

        self.difference_label = QLabel(self)
        self.right_layout.addWidget(self.difference_label)

        self.radio_button_group = QButtonGroup(self)

        self.radio_no_aplica = QRadioButton("No Aplica", self)
        self.radio_no_aplica.setChecked(True)
        self.radio_button_group.addButton(self.radio_no_aplica)
        self.right_layout.addWidget(self.radio_no_aplica)

        self.radio_aplica = QRadioButton("Aplica", self)
        self.radio_button_group.addButton(self.radio_aplica)
        self.right_layout.addWidget(self.radio_aplica)

        self.radio_otro = QRadioButton("Otro", self)
        self.radio_button_group.addButton(self.radio_otro)
        self.radio_otro.toggled.connect(self.toggle_other_input)
        self.right_layout.addWidget(self.radio_otro)

        self.other_input = QLineEdit(self)
        self.other_input.setPlaceholderText("Escriba el otro aquí")
        self.other_input.setVisible(False)
        self.right_layout.addWidget(self.other_input)

        self.prev_page_button = QPushButton("Previous Page", self)
        self.prev_page_button.clicked.connect(self.prev_page)
        self.prev_page_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_page_button)

        self.next_page_button = QPushButton("Next Page", self)
        self.next_page_button.clicked.connect(self.next_page)
        self.next_page_button.setEnabled(False)
        self.right_layout.addWidget(self.next_page_button)

        self.prev_button = QPushButton("Previous Difference", self)
        self.prev_button.clicked.connect(self.prev_difference)
        self.prev_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next Difference", self)
        self.next_button.clicked.connect(self.next_difference)
        self.next_button.setEnabled(False)
        self.right_layout.addWidget(self.next_button)

        self.middle_layout.addLayout(self.left_layout, 8)  # Give more space to PDFs
        self.middle_layout.addLayout(self.right_layout, 1)  # Give less space to buttons

        self.main_layout.addLayout(self.middle_layout)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        self.differences = []
        self.current_difference_index = -1
        self.temp_pdf1_path = None
        self.temp_pdf2_path = None
        self.labels = {}  # Dictionary to store labels for differences
        self.current_page = 0

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
            self.current_page = 0
            self.compare_pdfs()

    def load_second_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.button2.setText(fileName.split('/')[-1])
            self.pdf2_path = fileName
            self.current_page = 0
            self.compare_pdfs()

    def extract_text_and_positions(self, file_path, page_num):
        document = fitz.open(file_path)
        text = []
        words = []

        if page_num < document.page_count:
            page = document.load_page(page_num)
            text.append(page.get_text())
            word_list = page.get_text("words")
            words.append(word_list)

        return text, words

    def compare_pdfs(self):
        if self.pdf1_path and self.pdf2_path:
            self.process_page(self.current_page)

    def process_page(self, page_num):
        self.pdf1_text, self.pdf1_words = self.extract_text_and_positions(self.pdf1_path, page_num)
        self.pdf2_text, self.pdf2_words = self.extract_text_and_positions(self.pdf2_path, page_num)

        self.differences = self.find_differences(self.pdf1_words, self.pdf2_words)
        if self.differences:
            self.current_difference_index = 0
            self.update_navigation_buttons()

        self.temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_words, self.pdf2_words)
        self.temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_words, self.pdf1_words)

        self.display_pdfs(self.pdf1_layout, self.temp_pdf1_path, page_num)
        self.display_pdfs(self.pdf2_layout, self.temp_pdf2_path, page_num)

        self.highlight_current_difference()

    def find_differences(self, words1, words2):
        differences = []
        for page_num in range(min(len(words1), len(words2))):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))
            page_differences = [(page_num, word, self.find_closest_word(word, words2[page_num])) for word in words1[page_num] if word[4] not in words2_set]
            differences.extend(page_differences)
        return differences

    def find_closest_word(self, word, words_list):
        min_distance = float('inf')
        closest_word = None
        for w in words_list:
            distance = self.euclidean_distance(word, w)
            if distance < min_distance:
                min_distance = distance
                closest_word = w
        return closest_word[4] if closest_word and min_distance < 50 else "ND"

    def euclidean_distance(self, word1, word2):
        x1, y1, x2, y2 = word1[:4]
        x1_center = (x1 + x2) / 2
        y1_center = (y1 + y2) / 2
        x3, y3, x4, y4 = word2[:4]
        x3_center = (x3 + x4) / 2
        y3_center = (y3 + y4) / 2
        return ((x1_center - x3_center) ** 2 + (y1_center - y3_center) ** 2) ** 0.5

    def highlight_differences(self, file_path, words1, words2):
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            if page_num >= len(words1) or page_num >= len(words2):
                continue  # Skip processing if no counterpart in the other PDF

            page = doc.load_page(page_num)

            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word in words1[page_num]:
                if word[4] not in words2_set:
                    highlight = fitz.Rect(word[:4])
                    page.add_highlight_annot(highlight)

        temp_pdf_path = tempfile.mktemp(suffix=".pdf")
        doc.save(temp_pdf_path)
        doc.close()
        return temp_pdf_path

    def display_pdfs(self, layout, file_path, page_num):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(file_path)
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        temp_image_path = tempfile.mktemp(suffix=".png")
        pix.save(temp_image_path)
        label = QLabel(self)
        label.setPixmap(QPixmap(temp_image_path).scaled(600, 800, Qt.KeepAspectRatio))
        layout.addWidget(label)

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_difference_index > 0)
        self.next_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_page_button.setEnabled(self.current_page > 0)
        self.next_page_button.setEnabled(self.current_page < min(len(self.pdf1_text), len(self.pdf2_text)) - 1)  # Enable only if there are more pages
        self.update_difference_label()

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            page_num, word, matching_word = self.differences[self.current_difference_index]

            # Load and highlight in first PDF
            doc1 = fitz.open(self.temp_pdf1_path)
            page1 = doc1.load_page(page_num)
            highlight1 = fitz.Rect(word[:4])
            extra_highlight1 = page1.add_rect_annot(highlight1)
            extra_highlight1.set_colors(stroke=(1, 0, 0), fill=None)  # Red color for the border
            extra_highlight1.update()
            temp_pdf1_path = tempfile.mktemp(suffix=".pdf")
            doc1.save(temp_pdf1_path)
            doc1.close()
            self.display_pdfs(self.pdf1_layout, temp_pdf1_path, page_num)
            self.temp_pdf1_path = temp_pdf1_path

            # Load and highlight in second PDF
            doc2 = fitz.open(self.temp_pdf2_path)
            page2 = doc2.load_page(page_num)
            highlight2 = fitz.Rect(word[:4])
            extra_highlight2 = page2.add_rect_annot(highlight2)
            extra_highlight2.set_colors(stroke=(1, 0, 0), fill=None)  # Red color for the border
            extra_highlight2.update()
            temp_pdf2_path = tempfile.mktemp(suffix=".pdf")
            doc2.save(temp_pdf2_path)
            doc2.close()
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path, page_num)
            self.temp_pdf2_path = temp_pdf2_path

            self.update_difference_label()

            # Restore previous label if exists
            if (page_num, word[4]) in self.labels:
                label = self.labels[(page_num, word[4])]
                if label == "No Aplica":
                    self.radio_no_aplica.setChecked(True)
                elif label == "Aplica":
                    self.radio_aplica.setChecked(True)
                else:
                    self.radio_otro.setChecked(True)
                    self.other_input.setText(label)
                    self.other_input.setVisible(True)
            else:
                self.radio_no_aplica.setChecked(True)
                self.other_input.setVisible(False)
                self.other_input.clear()

    def update_difference_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            page_num, word, matching_word = self.differences[self.current_difference_index]
            self.difference_label.setText(f"Difference {self.current_difference_index + 1} of {len(self.differences)}: Page {page_num + 1}, Word in PDF1: '{word[4]}', Word in PDF2: '{matching_word}'")

    def toggle_other_input(self):
        if self.radio_otro.isChecked():
            self.other_input.setVisible(True)
        else:
            self.other_input.setVisible(False)
            self.other_input.clear()

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.save_current_label()
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.save_current_label()
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def next_page(self):
        self.save_current_label()
        self.current_page += 1
        self.compare_pdfs()

    def prev_page(self):
        self.save_current_label()
        self.current_page -= 1
        self.compare_pdfs()

    def save_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            page_num, word, _ = self.differences[self.current_difference_index]
            if self.radio_no_aplica.isChecked():
                self.labels[(page_num, word[4])] = "No Aplica"
            elif self.radio_aplica.isChecked():
                self.labels[(page_num, word[4])] = "Aplica"
            elif self.radio_otro.isChecked():
                self.labels[(page_num, word[4])] = self.other_input.text()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
