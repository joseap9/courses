import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout, QLabel, QScrollArea
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QByteArray
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1600, 900)

        layout = QVBoxLayout()

        # Sección de botones para cargar PDFs
        self.button_layout = QHBoxLayout()

        self.load_pdf1_button = QPushButton("Load First PDF", self)
        self.load_pdf1_button.clicked.connect(self.load_first_pdf)
        self.button_layout.addWidget(self.load_pdf1_button)

        self.load_pdf2_button = QPushButton("Load Second PDF", self)
        self.load_pdf2_button.clicked.connect(self.load_second_pdf)
        self.button_layout.addWidget(self.load_pdf2_button)

        layout.addLayout(self.button_layout)

        # Sección de visualización de PDFs
        self.viewer_layout = QHBoxLayout()

        self.pdf1_viewer = QLabel(self)
        self.pdf1_viewer.setAlignment(Qt.AlignTop)
        self.pdf1_scroll = QScrollArea()
        self.pdf1_scroll.setWidgetResizable(True)
        self.pdf1_scroll.setWidget(self.pdf1_viewer)
        self.viewer_layout.addWidget(self.pdf1_scroll)

        self.pdf2_viewer = QLabel(self)
        self.pdf2_viewer.setAlignment(Qt.AlignTop)
        self.pdf2_scroll = QScrollArea()
        self.pdf2_scroll.setWidgetResizable(True)
        self.pdf2_scroll.setWidget(self.pdf2_viewer)
        self.viewer_layout.addWidget(self.pdf2_scroll)

        layout.addLayout(self.viewer_layout)

        # Sección de navegación entre diferencias
        self.navigation_layout = QHBoxLayout()

        self.prev_diff_button = QPushButton("Previous Difference", self)
        self.prev_diff_button.clicked.connect(self.prev_difference)
        self.navigation_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Difference", self)
        self.next_diff_button.clicked.connect(self.next_difference)
        self.navigation_layout.addWidget(self.next_diff_button)

        layout.addLayout(self.navigation_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Inicialización de variables
        self.pdf1_path = None
        self.pdf2_path = None
        self.current_page = 0
        self.total_pages = 0
        self.differences = []
        self.current_difference_index = -1

    def load_first_pdf(self):
        self.pdf1_path, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf)")
        if self.pdf1_path:
            self.extract_differences()

    def load_second_pdf(self):
        self.pdf2_path, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf)")
        if self.pdf2_path:
            self.extract_differences()

    def extract_differences(self):
        if self.pdf1_path and self.pdf2_path:
            doc1 = fitz.open(self.pdf1_path)
            doc2 = fitz.open(self.pdf2_path)
            self.total_pages = min(len(doc1), len(doc2))

            self.differences = []
            for i in range(self.total_pages):
                text1 = doc1[i].get_text("blocks")
                text2 = doc2[i].get_text("blocks")
                differences_in_page = []
                for block1, block2 in zip(text1, text2):
                    if block1[4] != block2[4]:
                        differences_in_page.append((block1, block2))
                if differences_in_page:
                    self.differences.append((i, differences_in_page))

            if self.differences:
                self.current_difference_index = 0
                self.go_to_difference()

    def go_to_difference(self):
        if self.differences:
            diff_page, differences_in_page = self.differences[self.current_difference_index]
            self.current_page = diff_page

            # Resalta las diferencias en ambas páginas
            img1 = self.render_page_with_highlight(self.pdf1_path, differences_in_page, 0)
            img2 = self.render_page_with_highlight(self.pdf2_path, differences_in_page, 1)

            self.display_image(self.pdf1_viewer, img1)
            self.display_image(self.pdf2_viewer, img2)

            self.update_navigation_buttons()

    def render_page_with_highlight(self, pdf_path, differences_in_page, pdf_index):
        doc = fitz.open(pdf_path)
        page = doc[self.current_page]

        # Resalta en amarillo las diferencias
        for block in differences_in_page:
            block_rect = fitz.Rect(block[pdf_index][:4])
            highlight = page.add_highlight_annot(block_rect)
            highlight.update()

        # Añade un recuadro rojo al párrafo completo
        if self.current_difference_index >= 0:
            diff_block = differences_in_page[self.current_difference_index][pdf_index]
            block_rect = fitz.Rect(diff_block[:4])
            rect = page.add_rect_annot(block_rect)
            rect.set_colors({"stroke": (1, 0, 0)})  # Rojo
            rect.update()

        # Renderizar la página a imagen
        pix = page.get_pixmap()
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        return img

    def display_image(self, label, img):
        label.setPixmap(QPixmap.fromImage(img))

    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.current_difference_index += 1
            self.go_to_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.go_to_difference()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
