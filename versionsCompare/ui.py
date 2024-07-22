from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QScrollArea, QSplitter
from PyQt5.QtCore import Qt
from logica import PDFComparerLogic

class PDFComparer(QMainWindow, PDFComparerLogic):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Comparer")
        self.setGeometry(100, 100, 1200, 800)

        self.layout = QVBoxLayout()

        self.button1 = QPushButton("Select First PDF", self)
        self.button1.clicked.connect(self.load_first_pdf)
        self.layout.addWidget(self.button1)

        self.button2 = QPushButton("Select Second PDF", self)
        self.button2.clicked.connect(self.load_second_pdf)
        self.layout.addWidget(self.button2)

        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

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

        self.diff_navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous Difference", self)
        self.prev_button.clicked.connect(self.prev_difference)
        self.next_button = QPushButton("Next Difference", self)
        self.next_button.clicked.connect(self.next_difference)
        self.diff_navigation_layout.addWidget(self.prev_button)
        self.diff_navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(self.diff_navigation_layout)

        self.diff_desc = QLabel(self)
        self.diff_desc.setFixedHeight(40)
        self.layout.addWidget(self.diff_desc)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.pdf1_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.pdf2_scroll.verticalScrollBar().valueChanged.connect(self.sync_scroll)
