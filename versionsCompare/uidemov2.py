import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QButtonGroup, QGroupBox
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

        self.summary_widget = QWidget()
        self.summary_layout = QVBoxLayout()
        self.summary_widget.setLayout(self.summary_layout)
        
        self.difference_summary_label = QLabel("Total Differences: 0", self)
        self.summary_layout.addWidget(self.difference_summary_label)

        self.difference_area = QVBoxLayout()
        self.current_difference_index = 0
        self.differences = []
        self.difference_labels = []
        self.difference_radio_buttons = []
        self.tagged_differences = []

        self.difference_group = QGroupBox("Tag Differences")
        self.difference_group.setLayout(self.difference_area)
        self.summary_layout.addWidget(self.difference_group)

        self.radio_group = QButtonGroup(self)

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_prev_difference)
        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_difference)
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_tags)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.save_button)
        self.summary_layout.addLayout(self.button_layout)

        self.splitter.addWidget(self.pdf1_scroll)
        self.splitter.addWidget(self.pdf2_scroll)
        self.splitter.addWidget(self.summary_widget)
        
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

            self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path)
            
            self.differences = self.find_differences(self.pdf1_words, self.pdf2_words)
            self.difference_summary_label.setText(f"Total Differences: {len(self.differences)}")
            self.tagged_differences = [None] * len(self.differences)
            self.show_difference(0)

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

    def find_differences(self, words1, words2):
        differences = []

        for page_num in range(len(words1)):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))
            diff1 = words1_set - words2_set
            diff2 = words2_set - words1_set

            for word in diff1:
                differences.append((page_num, word))
            for word in diff2:
                differences.append((page_num, word))

        return differences

    def show_difference(self, index):
        if index < 0 or index >= len(self.differences):
            return

        self.current_difference_index = index
        page_num, word = self.differences[index]

        for i in range(len(self.difference_labels)):
            self.difference_labels[i].deleteLater()
        self.difference_labels.clear()
        self.difference_radio_buttons.clear()

        label = QLabel(f"Difference {index + 1}/{len(self.differences)}: {word}")
        self.difference_labels.append(label)
        self.difference_area.addWidget(label)

        radio_button1 = QRadioButton("No Aplica")
        radio_button2 = QRadioButton("Si Aplica")
        radio_button3 = QRadioButton("Otro")
        self.radio_group.addButton(radio_button1)
        self.radio_group.addButton(radio_button2)
        self.radio_group.addButton(radio_button3)

        self.difference_area.addWidget(radio_button1)
        self.difference_area.addWidget(radio_button2)
        self.difference_area.addWidget(radio_button3)

        self.difference_radio_buttons.append(radio_button1)
        self.difference_radio_buttons.append(radio_button2)
        self.difference_radio_buttons.append(radio_button3)

        if self.tagged_differences[index] == "No Aplica":
            radio_button1.setChecked(True)
        elif self.tagged_differences[index] == "Si Aplica":
            radio_button2.setChecked(True)
        elif self.tagged_differences[index] == "Otro":
            radio_button3.setChecked(True)

        # Highlight current difference
        self.highlight_current_difference(page_num, word)

    def show_prev_difference(self):
        self.save_current_tag()
        if self.current_difference_index > 0:
            self.show_difference(self.current_difference_index - 1)

    def show_next_difference(self):
        self.save_current_tag()
        if self.current_difference_index < len(self.differences) - 1:
            self.show_difference(self.current_difference_index + 1)

    def save_current_tag(self):
        if self.radio_group.checkedButton():
            self.tagged_differences[self.current_difference_index] = self.radio_group.checkedButton().text()

    def save_tags(self):
        self.save_current_tag()
        # Save the tags to a file or database here
        print("Tagged Differences:", self.tagged_differences)

    def highlight_current_difference(self, page_num, word):
        # Clear previous highlights and add new highlight for the current difference
        self.compare_pdfs()
        # Add specific highlight code here based on page_num and word

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
