import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        # Layout principal horizontal que contendrá las tres secciones verticales
        self.main_layout = QHBoxLayout()

        # Sección para la selección de PDFs y navegación entre páginas
        self.left_layout = QVBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.left_layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.left_layout.addWidget(self.button2)

        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Prev", self)
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        self.navigation_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        self.navigation_layout.addWidget(self.next_button)

        self.left_layout.addLayout(self.navigation_layout)

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

        # Añadir la sección izquierda (dos PDFs y navegación) al layout principal
        self.main_layout.addLayout(self.left_layout)

        # Sección derecha (la tercera columna)
        self.right_frame = QFrame(self)
        self.right_frame.setFrameShape(QFrame.StyledPanel)
        self.right_frame.setFrameShadow(QFrame.Sunken)
        self.right_frame.setFixedWidth(200)  # Ajusta la anchura fija de la sección derecha

        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        self.difference_label = QLabel(self)
        self.difference_label.setWordWrap(True)  # Permite que el texto se ajuste a varias líneas
        self.difference_label.setAlignment(Qt.AlignCenter)  # Alinea el texto en el centro
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

        # Añadir la sección derecha al layout principal
        self.main_layout.addWidget(self.right_frame)

        container = QWidget()
        container.setLayout(self.main_layout)
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
            self.highlight_current_difference()  # Marcar automáticamente la primera diferencia

    def highlight_differences(self, doc, words1, words2, page_num):
        differences1 = []
        differences2 = []

        if page_num < len(words1) and page_num < len(words2):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word1 in words1[page_num]:
                if word1[4] not in words2_set:
                    highlight = fitz.Rect(word1[:4])
                    doc[page_num].add_highlight_annot(highlight)
                    differences1.append(word1)

            for word2 in words2[page_num]:
                if word2[4] not in words1_set:
                    highlight = fitz.Rect(word2[:4])
                    doc[page_num].add_highlight_annot(highlight)
                    differences2.append(word2)

            # Ajustar para que las diferencias que sobran en un párrafo no continúen en el otro
            max_differences = max(len(differences1), len(differences2))
            differences1 = differences1[:max_differences]
            differences2 = differences2[:max_differences]

        return doc, differences1, differences2

    def load_page_pair(self, page_num):
        # Cargar y resaltar diferencias en PDF1
        doc1 = self.temp_pdf1_paths[self.current_page] if len(self.temp_pdf1_paths) > self.current_page else fitz.open(self.pdf1_path)
        doc1, differences1, differences2 = self.highlight_differences(doc1, self.pdf1_words, self.pdf2_words, page_num)

        # Cargar y resaltar diferencias en PDF2
        doc2 = self.temp_pdf2_paths[self.current_page] if len(self.temp_pdf2_paths) > self.current_page else fitz.open(self.pdf2_path)
        doc2, _, _ = self.highlight_differences(doc2, self.pdf2_words, self.pdf1_words, page_num)

        self.display_pdfs(self.pdf1_layout, doc1, page_num)
        self.display_pdfs(self.pdf2_layout, doc2, page_num)

        self.differences = list(zip(differences1, differences2))  # Combina las diferencias de ambos PDFs
        self.current_difference_index = 0
        self.update_navigation_buttons()

        # Guardar los documentos con las anotaciones
        if len(self.temp_pdf1_paths) <= self.current_page:
            self.temp_pdf1_paths.append(doc1)
        else:
            self.temp_pdf1_paths[self.current_page] = doc1

        if len(self.temp_pdf2_paths) <= self.current_page:
            self.temp_pdf2_paths.append(doc2)
        else:
            self.temp_pdf2_paths[self.current_page] = doc2

    def display_pdfs(self, layout, doc, page_num):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        label = QLabel(self)
        label.setPixmap(QPixmap.fromImage(img))
        layout.addWidget(label)

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            word1, word2 = self.differences[self.current_difference_index]

            page_num = self.current_page

            # Resalta en el primer PDF
            doc1 = self.temp_pdf1_paths[self.current_page]
            highlight1 = fitz.Rect(word1[:4])
            doc1[page_num].add_rect_annot(highlight1)
            self.display_pdfs(self.pdf1_layout, doc1, page_num)

            # Resalta en el segundo PDF
            doc2 = self.temp_pdf2_paths[self.current_page]
            highlight2 = fitz.Rect(word2[:4])
            doc2[page_num].add_rect_annot(highlight2)
            self.display_pdfs(self.pdf2_layout, doc2, page_num)

            # Actualizar el QLabel con el texto exacto resaltado de ambos PDFs
            self.difference_label.setText(f"PDF1: '{word1[4]}'\nPDF2: '{word2[4]}'")

    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        self.update_difference_label()

    def update_difference_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            word1, word2 = self.differences[self.current_difference_index]
            self.difference_label.setText(f"PDF1: '{word1[4]}'\nPDF2: '{word2[4]}'")

    def toggle_other_input(self):
        if self.radio_otro.isChecked():
            self.other_input.setVisible(True)
        else:
            self.other_input.setVisible(False)
            self.other_input.clear()

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.prev_button.setEnabled(True)
            
            # Cargar la siguiente página si no está cargada
            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)
            
            if self.current_page == self.total_pages - 1:
                self.next_button.setEnabled(False)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.next_button.setEnabled(True)
            
            # Cargar la página anterior si no está cargada
            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)
            
            if self.current_page == 0:
                self.prev_button.setEnabled(False)

    def save_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            word1, word2 = self.differences[self.current_difference_index]
            if self.radio_no_aplica.isChecked():
                self.labels[(self.current_page, word1[4])] = "No Aplica"
            elif self.radio_aplica.isChecked():
                self.labels[(self.current_page, word1[4])] = "Aplica"
            elif self.radio_otro.isChecked():
                self.labels[(self.current_page, word1[4])] = self.other_input.text()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
