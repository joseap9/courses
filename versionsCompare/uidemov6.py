import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup, QSpacerItem, QSizePolicy
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

        # Right layout for navigation buttons and labels
        self.right_layout = QVBoxLayout()

        # Add a spacer to reduce the height of the difference label area
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_layout.addItem(spacer)

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

        self.prev_diff_button = QPushButton("Previous Difference", self)
        self.prev_diff_button.clicked.connect(self.prev_difference)
        self.prev_diff_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Difference", self)
        self.next_diff_button.clicked.connect(self.next_difference)
        self.next_diff_button.setEnabled(False)
        self.right_layout.addWidget(self.next_diff_button)

        self.layout.addLayout(self.right_layout)

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
        self.current_difference_index = -1
        self.labels = {}  # Dictionary to store labels for differences

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

    def highlight_differences(self, doc, words1, words2, page_num):
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
        return doc

    def load_page_pair(self, page_num):
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)
        
        doc1 = self.highlight_differences(doc1, self.pdf1_words, self.pdf2_words, page_num)
        doc2 = self.highlight_differences(doc2, self.pdf2_words, self.pdf1_words, page_num)

        self.display_pdfs(self.pdf1_layout, doc1, page_num)
        self.display_pdfs(self.pdf2_layout, doc2, page_num)

        self.find_differences(self.pdf1_words, self.pdf2_words)
        self.update_navigation_buttons()

    def display_pdfs(self, layout, doc, page_num):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        label = QLabel(self)
        label.setPixmap(QPixmap.fromImage(img))
        layout.addWidget(label)

    def find_differences(self, words1, words2):
        self.differences = []
        if self.current_page < len(words1) and self.current_page < len(words2):
            words1_set = set((word[4] for word in words1[self.current_page]))
            words2_set = set((word[4] for word in words2[self.current_page]))
            page_differences = [(self.current_page, word, self.find_closest_word(word, words2[self.current_page])) for word in words1[self.current_page] if word[4] not in words2_set]
            self.differences.extend(page_differences)
        if self.differences:
            self.current_difference_index = 0
            self.update_navigation_buttons()

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

    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        self.update_difference_label()

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            page_num, word, matching_word = self.differences[self.current_difference_index]

            # Load and highlight in first PDF
            doc1 = fitz.open(self.pdf1_path)
            doc1 = self.highlight_differences(doc1, self.pdf1_words, self.pdf2_words, page_num)
            highlight1 = fitz.Rect(word[:4])
            extra_highlight1 = doc1[page_num].add_rect_annot(highlight1)
            extra_highlight1.set_colors(stroke=(1, 0, 0), fill=None)  # Red color for the border
            extra_highlight1.update()
            self.display_pdfs(self.pdf1_layout, doc1, page_num)
            if len(self.temp_pdf1_paths) <= self.current_page:
                self.temp_pdf1_paths.append(doc1)
            else:
                self.temp_pdf1_paths[self.current_page] = doc1

            # Load and highlight in second PDF
            doc2 = fitz.open(self.pdf2_path)
            doc2 = self.highlight_differences(doc2, self.pdf2_words, self.pdf1_words, page_num)
            highlight2 = fitz.Rect(word[:4])
            extra_highlight2 = doc2[page_num].add_rect_annot(highlight2)
            extra_highlight2.set_colors(stroke=(1, 0, 0), fill=None)  # Red color for the border
            extra_highlight2.update()
            self.display_pdfs(self.pdf2_layout, doc2, page_num)
            if len(self.temp_pdf2_paths) <= self.current_page:
                self.temp_pdf2_paths.append(doc2)
            else:
                self.temp_pdf2_paths[self.current_page] = doc2

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
        if self.current_page < self.total_pages - 1:
            self.save_current_label()
            self.current_page += 1
            self.prev_button.setEnabled(True)
            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)
            if self.current_page == self.total_pages - 1:
                self.next_button.setEnabled(False)

    def prev_page(self):
        if self.current_page > 0:
            self.save_current_label()
            self.current_page -= 1
            self.next_button.setEnabled(True)
            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)
            if self.current_page == 0:
                self.prev_button.setEnabled(False)

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
