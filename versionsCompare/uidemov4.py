import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup, QStackedWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import fitz  # PyMuPDF
import tempfile

class LoadPDFThread(QThread):
    page_loaded = pyqtSignal(int, str, str)  # page number, first pdf image path, second pdf image path

    def __init__(self, pdf1_path, pdf2_path, page_num):
        super().__init__()
        self.pdf1_path = pdf1_path
        self.pdf2_path = pdf2_path
        self.page_num = page_num

    def run(self):
        # Load and convert the page to images
        doc1 = fitz.open(self.pdf1_path)
        doc2 = fitz.open(self.pdf2_path)
        
        page1 = doc1.load_page(self.page_num)
        pix1 = page1.get_pixmap()
        temp_image1 = tempfile.mktemp(suffix=".png")
        pix1.save(temp_image1)
        
        page2 = doc2.load_page(self.page_num)
        pix2 = page2.get_pixmap()
        temp_image2 = tempfile.mktemp(suffix=".png")
        pix2.save(temp_image2)

        self.page_loaded.emit(self.page_num, temp_image1, temp_image2)

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        self.main_layout = QVBoxLayout()

        self.top_layout = QHBoxLayout()
        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.top_layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.top_layout.addWidget(self.button2)

        self.main_layout.addLayout(self.top_layout)

        self.middle_layout = QHBoxLayout()
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

        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignBottom)

        self.loading_label = QLabel(self)
        self.loading_label.setText("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setVisible(False)
        self.right_layout.addWidget(self.loading_label)

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

        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        self.right_layout.addWidget(self.next_button)

        self.middle_layout.addLayout(self.left_layout, 8)
        self.middle_layout.addLayout(self.right_layout, 1)
        self.main_layout.addLayout(self.middle_layout)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        self.pdf1_path = None
        self.pdf2_path = None
        self.current_page = 0
        self.total_pages = 0

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

    def compare_pdfs(self):
        if self.pdf1_path and self.pdf2_path:
            self.current_page = 0
            self.load_page(self.current_page)
            self.prev_button.setEnabled(False)

    def load_page(self, page_num):
        self.loading_label.setVisible(True)
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)

        self.thread = LoadPDFThread(self.pdf1_path, self.pdf2_path, page_num)
        self.thread.page_loaded.connect(self.on_page_loaded)
        self.thread.start()

    def on_page_loaded(self, page_num, temp_image1, temp_image2):
        self.loading_label.setVisible(False)

        self.pdf1_layout.itemAt(0).widget().deleteLater() if self.pdf1_layout.count() > 0 else None
        self.pdf2_layout.itemAt(0).widget().deleteLater() if self.pdf2_layout.count() > 0 else None

        label1 = QLabel(self)
        label1.setPixmap(QPixmap(temp_image1).scaled(600, 800, Qt.KeepAspectRatio))
        self.pdf1_layout.addWidget(label1)

        label2 = QLabel(self)
        label2.setPixmap(QPixmap(temp_image2).scaled(600, 800, Qt.KeepAspectRatio))
        self.pdf2_layout.addWidget(label2)

        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_page(self.current_page)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page(self.current_page)

    def toggle_other_input(self):
        self.other_input.setVisible(self.radio_otro.isChecked())
        if not self.radio_otro.isChecked():
            self.other_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())