import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QTextEdit, QButtonGroup, QRadioButton, QLineEdit, QMessageBox, QFrame
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
        self.pdf1_diff_edit.editingFinished.connect(self.save_current_label)
        self.right_layout.addWidget(self.pdf1_diff_edit)

        self.divider2 = QLabel(self)
        self.divider2.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.right_layout.addWidget(self.divider2)

        self.pdf2_label = QLabel("PDF 2", self)
        self.pdf2_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.pdf2_label)

        self.pdf2_diff_edit = QTextEdit(self)
        self.pdf2_diff_edit.editingFinished.connect(self.save_current_label)
        self.right_layout.addWidget(self.pdf2_diff_edit)

        self.prev_diff_button = QPushButton("Previous Difference", self)
        self.prev_diff_button.clicked.connect(self.prev_difference)
        self.prev_diff_button.setEnabled(False)
        self.right_layout.addWidget(self.prev_diff_button)

        self.next_diff_button = QPushButton("Next Difference", self)
        self.next_diff_button.clicked.connect(self.next_difference)
        self.next_diff_button.setEnabled(False)
        self.right_layout.addWidget(self.next_diff_button)

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

        self.summary_button = None
        self.total_aplica = 0
        self.total_no_aplica = 0
        self.total_otro = 0

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

    def save_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            diff1, diff2 = self.differences[self.current_difference_index]
            diff_text = ' '.join([word[4] for word in diff1]) if diff1 else ''
            if self.radio_no_aplica.isChecked():
                self.labels[(self.current_page, diff_text)] = "No Aplica"
                self.total_no_aplica += 1
            elif self.radio_aplica.isChecked():
                self.labels[(self.current_page, diff_text)] = "Aplica"
                self.total_aplica += 1
            elif self.radio_otro.isChecked():
                self.labels[(self.current_page, diff_text)] = self.other_input.text()
                self.total_otro += 1

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

        # Mostrar botón de resumen en la última página
        if self.current_page == self.total_pages - 1:
            self.show_summary_button()

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

    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setEnabled(self.current_difference_index < len(self.differences) - 1)
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        self.update_difference_labels()

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
            self.save_current_label()  # Guardar antes de cambiar
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.save_current_label()  # Guardar antes de cambiar
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

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
                        self.save_current_label()

            if reply == QMessageBox.Yes and self.current_page < self.total_pages - 1:
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

    def show_summary_button(self):
        if not self.summary_button:
            self.summary_button = QPushButton("Summary", self)
            self.summary_button.clicked.connect(self.show_summary)
            self.right_layout.addWidget(self.summary_button)

    def show_summary(self):
        # Verificar si todas las diferencias han sido revisadas antes de mostrar el resumen
        unrevised_diffs = len(self.differences) - self.current_difference_index - 1
        if unrevised_diffs > 0:
            reply = QMessageBox.question(self, 'Diferencias sin revisar',
                                        f'Hay {unrevised_diffs} diferencias que no se han visto. ¿Deseas marcarlas como "No Aplica"?',
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                while self.current_difference_index < len(self.differences) - 1:
                    self.current_difference_index += 1
                    self.save_current_label()

        # Ocultar todos los widgets de la sección de diferencias y deshabilitar botones
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget and widget != self.summary_button:
                widget.setVisible(False)

        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_diff_button.setEnabled(False)
        self.next_diff_button.setEnabled(False)

        # Calcular el total de diferencias (suma de todas las páginas)
        total_differences = self.total_diffs

        # Mostrar resumen en texto simple
        summary_label = QLabel("Resumen de Diferencias")
        self.right_layout.addWidget(summary_label)

        total_diff_label = QLabel(f"Total de diferencias en el documento: {total_differences}")
        self.right_layout.addWidget(total_diff_label)

        filtered_diff_label = QLabel(f"Total de diferencias (Excluyendo 'No Aplica'): {self.total_aplica + self.total_otro}")
        self.right_layout.addWidget(filtered_diff_label)

        aplica_label = QLabel(f"Diferencias 'Aplica': {self.total_aplica}")
        self.right_layout.addWidget(aplica_label)

        no_aplica_label = QLabel(f"Diferencias 'No Aplica': {self.total_no_aplica}")
        self.right_layout.addWidget(no_aplica_label)

        otro_label = QLabel(f"Diferencias 'Otro': {self.total_otro}")
        self.right_layout.addWidget(otro_label)

        # Botón para volver atrás a la vista de comparación
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.back_to_comparison)
        self.right_layout.addWidget(back_button)

    def back_to_comparison(self):
        # Eliminar todos los widgets del resumen
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Mostrar nuevamente los widgets originales de la sección de diferencias
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.prev_diff_button.setEnabled(True)
        self.next_diff_button.setEnabled(True)

        for i in range(self.right_layout.count()):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(True)

        self.update_navigation_buttons()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
