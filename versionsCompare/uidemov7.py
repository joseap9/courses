import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup, QFrame, QMessageBox, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.setWindowTitle("GMF - PDF Comparer")
        self.setGeometry(100, 100, 1650, 800)

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
        self.prev_button = QPushButton("Previous Page", self)
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        self.navigation_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next Page", self)
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
        self.right_frame.setFixedWidth(300)  # Ajusta la anchura fija de la sección derecha

        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        # Encabezado con el total de diferencias de todo el documento
        self.total_diff_label = QLabel(self)
        self.total_diff_label.setWordWrap(True)
        self.total_diff_label.setAlignment(Qt.AlignCenter)
        self.total_diff_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.right_layout.addWidget(self.total_diff_label)

        # Línea divisora (simula <hr/>)
        self.divider1 = QLabel(self)
        self.divider1.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.right_layout.addWidget(self.divider1)

        # Encabezado para diferencias actuales de la página
        self.page_diff_label = QLabel(self)
        self.page_diff_label.setWordWrap(True)
        self.page_diff_label.setAlignment(Qt.AlignCenter)
        self.page_diff_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.right_layout.addWidget(self.page_diff_label)

        # Cuadro editable para la diferencia actual del PDF 1
        self.pdf1_label = QLabel("PDF 1", self)
        self.pdf1_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.pdf1_label)

        self.pdf1_diff_edit = QTextEdit(self)
        self.pdf1_diff_edit.setReadOnly(True)
        self.right_layout.addWidget(self.pdf1_diff_edit)

        # Línea divisora (simula <hr/>)
        self.divider2 = QLabel(self)
        self.divider2.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.right_layout.addWidget(self.divider2)

        # Cuadro editable para la diferencia actual del PDF 2
        self.pdf2_label = QLabel("PDF 2", self)
        self.pdf2_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.pdf2_label)

        self.pdf2_diff_edit = QTextEdit(self)
        self.pdf2_diff_edit.setReadOnly(True)
        self.right_layout.addWidget(self.pdf2_diff_edit)

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

        # Conexiones de señales para scroll sincronizado
        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        # Inicialización de variables
        self.pdf1_text = None
        self.pdf2_text = None
        self.pdf1_path = None
        self.pdf2_path = None

        self.current_page = 0
        self.total_pages = 0
        self.temp_pdf1_paths = []
        self.temp_pdf2_paths = []

        self.differences = []
        self.current_difference_index = -1
        self.labels = {}
        self.total_diffs = 0  # Variable para almacenar el total de diferencias

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
        self.total_diffs = 0  # Reiniciar el total de diferencias
        if self.pdf1_path and self.pdf2_path:
            self.compare_pdfs()
            self.highlight_current_difference()

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
            self.current_difference_index = 0
            self.update_difference_labels()  # Actualiza las etiquetas de diferencias
            self.highlight_current_difference()


    def load_page_pair(self, page_num):
        doc1 = self.temp_pdf1_paths[self.current_page] if len(self.temp_pdf1_paths) > self.current_page else fitz.open(self.pdf1_path)
        doc1, differences1 = self.highlight_differences(doc1, self.pdf1_words, self.pdf2_words, page_num)

        doc2 = self.temp_pdf2_paths[self.current_page] if len(self.temp_pdf2_paths) > self.current_page else fitz.open(self.pdf2_path)
        doc2, differences2 = self.highlight_differences(doc2, self.pdf2_words, self.pdf1_words, page_num)

        self.display_pdfs(self.pdf1_layout, doc1, page_num)
        self.display_pdfs(self.pdf2_layout, doc2, page_num)

        self.differences = list(zip(differences1, differences2))
        self.current_difference_index = 0
        self.update_navigation_buttons()
        self.update_difference_labels()  # Actualiza las etiquetas de diferencias

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

    def highlight_differences(self, doc, words1, words2, page_num):
        differences = []
        current_diff = []
        non_diff_counter = 0

        if page_num < len(words1) and page_num < len(words2):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word1 in words1[page_num]:
                if word1[4] not in words2_set:
                    if non_diff_counter > 8:  # Si hay más de 8 palabras no diferentes entre diferencias, separar la diferencia actual
                        if current_diff:
                            differences.append(current_diff)
                            current_diff = []
                        non_diff_counter = 0

                    current_diff.append(word1)
                    highlight = fitz.Rect(word1[:4])
                    doc[page_num].add_highlight_annot(highlight)  # Resaltado amarillo
                    non_diff_counter = 0  # Reinicia el contador de palabras no diferentes
                else:
                    if current_diff:
                        non_diff_counter += 1

                    if non_diff_counter > 8 and current_diff:
                        differences.append(current_diff)
                        current_diff = []
                        non_diff_counter = 0

            if current_diff:
                differences.append(current_diff)

        elif page_num < len(words1):  # Caso donde solo hay texto en el primer PDF
            for word1 in words1[page_num]:
                current_diff.append(word1)
                highlight = fitz.Rect(word1[:4])
                doc[page_num].add_highlight_annot(highlight)  # Resaltado amarillo
            differences.append(current_diff)
            self.pdf1_diff_edit.setText(f"Texto encontrado en PDF1 pero no en PDF2:\n{' '.join([word[4] for word in current_diff])}")
        elif page_num < len(words2):  # Caso donde solo hay texto en el segundo PDF
            for word2 in words2[page_num]:
                current_diff.append(word2)
                highlight = fitz.Rect(word2[:4])
                doc[page_num].add_highlight_annot(highlight)  # Resaltado amarillo
            differences.append(current_diff)
            self.pdf2_diff_edit.setText(f"Texto encontrado en PDF2 pero no en PDF1:\n{' '.join([word[4] for word in current_diff])}")

        self.total_diffs += len(differences)  # Acumular diferencias totales
        return doc, differences

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            # Elimina los recuadros rojos anteriores antes de resaltar la siguiente diferencia
            self.clear_highlights()

            diff1, diff2 = self.differences[self.current_difference_index]

            page_num = self.current_page

            if diff1:
                doc1 = self.temp_pdf1_paths[self.current_page]
                start_rect1 = fitz.Rect(diff1[0][:4])
                for word in diff1[1:]:
                    start_rect1 = start_rect1 | fitz.Rect(word[:4])
                rect_annot1 = doc1[page_num].add_rect_annot(start_rect1)
                rect_annot1.set_colors({"stroke": (1, 0, 0)})
                rect_annot1.update()
                self.display_pdfs(self.pdf1_layout, doc1, page_num)

            if diff2:
                doc2 = self.temp_pdf2_paths[self.current_page]
                start_rect2 = fitz.Rect(diff2[0][:4])
                for word in diff2[1:]:
                    start_rect2 = start_rect2 | fitz.Rect(word[:4])
                rect_annot2 = doc2[page_num].add_rect_annot(start_rect2)
                rect_annot2.set_colors({"stroke": (1, 0, 0)})
                rect_annot2.update()
                self.display_pdfs(self.pdf2_layout, doc2, page_num)

            if diff1 and diff2:
                combined_diff1 = ' '.join([word[4] for word in diff1])
                combined_diff2 = ' '.join([word[4] for word in diff2])
                self.pdf1_diff_edit.setText(combined_diff1)
                self.pdf2_diff_edit.setText(combined_diff2)

    def clear_highlights(self):
        # Eliminar solo los recuadros rojos, mantener los resaltados amarillos
        if self.current_page < len(self.temp_pdf1_paths):
            doc1 = self.temp_pdf1_paths[self.current_page]
            for annot in doc1[self.current_page].annots():
                if annot.type[0] == 1:  # Tipo 1 es rectángulo (recuadro rojo)
                    doc1[self.current_page].delete_annot(annot)
            doc1.save(self.pdf1_path)  # Usar save() en lugar de saveIncr()

        if self.current_page < len(self.temp_pdf2_paths):
            doc2 = self.temp_pdf2_paths[self.current_page]
            for annot in doc2[self.current_page].annots():
                if annot.type[0] == 1:  # Tipo 1 es rectángulo (recuadro rojo)
                    doc2[self.current_page].delete_annot(annot)
            doc2.save(self.pdf2_path)  # Usar save() en lugar de saveIncr()




    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        self.update_difference_labels()

    def update_difference_labels(self):
        total_page_diffs = len(self.differences)

        self.total_diff_label.setText(f"Diferencias totales en el documento: {self.total_diffs}")
        self.page_diff_label.setText(f"Página {self.current_page + 1} - Diferencia {self.current_difference_index + 1} de {total_page_diffs}")

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
        # Verificar si todas las diferencias han sido revisadas antes de cambiar de página
        unrevised_diffs = len(self.differences) - self.current_difference_index - 1
        if unrevised_diffs > 0:
            reply = QMessageBox.question(self, 'Diferencias sin revisar',
                                         f'Hay {unrevised_diffs} diferencias que no se han visto. ¿Deseas marcarlas como "No Aplica"?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                while self.current_difference_index < len(self.differences) - 1:
                    self.current_difference_index += 1
                    self.save_current_label()  # Marca como "No Aplica"

        # Solo pasar a la siguiente página si se presiona "Sí"
        if reply == QMessageBox.Yes and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.prev_button.setEnabled(True)

            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)

            # Resaltar la primera diferencia automáticamente en la nueva página
            self.current_difference_index = 0
            self.highlight_current_difference()
            self.update_difference_labels()

            if self.current_page == self.total_pages - 1:
                self.next_button.setEnabled(False)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.next_button.setEnabled(True)

            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)

            # Resaltar la primera diferencia automáticamente en la nueva página
            self.current_difference_index = 0
            self.highlight_current_difference()
            self.update_difference_labels()

            if self.current_page == 0:
                self.prev_button.setEnabled(False)

    def save_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            diff1, diff2 = self.differences[self.current_difference_index]
            diff_text = ' '.join([word[4] for word in diff1]) if diff1 else ''
            if self.radio_no_aplica.isChecked():
                self.labels[(self.current_page, diff_text)] = "No Aplica"
            elif self.radio_aplica.isChecked():
                self.labels[(self.current_page, diff_text)] = "Aplica"
            elif self.radio_otro.isChecked():
                self.labels[(self.current_page, diff_text)] = self.other_input.text()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
