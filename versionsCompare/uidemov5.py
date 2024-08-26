import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QTextEdit, QButtonGroup, QRadioButton, QMessageBox, QFrame, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GMF - PDF Comparer")
        self.setGeometry(100, 100, 1650, 800)

        self.main_layout = QHBoxLayout()
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

        self.main_layout.addLayout(self.left_layout)

        self.right_frame = QFrame(self)
        self.right_frame.setFrameShape(QFrame.StyledPanel)
        self.right_frame.setFrameShadow(QFrame.Sunken)
        self.right_frame.setFixedWidth(300)

        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        self.page_diff_label = QLabel(self)
        self.page_diff_label.setWordWrap(True)
        self.page_diff_label.setAlignment(Qt.AlignCenter)
        self.page_diff_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.right_layout.addWidget(self.page_diff_label)

        self.pdf1_label = QLabel("PDF 1", self)
        self.pdf1_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.pdf1_label)

        self.pdf1_diff_edit = QTextEdit(self)
        self.right_layout.addWidget(self.pdf1_diff_edit)

        self.divider2 = QLabel(self)
        self.divider2.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.right_layout.addWidget(self.divider2)

        self.pdf2_label = QLabel("PDF 2", self)
        self.pdf2_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.pdf2_label)

        self.pdf2_diff_edit = QTextEdit(self)
        self.right_layout.addWidget(self.pdf2_diff_edit)

        self.radio_group = QButtonGroup(self)
        self.radio_aplica = QRadioButton("Aplica")
        self.radio_no_aplica = QRadioButton("No Aplica")
        self.radio_otro = QRadioButton("Otro")
        self.radio_group.addButton(self.radio_aplica)
        self.radio_group.addButton(self.radio_no_aplica)
        self.radio_group.addButton(self.radio_otro)

        self.right_layout.addWidget(self.radio_aplica)
        self.right_layout.addWidget(self.radio_no_aplica)
        self.right_layout.addWidget(self.radio_otro)

        self.otro_text = QLineEdit(self)
        self.otro_text.setPlaceholderText("Especificar otro...")
        self.otro_text.setVisible(False)
        self.right_layout.addWidget(self.otro_text)

        self.radio_otro.toggled.connect(self.show_otro_text)
        self.radio_no_aplica.setChecked(True)  # Seleccionar "No Aplica" por defecto

        self.prev_diff_button = QPushButton("Previous Difference", self)
        self.prev_diff_button.clicked.connect(self.prev_difference)
        self.prev_diff_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Difference", self)
        self.next_diff_button.clicked.connect(self.next_difference)
        self.next_diff_button.setEnabled(False)
        self.right_layout.addWidget(self.next_diff_button)

        self.summary_button = QPushButton("Summary", self)
        self.summary_button.clicked.connect(self.show_summary)
        self.right_layout.addWidget(self.summary_button)
        self.summary_button.setVisible(False)  # Ocultar el botón de resumen inicialmente

        self.main_layout.addWidget(self.right_frame)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

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
        self.total_diffs = 0

        self.total_aplica = 0
        self.total_no_aplica = 0
        self.total_otro = 0

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
        self.total_diffs = 0
        self.labels.clear()
        self.total_aplica = 0
        self.total_no_aplica = 0
        self.total_otro = 0
        self.summary_button.setVisible(False)  # Ocultar el botón de resumen al reiniciar
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
            self.update_difference_labels()
            self.highlight_current_difference()

    def highlight_differences(self, doc, words1, words2, page_num):
        differences = []
        current_diff = []

        if page_num < len(words1) and page_num < len(words2):
            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word1 in words1[page_num]:
                if word1[4] not in words2_set:
                    if current_diff and (int(word1[0]) > int(current_diff[-1][2]) + 10):
                        differences.append(current_diff)
                        current_diff = []
                    current_diff.append(word1)
                    highlight = fitz.Rect(word1[:4])
                    doc[page_num].add_highlight_annot(highlight)
                else:
                    if current_diff:
                        differences.append(current_diff)
                        current_diff = []
            if current_diff:
                differences.append(current_diff)
        else:
            if page_num < len(words1):
                for word1 in words1[page_num]:
                    current_diff.append(word1)
                    highlight = fitz.Rect(word1[:4])
                    doc[page_num].add_highlight_annot(highlight)
                self.pdf1_diff_edit.setText(f"Texto encontrado en PDF1 pero no en PDF2:\n{' '.join([word[4] for word in current_diff])}")
            if page_num < len(words2):
                for word2 in words2[page_num]:
                    current_diff.append(word2)
                    highlight = fitz.Rect(word2[:4])
                    doc[page_num].add_highlight_annot(highlight)
                self.pdf2_diff_edit.setText(f"Texto encontrado en PDF2 pero no en PDF1:\n{' '.join([word[4] for word in current_diff])}")

        self.total_diffs += len(differences)
        return doc, differences

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
        self.update_difference_labels()

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
            diff1, diff2 = self.differences[self.current_difference_index]

            page_num = self.current_page

            if diff1:
                doc1 = self.temp_pdf1_paths[self.current_page]
                start_rect1 = fitz.Rect(diff1[0][:4])
                for word in diff1[1:]:
                    start_rect1 = start_rect1 | fitz.Rect(word[:4])
                # Solo marca el conjunto si es un conjunto
                if len(diff1) > 1:
                    rect_annot1 = doc1[page_num].add_rect_annot(start_rect1)
                    rect_annot1.set_colors({"stroke": (1, 0, 0)})
                    rect_annot1.update()
                self.display_pdfs(self.pdf1_layout, doc1, page_num)

            if diff2:
                doc2 = self.temp_pdf2_paths[self.current_page]
                start_rect2 = fitz.Rect(diff2[0][:4])
                for word in diff2[1:]:
                    start_rect2 = start_rect2 | fitz.Rect(word[:4])
                # Solo marca el conjunto si es un conjunto
                if len(diff2) > 1:
                    rect_annot2 = doc2[page_num].add_rect_annot(start_rect2)
                    rect_annot2.set_colors({"stroke": (1, 0, 0)})
                    rect_annot2.update()
                self.display_pdfs(self.pdf2_layout, doc2, page_num)

            if diff1 and diff2:
                combined_diff1 = ' '.join([word[4] for word in diff1])
                combined_diff2 = ' '.join([word[4] for word in diff2])
                self.pdf1_diff_edit.setText(combined_diff1)
                self.pdf2_diff_edit.setText(combined_diff2)

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.save_current_label()
            # Saltar a la siguiente diferencia no solapada
            while self.current_difference_index < len(self.differences) - 1:
                self.current_difference_index += 1
                diff1, diff2 = self.differences[self.current_difference_index]
                if len(diff1) > 1 or len(diff2) > 1:
                    break
            self.update_navigation_buttons()
            self.highlight_current_difference()
            self.load_current_label()  # Cargar la etiqueta guardada al avanzar



    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        self.update_difference_labels()

    def update_difference_labels(self):
        total_page_diffs = len(self.differences)
        self.page_diff_label.setText(f"Página {self.current_page + 1} - Diferencia {self.current_difference_index + 1} de {total_page_diffs}")

        # Mostrar el botón de Summary si se está en la última página
        if self.current_page == self.total_pages - 1:
            self.summary_button.setVisible(True)

    def check_all_labeled(self):
        """Verifica si todas las diferencias han sido etiquetadas y muestra el botón de resumen."""
        if len(self.labels) == self.total_diffs:
            self.summary_button.setVisible(True)

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.save_current_label()
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()
            self.load_current_label()  # Cargar la etiqueta guardada al avanzar

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.save_current_label()
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()
            self.load_current_label()  # Cargar la etiqueta guardada al retroceder

    def next_page(self):
        try:
            unrevised_diffs = len(self.differences) - self.current_difference_index - 1
            if unrevised_diffs > 0:
                reply = QMessageBox.question(self, 'Diferencias sin revisar',
                                            f'Hay {unrevised_diffs} diferencias que no se han visto. ¿Deseas marcarlas como "No Aplica"?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    while self.current_difference_index < len(self.differences) - 1:
                        self.current_difference_index += 1
                        self.radio_no_aplica.setChecked(True)
                        self.save_current_label()

            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.prev_button.setEnabled(True)

                if self.current_page >= len(self.temp_pdf1_paths):
                    self.load_page_pair(self.current_page)
                else:
                    self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                    self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)

                self.current_difference_index = 0
                self.highlight_current_difference()
                self.update_difference_labels()

                if self.current_page == self.total_pages - 1:
                    self.next_button.setEnabled(False)
                    self.summary_button.setVisible(True)  # Mostrar el botón de Summary en la última página
        except UnboundLocalError:
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.prev_button.setEnabled(True)

                if self.current_page >= len(self.temp_pdf1_paths):
                    self.load_page_pair(self.current_page)
                else:
                    self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                    self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)

                self.current_difference_index = 0
                self.highlight_current_difference()
                self.update_difference_labels()

                if self.current_page == self.total_pages - 1:
                    self.next_button.setEnabled(False)
                    self.summary_button.setVisible(True)  # Mostrar el botón de Summary en la última página

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.next_button.setEnabled(True)

            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, self.temp_pdf1_paths[self.current_page], self.current_page)
                self.display_pdfs(self.pdf2_layout, self.temp_pdf2_paths[self.current_page], self.current_page)

            self.current_difference_index = 0
            self.highlight_current_difference()
            self.update_difference_labels()

            if self.current_page == 0:
                self.prev_button.setEnabled(False)

    def save_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            diff1, diff2 = self.differences[self.current_difference_index]
            diff_text = ' '.join([word[4] for word in diff1]) if diff1 else ''
            
            # Remover el conteo previo si ya se había etiquetado esta diferencia
            if (self.current_page, diff_text) in self.labels:
                prev_label = self.labels[(self.current_page, diff_text)]
                if prev_label == "Aplica":
                    self.total_aplica -= 1
                elif prev_label == "No Aplica":
                    self.total_no_aplica -= 1
                elif "Otro" in prev_label:
                    self.total_otro -= 1
            
            # Guardar la nueva etiqueta y actualizar el conteo
            if self.radio_aplica.isChecked():
                self.labels[(self.current_page, diff_text)] = "Aplica"
                self.total_aplica += 1
            elif self.radio_no_aplica.isChecked():
                self.labels[(self.current_page, diff_text)] = "No Aplica"
                self.total_no_aplica += 1
            elif self.radio_otro.isChecked():
                self.labels[(self.current_page, diff_text)] = f"Otro: {self.otro_text.text()}"
                self.total_otro += 1

    def load_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            diff1, diff2 = self.differences[self.current_difference_index]
            diff_text = ' '.join([word[4] for word in diff1]) if diff1 else ''
            
            # Cargar la etiqueta previamente guardada, si existe
            if (self.current_page, diff_text) in self.labels:
                saved_label = self.labels[(self.current_page, diff_text)]
                if saved_label == "Aplica":
                    self.radio_aplica.setChecked(True)
                elif saved_label == "No Aplica":
                    self.radio_no_aplica.setChecked(True)
                elif "Otro" in saved_label:
                    self.radio_otro.setChecked(True)
                    self.otro_text.setText(saved_label.split(": ")[1])

    def show_otro_text(self):
        self.otro_text.setVisible(self.radio_otro.isChecked())

    def show_summary_button(self):
        if not self.summary_button:
            self.summary_button = QPushButton("Summary", self)
            self.summary_button.clicked.connect(self.show_summary)
            self.right_layout.addWidget(self.summary_button)
            self.summary_button.setVisible(False)

    def show_summary(self):
        # Calcular el total de diferencias como la suma de "Aplica", "No Aplica" y "Otro"
        total_aplica = sum(1 for label in self.labels.values() if label == "Aplica")
        total_no_aplica = sum(1 for label in self.labels.values() if label == "No Aplica")
        total_otro = sum(1 for label in self.labels.values() if "Otro" in label)

        total_differences = total_aplica + total_no_aplica + total_otro
        total_diffs_excl_no_aplica = total_aplica + total_otro

        # Mostrar el resumen en una ventana emergente
        summary_message = QMessageBox()
        summary_message.setWindowTitle("Resumen de Diferencias")
        summary_message.setText(
            f"Total de diferencias en el documento: {total_differences}\n"
            f"Diferencias 'Aplica': {total_aplica}\n"
            f"Diferencias 'No Aplica': {total_no_aplica}\n"
            f"Diferencias 'Otro': {total_otro}\n"
            f"Total de diferencias excluyendo 'No Aplica': {total_diffs_excl_no_aplica}"
        )
        summary_message.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())                             
