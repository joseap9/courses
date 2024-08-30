import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter, QRadioButton, QLineEdit, QButtonGroup, QFrame, QMessageBox, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF

class PDFComparer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_vars()

    def init_ui(self):
        self.setWindowTitle("GMF - PDF Comparer")
        self.setGeometry(100, 100, 1650, 800)

        main_layout = QHBoxLayout()

        # Sección para la selección de PDFs y navegación
        left_layout = QVBoxLayout()
        self.button1 = self.create_button("Select First PDF", self.load_first_pdf)
        self.button2 = self.create_button("Select Second PDF", self.load_second_pdf)
        left_layout.addWidget(self.button1)
        left_layout.addWidget(self.button2)

        navigation_layout = QHBoxLayout()
        self.prev_button = self.create_button("Previous Page", self.prev_page, enabled=False)
        self.next_button = self.create_button("Next Page", self.next_page, enabled=False)
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)
        left_layout.addLayout(navigation_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        self.pdf1_scroll = self.create_scroll_area()
        self.pdf2_scroll = self.create_scroll_area()
        self.splitter.addWidget(self.pdf1_scroll)
        self.splitter.addWidget(self.pdf2_scroll)
        left_layout.addWidget(self.splitter)

        main_layout.addLayout(left_layout)

        # Sección derecha (la tercera columna)
        right_frame = QFrame(self)
        right_frame.setFixedWidth(300)
        right_layout = QVBoxLayout(right_frame)
        self.page_diff_label = QLabel(self)
        self.pdf1_diff_edit = QTextEdit(self)
        self.pdf2_diff_edit = QTextEdit(self)
        self.other_input = QLineEdit(self)

        self.setup_right_layout(right_layout)
        main_layout.addWidget(right_frame)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Scroll sincronizado
        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)

    def init_vars(self):
        self.pdf1_path = self.pdf2_path = None
        self.current_page = self.total_pages = 0
        self.temp_pdf1_paths = self.temp_pdf2_paths = []
        self.differences = []
        self.current_difference_index = -1
        self.labels = {}

    def create_button(self, text, callback, enabled=True):
        button = QPushButton(text, self)
        button.clicked.connect(callback)
        button.setEnabled(enabled)
        return button

    def create_scroll_area(self):
        scroll = QScrollArea(self)
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        return scroll

    def setup_right_layout(self, layout):
        self.page_diff_label.setAlignment(Qt.AlignCenter)
        self.page_diff_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.page_diff_label)

        self.setup_text_edit("PDF 1", layout, self.pdf1_diff_edit)
        layout.addWidget(self.create_divider())
        self.setup_text_edit("PDF 2", layout, self.pdf2_diff_edit)

        radio_group = QButtonGroup(self)
        for text, callback in [("No Aplica", None), ("Aplica", None), ("Otro", self.toggle_other_input)]:
            radio_button = QRadioButton(text, self)
            radio_group.addButton(radio_button)
            layout.addWidget(radio_button)
        self.other_input.setPlaceholderText("Por favor, especifique para guardar etiqueta")
        self.other_input.setVisible(False)
        layout.addWidget(self.other_input)

        layout.addWidget(self.create_button("Previous Difference", self.prev_difference, enabled=False))
        layout.addWidget(self.create_button("Next Difference", self.next_difference, enabled=False))

    def setup_text_edit(self, label_text, layout, text_edit):
        label = QLabel(label_text, self)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

    def create_divider(self):
        divider = QLabel(self)
        divider.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        return divider

    def sync_scroll(self, value):
        if self.sender() == self.pdf1_scroll.verticalScrollBar():
            self.pdf2_scroll.verticalScrollBar().setValue(value)
        elif self.sender() == self.pdf2_scroll.verticalScrollBar():
            self.pdf1_scroll.verticalScrollBar().setValue(value)

    def load_first_pdf(self):
        self.load_pdf(is_first=True)

    def load_second_pdf(self):
        self.load_pdf(is_first=False)

    def load_pdf(self, is_first):
        if self.pdf1_path and self.pdf2_path:
            self.reset_all()
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_name:
            if is_first:
                self.button1.setText(file_name.split('/')[-1])
                self.pdf1_path = file_name
            else:
                self.button2.setText(file_name.split('/')[-1])
                self.pdf2_path = file_name
            self.reset_comparison()

    def reset_comparison(self):
        self.current_page = 0
        self.temp_pdf1_paths = []
        self.temp_pdf2_paths = []
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.labels = {}
        if self.pdf1_path and self.pdf2_path:
            self.compare_pdfs()
            self.highlight_current_difference()

    def extract_text_and_positions(self, file_path):
        document = fitz.open(file_path)
        text, words = [], []
        for page in document:
            text.append(page.get_text())
            words.append(page.get_text("words"))
        return text, words

    def compare_pdfs(self):
        self.pdf1_text, self.pdf1_words = self.extract_text_and_positions(self.pdf1_path)
        self.pdf2_text, self.pdf2_words = self.extract_text_and_positions(self.pdf2_path)
        self.total_pages = min(len(self.pdf1_words), len(self.pdf2_words))
        self.load_page_pair(self.current_page)
        self.next_button.setEnabled(True)
        self.update_difference_labels()
        self.highlight_current_difference()

    def highlight_differences(self, doc, words1, words2, page_num):
        differences, current_diff, non_diff_counter = [], [], 0

        if page_num < len(words1) and page_num < len(words2):
            words1_set, words2_set = set(word[4] for word in words1[page_num]), set(word[4] for word in words2[page_num])
            for word1 in words1[page_num]:
                if word1[4] not in words2_set:
                    if non_diff_counter > 8 and current_diff:
                        differences.append(current_diff)
                        current_diff = []
                    current_diff.append(word1)
                    doc[page_num].add_highlight_annot(fitz.Rect(word1[:4]))  # Resaltado amarillo
                    non_diff_counter = 0
                else:
                    non_diff_counter += 1
                    if non_diff_counter > 8 and current_diff:
                        differences.append(current_diff)
                        current_diff = []

            if current_diff:
                differences.append(current_diff)

        return doc, differences

    def load_page_pair(self, page_num):
        doc1, differences1 = self.highlight_differences(fitz.open(self.pdf1_path), self.pdf1_words, self.pdf2_words, page_num)
        doc2, differences2 = self.highlight_differences(fitz.open(self.pdf2_path), self.pdf2_words, self.pdf1_words, page_num)

        self.display_pdfs(self.pdf1_layout, doc1, page_num)
        self.display_pdfs(self.pdf2_layout, doc2, page_num)

        self.differences = list(zip(differences1, differences2))
        self.current_difference_index = 0
        self.update_navigation_buttons()
        self.update_difference_labels()

    def display_pdfs(self, layout, doc, page_num):
        layout.takeAt(0).widget().deleteLater() if layout.count() > 0 else None
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        label = QLabel(self)
        label.setPixmap(QPixmap.fromImage(img))
        layout.addWidget(label)

    def highlight_current_difference(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            doc1, _ = self.highlight_differences(fitz.open(self.pdf1_path), self.pdf1_words, self.pdf2_words, self.current_page)
            doc2, _ = self.highlight_differences(fitz.open(self.pdf2_path), self.pdf2_words, self.pdf1_words, self.current_page)

            diff1, diff2 = self.differences[self.current_difference_index]

            if diff1:
                rect_annot1 = doc1[self.current_page].add_rect_annot(self.merge_rects(diff1))
                rect_annot1.set_colors({"stroke": (1, 0, 0)})
                rect_annot1.update()

            if diff2:
                rect_annot2 = doc2[self.current_page].add_rect_annot(self.merge_rects(diff2))
                rect_annot2.set_colors({"stroke": (1, 0, 0)})
                rect_annot2.update()

            self.display_pdfs(self.pdf1_layout, doc1, self.current_page)
            self.display_pdfs(self.pdf2_layout, doc2, self.current_page)

            self.update_text_edits(diff1, diff2)

    def merge_rects(self, words):
        start_rect = fitz.Rect(words[0][:4])
        for word in words[1:]:
            start_rect |= fitz.Rect(word[:4])
        return start_rect

    def update_text_edits(self, diff1, diff2):
        self.pdf1_diff_edit.setText(' '.join([word[4] for word in diff1]) if diff1 else '')
        self.pdf2_diff_edit.setText(' '.join([word[4] for word in diff2]) if diff2 else '')
        self.pdf1_diff_edit.setReadOnly(False)
        self.pdf2_diff_edit.setReadOnly(False)

    def update_navigation_buttons(self):
        self.prev_diff_button.setEnabled(self.current_difference_index > 0)
        self.next_diff_button.setText("Go to Summary" if self.current_page == self.total_pages - 1 and self.current_difference_index == len(self.differences) - 1 else "Next Difference")
        self.next_diff_button.setEnabled(True)
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        self.update_difference_labels()

    def update_difference_labels(self):
        total_page_diffs = len(self.differences)
        self.page_diff_label.setText(f"Página {self.current_page + 1} - Diferencia {self.current_difference_index + 1} de {total_page_diffs}")

    def toggle_other_input(self):
        self.other_input.setVisible(self.radio_otro.isChecked())
        if not self.radio_otro.isChecked():
            self.other_input.clear()

    def next_difference(self):
        if self.current_difference_index < len(self.differences) - 1:
            self.save_current_label()
            self.current_difference_index += 1
            self.update_navigation_buttons()
            self.highlight_current_difference()
        elif self.current_page < self.total_pages - 1:
            self.save_current_label()
            self.next_page()
        else:
            self.save_current_label()
            self.show_summary()

    def prev_difference(self):
        if self.current_difference_index > 0:
            self.current_difference_index -= 1
            self.update_navigation_buttons()
            self.highlight_current_difference()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.save_current_label()
            if self.check_all_labeled():
                self.current_page += 1
                self.load_page_pair(self.current_page)
                self.current_difference_index = 0
                self.highlight_current_difference()
                self.update_difference_labels()
                self.prev_button.setEnabled(self.current_page > 0)
                self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page_pair(self.current_page)
            self.highlight_current_difference()
            self.update_difference_labels()
            self.prev_button.setEnabled(self.current_page > 0)

    def check_all_labeled(self):
        all_labeled = all(
            (self.current_page, i) in self.labels and self.labels[(self.current_page, i)]['label'] != ''
            for i in range(len(self.differences))
        )
        if not all_labeled:
            reply = QMessageBox.question(self, 'Diferencias sin revisar', 'Existen diferencias que no han sido etiquetadas. ¿Deseas marcarlas como "No Aplica"?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for i in range(len(self.differences)):
                    if (self.current_page, i) not in self.labels or self.labels[(self.current_page, i)]['label'] == '':
                        self.current_difference_index = i
                        self.radio_no_aplica.setChecked(True)
                        self.save_current_label()
            else:
                return False
        return all_labeled

    def save_current_label(self):
        if self.current_difference_index >= 0 and self.current_difference_index < len(self.differences):
            current_labels = {
                'pdf1_text': self.pdf1_diff_edit.toPlainText(),
                'pdf2_text': self.pdf2_diff_edit.toPlainText(),
                'label': self.get_selected_label()
            }
            self.labels[(self.current_page, self.current_difference_index)] = current_labels

    def get_selected_label(self):
        if self.radio_no_aplica.isChecked():
            return "No Aplica"
        elif self.radio_aplica.isChecked():
            return "Aplica"
        elif self.radio_otro.isChecked():
            return self.other_input.text()
        return ''

    def show_summary(self):
        count_applies = sum(1 for label in self.labels.values() if label['label'] == "Aplica")
        count_no_applies = sum(1 for label in self.labels.values() if label['label'] == "No Aplica")
        count_others = sum(1 for label in self.labels.values() if label['label'] and label['label'] != "Aplica" and label['label'] != "No Aplica")
        total_diffs = count_applies + count_no_applies + count_others
        summary_text = (
            f"<b><span style='font-size:14pt;'>Total de diferencias que aplican: </span><span style='font-size:14pt;'>{count_applies}</span></b><br><br>"
            f"<b><span style='font-size:12pt;'>Detalle</span></b></<br><br>"
            f"<b><span style='font-size:10pt;'>  - Aplica: </span><span style='font-size:10pt;'>{count_applies}</span></b><br>"
            f"<b><span style='font-size:10pt;'>  - No Aplica: </span><span style='font-size:10pt;'>{count_no_applies}</span></b><br>"
            f"<b><span style='font-size:10pt;'>  - Otro: </span><span style='font-size:10pt;'>{count_others}</span></b><br><br>"
            f"<b><span style='font-size:12pt;'>Total: </span><span style='font-size:12pt;'>{total_diffs}</span></b>"
        )
        QMessageBox.information(self, "Resumen de Diferencias", summary_text)

    def reset_all(self):
        self.init_vars()
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

if __name__=="__main__":
    app = QApplication(sys.argv)
    comparer = PDFComparer()
    comparer.show()
    sys.exit(app.exec_())
