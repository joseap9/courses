import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QTextEdit
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

        # Right layout for navigation buttons
        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignBottom)  # Align buttons to the bottom

        self.difference_description = QTextEdit(self)
        self.difference_description.setReadOnly(True)
        self.right_layout.addWidget(self.difference_description)

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.prev_difference)
        self.prev_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
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
        highlights = []

        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text.append(page.get_text())
            highlight_list = page.search_for(" ")
            highlights.append(highlight_list)

        return text, highlights

    def compare_pdfs(self):
        if self.pdf1_path and self.pdf2_path:
            self.pdf1_text, self.pdf1_highlights = self.extract_text_and_positions(self.pdf1_path)
            self.pdf2_text, self.pdf2_highlights = self.extract_text_and_positions(self.pdf2_path)

            self.differences = self.find_differences(self.pdf1_highlights, self.pdf2_highlights)
            if self.differences:
                self.current_difference_index = 0
                self.update_navigation_buttons()
                self.update_difference_description()

            self.temp_pdf1_path = self.highlight_differences(self.pdf1_path, self.pdf1_highlights, self.pdf2_highlights)
            self.temp_pdf2_path = self.highlight_differences(self.pdf2_path, self.pdf2_highlights, self.pdf1_highlights)

            self.display_pdfs(self.pdf1_layout, self.temp_pdf1_path)
            self.display_pdfs(self.pdf2_layout, self.temp_pdf2_path)

            self.highlight_current_difference()

    def find_differences(self, highlights1, highlights2):
        differences = []
        for page_num in range(min(len(highlights1), len(highlights2))):
            highlights1_set = set((highlight.x0, highlight.y0, highlight.x1, highlight.y1) for highlight in highlights1[page_num])
            highlights2_set = set((highlight.x0, highlight.y0, highlight.x1, highlight.y1) for highlight in highlights2[page_num])
            page_differences = [(page_num, highlight, "Not in this PDF") for highlight in highlights1[page_num] if (highlight.x0, highlight.y0, highlight.x1, highlight.y1) not in highlights2_set]
            page_differences += [(page_num, "Not in this PDF", highlight) for highlight in highlights2[page_num] if (highlight.x0, highlight.y0, highlight.x1, highlight.y1) not in highlights1_set]
            differences.extend(page_differences)
        return differences

    def highlight_differences(self, file_path, highlights1, highlights2):
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            if page_num < len(highlights1) and page_num < len(highlights2):
                highlights1_set = set((highlight.x0, highlight.y0, highlight.x1, highlight.y1) for highlight in highlights1[page_num])
                highlights2_set = set((highlight.x0, highlight.y0, highlight.x1, highlight.y1) for highlight in highlights2[page_num])

                for highlight in highlights1[page_num]:
                    if (highlight.x0, highlight.y0, highlight.x1, highlight.y1) not in highlights2_set:
                        page.add_highlight_annot(highlight)
            elif page_num < len(highlights1):
                for highlight in highlights1[page_num]:
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

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_difference_index > 0)
        self.next_button.setEnabled(self.current_difference_index < len(self.differences) - 1)

    def update_difference_description(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            page_num, highlight1, highlight2 = self.differences[self.current_difference_index]
            if highlight1 == "Not in this PDF":
                description = f"Page {page_num + 1}\nDifference:\nPDF1: Not in this PDF\nPDF2: {highlight2}"
            elif highlight2 == "Not in this PDF":
                description = f"Page {page_num + 1}\nDifference:\nPDF1: {highlight1}\nPDF2: Not in this PDF"
            else:
                description = f"Page {page_num + 1}\nDifference:\nPDF1: {highlight1}\nPDF2: {highlight2}"
            self.difference_description.setText(description)

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            page_num, highlight1, highlight2 = self.differences[self.current_difference_index]

            # Load and highlight in first PDF
            doc1 = fitz.open(self.temp_pdf1_path)
            page1 = doc1.load_page(page_num)
            if highlight1 != "Not in this PDF":
                extra_highlight1 = page1.add_rect_annot(highlight1)
                extra_highlight1.set_colors(stroke=(1, 0, 0), fill=None)  # Red color for the border
                extra_highlight1.update()
            temp_pdf1_path = tempfile.mktemp(suffix=".pdf")
            doc1.save(temp_pdf1_path)
            doc1.close()
            self.display_pdfs(self.pdf1_layout, temp_pdf1_path)
            self.temp_pdf1_path = temp_pdf1_path

            # Load and highlight in second PDF
            doc2 = fitz.open(self.temp_pdf2_path)
            page2 = doc2.load_page(page_num)
            if highlight2 != "Not in this PDF":
                extra_highlight2 = page2.add_rect_annot(highlight2)
                extra_highlight2.set_colors(stroke=(1, 0, 0), fill=None)  # Red color for the border
                extra_highlight2.update()
            temp_pdf2_path = tempfile.mktemp(suffix=".pdf")
            doc2.save(temp_pdf2_path)
            doc2.close()
            self.display_pdfs(self.pdf2_layout, temp_pdf2_path)
            self.temp_pdf2_path = temp_pdf2_path

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.update_difference_description()
            self.highlight_current_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.update_difference_description()
            self.highlight_current_difference()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())