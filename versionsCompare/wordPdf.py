import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea,
    QSplitter, QRadioButton, QLineEdit, QButtonGroup, QFrame, QMessageBox, QTextEdit, QInputDialog, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
from docx import Document

class DocumentComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GMF - Document Comparer")
        self.setGeometry(100, 100, 1650, 800)

        # Layout principal horizontal que contendrá las tres secciones verticales
        self.main_layout = QHBoxLayout()

        # Sección para la selección de documentos y navegación entre páginas
        self.init_left_section()

        # Sección derecha (la tercera columna)
        self.init_right_section()

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Inicialización de variables
        self.reset_all()

    def init_left_section(self):
        self.left_layout = QVBoxLayout()

        self.button1 = QPushButton("Select First Document", self)
        self.button1.clicked.connect(self.load_first_document)
        self.left_layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second Document", self)
        self.button2.clicked.connect(self.load_second_document)
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

        self.doc1_scroll = QScrollArea(self)
        self.doc1_container = QWidget()
        self.doc1_layout = QVBoxLayout()
        self.doc1_container.setLayout(self.doc1_layout)
        self.doc1_scroll.setWidget(self.doc1_container)
        self.doc1_scroll.setWidgetResizable(True)

        self.doc2_scroll = QScrollArea(self)
        self.doc2_container = QWidget()
        self.doc2_layout = QVBoxLayout()
        self.doc2_container.setLayout(self.doc2_layout)
        self.doc2_scroll.setWidget(self.doc2_container)
        self.doc2_scroll.setWidgetResizable(True)

        self.splitter.addWidget(self.doc1_scroll)
        self.splitter.addWidget(self.doc2_scroll)

        # Añadir la sección izquierda al layout principal
        self.main_layout.addLayout(self.left_layout)

    def init_right_section(self):
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

        self.doc1_label = QLabel("Document 1", self)
        self.doc1_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.doc1_label)

        self.doc1_diff_edit = QTextEdit(self)
        self.doc1_diff_edit.setReadOnly(True)
        self.right_layout.addWidget(self.doc1_diff_edit)

        self.divider2 = QLabel(self)
        self.divider2.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        self.right_layout.addWidget(self.divider2)

        self.doc2_label = QLabel("Document 2", self)
        self.doc2_label.setStyleSheet("font-weight: bold;")
        self.right_layout.addWidget(self.doc2_label)

        self.doc2_diff_edit = QTextEdit(self)
        self.doc2_diff_edit.setReadOnly(True)
        self.right_layout.addWidget(self.doc2_diff_edit)

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

    def load_first_document(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select First Document", "", "PDF or Word Files (*.pdf *.docx);;All Files (*)", options=options
        )
        if fileName:
            self.doc1_path = fileName
            self.button1.setText(fileName.split('/')[-1])
            self.reset_comparison()

    def load_second_document(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select Second Document", "", "PDF or Word Files (*.pdf *.docx);;All Files (*)", options=options
        )
        if fileName:
            self.doc2_path = fileName
            self.button2.setText(fileName.split('/')[-1])
            self.reset_comparison()

    def reset_comparison(self):
        # Reset logic and compare documents
        if self.doc1_path and self.doc2_path:
            self.compare_documents()

    def extract_text_from_docx(self, file_path):
        document = Document(file_path)
        return "\n".join([para.text for para in document.paragraphs])

    def extract_text_from_pdf(self, file_path):
        doc = fitz.open(file_path)
        return "\n".join([page.get_text() for page in doc])

    def compare_documents(self):
        if self.doc1_path.endswith(".pdf"):
            text1 = self.extract_text_from_pdf(self.doc1_path)
        else:
            text1 = self.extract_text_from_docx(self.doc1_path)

        if self.doc2_path.endswith(".pdf"):
            text2 = self.extract_text_from_pdf(self.doc2_path)
        else:
            text2 = self.extract_text_from_docx(self.doc2_path)

        self.highlight_differences(text1, text2)

    def highlight_differences(self, text1, text2):
        # Placeholder for highlighting differences logic
        self.doc1_diff_edit.setText(text1)
        self.doc2_diff_edit.setText(text2)

    def toggle_other_input(self):
        self.other_input.setVisible(self.radio_otro.isChecked())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comparer = DocumentComparer()
    comparer.show()
    sys.exit(app.exec_())
