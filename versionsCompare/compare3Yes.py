import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup, QFrame, QMessageBox, QTextEdit, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
import pandas as pd

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GMF - PDF Comparer")
        self.setGeometry(100, 100, 1650, 800)

        # Layout principal horizontal que contendrá las tres secciones verticales
        self.main_layout = QHBoxLayout()

        # Sección para la selección de PDFs y navegación entre páginas
        self.init_left_section()

        # Sección derecha (la tercera columna)
        self.init_right_section()

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Conexiones de señales para scroll sincronizado
        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

        # Inicialización de variables
        self.reset_all()

    def init_left_section(self):
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

    def init_right_section(self):
        self.right_frame = QFrame(self)
        self.right_frame.setFrameShape(QFrame.StyledPanel)
        self.right_frame.setFrameShadow(QFrame.Sunken)
        self.right_frame.setFixedWidth(300)  # Ajusta la anchura fija de la sección derecha

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
        self.pdf1_diff_edit.setReadOnly(True)
        self.right_layout.addWidget(self.pdf1_diff_edit)

        self.divider2 = QLabel(self)
        self.divider2.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.right_layout.addWidget(self.divider2)

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
        self.other_input.setPlaceholderText("Por favor, especifique para guardar etiqueta")
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

    def sync_scroll(self, value):
        if self.sender() == self.pdf1_scroll.verticalScrollBar():
            self.pdf2_scroll.verticalScrollBar().setValue(value)
        elif self.sender() == self.pdf2_scroll.verticalScrollBar():
            self.pdf1_scroll.verticalScrollBar().setValue(value)

    def load_first_pdf(self):
        if self.pdf1_path and self.pdf2_path:
            self.reset_all()  # Reiniciar si ya hay dos PDFs cargados

        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.button1.setText(fileName.split('/')[-1])
            self.pdf1_path = fileName
            self.reset_comparison()  # Reiniciar la comparación al cargar un nuevo PDF

    def load_second_pdf(self):
        if self.pdf1_path and self.pdf2_path:
            self.reset_all()  # Reiniciar si ya hay dos PDFs cargados

        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.button2.setText(fileName.split('/')[-1])
            self.pdf2_path = fileName
            self.reset_comparison()  # Reiniciar la comparación al cargar un nuevo PDF

    def reset_comparison(self):
        self.current_page = 0
        self.temp_pdf1_paths = []
        self.temp_pdf2_paths = []
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.pdf1_layout.update()
        self.pdf2_layout.update()
        self.labels = {}  # Reiniciar las etiquetas
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

    def highlight_differences(self, doc, words1, words2, page_num):
        differences = []
        current_diff = []
        non_diff_counter = 0

        if page_num < len(words1) and page_num < len(words2):
            page = doc.load_page(page_num)
            page_height = page.rect.height  # Obtener la altura de la página

            # Definir el umbral de exclusión (10% desde el final de la página y 10% desde el inicio)
            lower_exclusion_threshold = page_height * 0.9
            upper_exclusion_threshold = page_height * 0.1

            words1_set = set((word[4] for word in words1[page_num]))
            words2_set = set((word[4] for word in words2[page_num]))

            for word1 in words1[page_num]:
                word_rect = fitz.Rect(word1[:4])

                # Saltar las palabras que están en el 10% superior o 10% inferior de la página
                if word_rect.y1 > lower_exclusion_threshold or word_rect.y1 < upper_exclusion_threshold:
                    continue

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
                word_rect = fitz.Rect(word1[:4])

                # Saltar las palabras que están en el 10% superior o 10% inferior de la página
                if word_rect.y1 > lower_exclusion_threshold or word_rect.y1 < upper_exclusion_threshold:
                    continue
                    
                current_diff.append(word1)
                highlight = fitz.Rect(word1[:4])
                doc[page_num].add_highlight_annot(highlight)  # Resaltado amarillo
            differences.append(current_diff)
            self.pdf1_diff_edit.setText(f"Texto encontrado en PDF1 pero no en PDF2:\n{' '.join([word[4] for word in current_diff])}")
        elif page_num < len(words2):  # Caso donde solo hay texto en el segundo PDF
            for word2 in words2[page_num]:
                word_rect = fitz.Rect(word2[:4])

                # Saltar las palabras que están en el 10% superior o 10% inferior de la página
                if word_rect.y1 > lower_exclusion_threshold or word_rect.y1 < upper_exclusion_threshold:
                    continue
                    
                current_diff.append(word2)
                highlight = fitz.Rect(word2[:4])
                doc[page_num].add_highlight_annot(highlight)  # Resaltado amarillo
            differences.append(current_diff)
            self.pdf2_diff_edit.setText(f"Texto encontrado en PDF2 pero no en PDF1:\n{' '.join([word[4] for word in current_diff])}")

        return doc, differences



    def load_page_pair(self, page_num):
        doc1 = fitz.open(self.pdf1_path)
        doc1, differences1 = self.highlight_differences(doc1, self.pdf1_words, self.pdf2_words, page_num)

        doc2 = fitz.open(self.pdf2_path)
        doc2, differences2 = self.highlight_differences(doc2, self.pdf2_words, self.pdf1_words, page_num)

        self.display_pdfs(self.pdf1_layout, doc1, page_num)
        self.display_pdfs(self.pdf2_layout, doc2, page_num)

        self.differences = list(zip(differences1, differences2))
        self.current_difference_index = 0
        self.update_navigation_buttons()
        self.update_difference_labels()  # Actualiza las etiquetas de diferencias

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
            # Regenerar las imágenes manteniendo los resaltados amarillos
            doc1 = fitz.open(self.pdf1_path)
            doc1, _ = self.highlight_differences(doc1, self.pdf1_words, self.pdf2_words, self.current_page)
            doc2 = fitz.open(self.pdf2_path)
            doc2, _ = self.highlight_differences(doc2, self.pdf2_words, self.pdf1_words, self.current_page)

            # Resaltar la nueva diferencia en rojo
            diff1, diff2 = self.differences[self.current_difference_index]

            page_num = self.current_page

            if diff1:
                start_rect1 = fitz.Rect(diff1[0][:4])
                for word in diff1[1:]:
                    start_rect1 = start_rect1 | fitz.Rect(word[:4])
                rect_annot1 = doc1[page_num].add_rect_annot(start_rect1)
                rect_annot1.set_colors({"stroke": (1, 0, 0)})
                rect_annot1.update()

            if diff2:
                start_rect2 = fitz.Rect(diff2[0][:4])
                for word in diff2[1:]:
                    start_rect2 = start_rect2 | fitz.Rect(word[:4])
                rect_annot2 = doc2[page_num].add_rect_annot(start_rect2)
                rect_annot2.set_colors({"stroke": (1, 0, 0)})
                rect_annot2.update()

            # Mostrar los PDF actualizados
            self.display_pdfs(self.pdf1_layout, doc1, page_num)
            self.display_pdfs(self.pdf2_layout, doc2, page_num)

            if diff1 and diff2:
                if (self.current_page, self.current_difference_index) in self.labels:
                    saved_data = self.labels[(self.current_page, self.current_difference_index)]
                    self.pdf1_diff_edit.setText(saved_data['pdf1_text'])
                    self.pdf2_diff_edit.setText(saved_data['pdf2_text'])

                    if saved_data['label'] == "No Aplica":
                        self.radio_no_aplica.setChecked(True)
                    elif saved_data['label'] == "Aplica":
                        self.radio_aplica.setChecked(True)
                    else:
                        self.radio_otro.setChecked(True)
                        self.other_input.setText(saved_data['label'])
                else:
                    combined_diff1 = ' '.join([word[4] for word in diff1])
                    combined_diff2 = ' '.join([word[4] for word in diff2])
                    self.pdf1_diff_edit.setText(combined_diff1)
                    self.pdf2_diff_edit.setText(combined_diff2)

            # Hacer los QTextEdit editables
            self.pdf1_diff_edit.setReadOnly(False)
            self.pdf2_diff_edit.setReadOnly(False)

    def update_navigation_buttons(self):
        # Verificar si estamos en la primera diferencia o en la última diferencia/página
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)

        if self.current_page == self.total_pages - 1 and self.current_difference_index == len(self.differences) - 1:
            self.next_diff_button.setText("Go to Summary")
        else:
            self.next_diff_button.setText("Next Difference")

        self.next_diff_button.setEnabled(True)  # Siempre habilitado para navegación entre diferencias

        # Habilitar o deshabilitar botones de página según las condiciones
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.check_all_labeled())  # Habilitar solo si todas las diferencias están etiquetadas

        self.update_difference_labels()

    def check_all_labeled(self):
        """Verificar si todas las diferencias en la página actual están etiquetadas."""
        return all(
            (self.current_page, i) in self.labels and self.labels[(self.current_page, i)]['label'] != ''
            for i in range(len(self.differences))
        )

    def update_difference_labels(self):
        total_page_diffs = len(self.differences)
        self.page_diff_label.setText(f"Página {self.current_page + 1} - Diferencia {self.current_difference_index + 1} de {total_page_diffs}")

    def toggle_other_input(self):
        if self.radio_otro.isChecked():
            self.other_input.setVisible(True)
        else:
            self.other_input.setVisible(False)
            self.other_input.clear()

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.save_current_label()  # Guarda la etiqueta actual antes de avanzar
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()
        elif self.current_page < self.total_pages - 1:
            # Guarda la última diferencia antes de pasar a la siguiente página
            self.save_current_label()
            # Si no hay más diferencias en la página actual, pasar automáticamente a la siguiente página
            self.next_page()
        else:
            # Cambiar el botón a "Go to Summary" cuando se esté en la última diferencia de la última página
            self.save_current_label()
            self.show_summary()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def next_page(self):
        # Solo permitir el cambio si todas las diferencias están etiquetadas
        if not self.check_all_labeled():
            QMessageBox.warning(self, 'Advertencia', 'Debes etiquetar todas las diferencias antes de continuar.')
            return

        self.save_current_label()

        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.prev_button.setEnabled(True)

            if self.current_page >= len(self.temp_pdf1_paths):
                self.load_page_pair(self.current_page)
            else:
                self.display_pdfs(self.pdf1_layout, fitz.open(self.pdf1_path), self.current_page)
                self.display_pdfs(self.pdf2_layout, fitz.open(self.pdf2_path), self.current_page)

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
                self.display_pdfs(self.pdf1_layout, fitz.open(self.pdf1_path), self.current_page)
                self.display_pdfs(self.pdf2_layout, fitz.open(self.pdf2_path), self.current_page)

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
            
            current_labels = {
                'pdf1_text': self.pdf1_diff_edit.toPlainText(),
                'pdf2_text': self.pdf2_diff_edit.toPlainText(),
                'label': ''
            }
            
            if self.radio_no_aplica.isChecked():
                current_labels['label'] = "No Aplica"
            elif self.radio_aplica.isChecked():
                current_labels['label'] = "Aplica"
            elif self.radio_otro.isChecked():
                current_labels['label'] = self.other_input.text()
            
            self.labels[(self.current_page, self.current_difference_index)] = current_labels

    def show_summary(self):
        responsible_name, ok = QInputDialog.getText(
            self, 'Nombre del Responsable', 'Por favor, ingrese el nombre del responsable:'
        )
        if not ok or not responsible_name:
            QMessageBox.warning(self, 'Advertencia', 'El nombre del responsable es obligatorio para continuar.')
            return

        # Crear y mostrar la ventana de resumen
        self.summary_window = self.SummaryWindow(self.labels, self.button1.text(), self.button2.text(), responsible_name)
        self.summary_window.setWindowTitle("Summary")
        self.summary_window.setGeometry(100, 100, 1650, 800)
        self.summary_window.show()

    def reset_all(self):
        self.pdf1_path = None
        self.pdf2_path = None
        self.pdf1_text = None
        self.pdf2_text = None
        self.temp_pdf1_paths = []
        self.temp_pdf2_paths = []
        self.differences = []
        self.labels = {}
        self.current_page = 0
        self.current_difference_index = -1
        self.total_pages = 0
        
        # Limpiar la interfaz de usuario
        self.pdf1_layout.update()
        self.pdf2_layout.update()
        self.pdf1_diff_edit.clear()
        self.pdf2_diff_edit.clear()
        self.radio_no_aplica.setChecked(True)
        self.other_input.clear()
        self.other_input.setVisible(False)
        self.page_diff_label.clear()
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_diff_button.setEnabled(False)
        self.next_diff_button.setEnabled(False)

    class SummaryWindow(QWidget):
        def __init__(self, labels, button1_text, button2_text, responsible_name):
            super().__init__()
            self.labels = labels
            self.button1_text = button1_text
            self.button2_text = button2_text
            self.responsible_name = responsible_name
            self.page = 0
            self.rows_per_page = 10

            # Calcular el número total de páginas
            self.total_pages = (len(self.labels) + self.rows_per_page - 1) // self.rows_per_page
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout()
            
            # Mostrar el nombre del responsable y el contador de página
            self.responsible_label = QLabel(f"<b>Responsable: {self.responsible_name} - Página {self.page + 1}/{self.total_pages}</b>")
            layout.addWidget(self.responsible_label)
            
            # Crear la tabla de etiquetas
            self.table_widget = QTableWidget()
            layout.addWidget(self.table_widget)
            
            # Configurar el estilo de la tabla
            self.table_widget.setColumnCount(4)
            self.table_widget.setHorizontalHeaderLabels(["PDF 1", "PDF 2", "Tag", "Page"])
            self.table_widget.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: blue; color: white; }")
            self.table_widget.horizontalHeader().setStretchLastSection(True)
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            # Botones de navegación
            prev_button = QPushButton("Anterior")
            prev_button.clicked.connect(self.show_previous_page)
            layout.addWidget(prev_button)
            
            next_button = QPushButton("Siguiente")
            next_button.clicked.connect(self.show_next_page)
            layout.addWidget(next_button)

            self.setLayout(layout)
            
            # Mostrar la primera página de datos
            self.show_data()

        def show_data(self):
            # Filtrar y ordenar los datos por etiquetas
            data = sorted(
                [{"PDF 1": lbl['pdf1_text'], "PDF 2": lbl['pdf2_text'], "Tag": lbl['label'], "Page": page + 1}
                 for (page, diff_idx), lbl in self.labels.items()],
                key=lambda x: ("Aplica", "Otro", "No Aplica").index(x["Tag"]) if x["Tag"] in ["Aplica", "Otro", "No Aplica"] else 2
            )
            
            start = self.page * self.rows_per_page
            end = start + self.rows_per_page
            page_data = data[start:end]
            
            # Configurar la tabla
            self.table_widget.setRowCount(len(page_data))
            
            # Llenar la tabla con los datos de la página actual
            for row, item in enumerate(page_data):
                self.table_widget.setItem(row, 0, QTableWidgetItem(item["PDF 1"]))
                self.table_widget.setItem(row, 1, QTableWidgetItem(item["PDF 2"]))
                self.table_widget.setItem(row, 2, QTableWidgetItem(item["Tag"]))
                self.table_widget.setItem(row, 3, QTableWidgetItem(str(item["Page"])))

            # Actualizar el contador de página en la etiqueta de responsable
            self.responsible_label.setText(f"<b>Responsable: {self.responsible_name} - Página {self.page + 1}/{self.total_pages}</b>")

        def show_next_page(self):
            if self.page < self.total_pages - 1:
                self.page += 1
                self.show_data()

        def show_previous_page(self):
            if self.page > 0:
                self.page -= 1
                self.show_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
