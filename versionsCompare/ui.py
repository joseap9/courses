import fitz
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import difflib
from pdfminer.high_level import extract_text
from PIL import Image, ImageDraw, ImageFont
import io

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Comparator")
        self.setGeometry(100, 100, 1200, 800)

        self.layout = QVBoxLayout()

        self.label = QLabel("Seleccione dos archivos PDF para comparar")
        self.layout.addWidget(self.label)

        self.button = QPushButton("Seleccionar archivos PDF")
        self.button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.button)

        self.result_label = QLabel("")
        self.layout.addWidget(self.result_label)

        self.pdf_layout = QHBoxLayout()
        self.layout.addLayout(self.pdf_layout)

        self.pdf1_view = QGraphicsView()
        self.pdf1_scene = QGraphicsScene()
        self.pdf1_view.setScene(self.pdf1_scene)
        self.pdf_layout.addWidget(self.pdf1_view)

        self.pdf2_view = QGraphicsView()
        self.pdf2_scene = QGraphicsScene()
        self.pdf2_view.setScene(self.pdf2_scene)
        self.pdf_layout.addWidget(self.pdf2_view)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos PDF", "", "Archivos PDF (*.pdf)", options=options)
        if len(file_names) == 2:
            pdf1_path, pdf2_path = file_names
            self.compare_pdfs(pdf1_path, pdf2_path)
        else:
            self.result_label.setText("Por favor seleccione exactamente dos archivos PDF.")

    def compare_pdfs(self, pdf1_path, pdf2_path):
        pdf1_text = self.extract_text_from_pdf(pdf1_path)
        pdf2_text = self.extract_text_from_pdf(pdf2_path)
        diffs = self.get_diff(pdf1_text, pdf2_text)

        self.highlight_differences(pdf1_path, pdf1_text, diffs, is_pdf1=True)
        self.highlight_differences(pdf2_path, pdf2_text, diffs, is_pdf1=False)
        self.list_differences(diffs)

    def extract_text_from_pdf(self, pdf_path):
        try:
            text = extract_text(pdf_path)
            return text.splitlines()
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return []

    def get_diff(self, text1, text2):
        diff = difflib.ndiff(text1, text2)
        return list(diff)

    def highlight_differences(self, pdf_path, text, diffs, is_pdf1=True):
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            page_text = text[page_num].splitlines()
            page_diffs = [d for d in diffs if d.startswith(' ') or (is_pdf1 and d.startswith('+')) or (not is_pdf1 and d.startswith('-'))]

            for d in page_diffs:
                if d.startswith(' '):
                    continue
                prefix, content = d[0], d[2:]
                if content.strip() == "":
                    continue

                quads = page.search_for(content)
                if quads:
                    for quad in quads:
                        rect = quad.rect
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        draw = ImageDraw.Draw(img)
                        color = "blue" if prefix == '+' else "red"
                        draw.rectangle([rect.x0, rect.y0, rect.x1, rect.y1], outline=color, width=2)
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        image = Image.open(buf)
                        pixmap = QPixmap.fromImage(QImage(image.tobytes(), image.width, image.height, QImage.Format_RGB888))
                        if is_pdf1:
                            self.pdf1_scene.addPixmap(pixmap)
                        else:
                            self.pdf2_scene.addPixmap(pixmap)
                        buf.close()

    def display_pdf(self, doc, is_pdf1):
        scene = QGraphicsScene()
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap(image)
            scene.addItem(QGraphicsPixmapItem(pixmap))

        if is_pdf1:
            self.pdf1_view.setScene(scene)
            self.pdf1_view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        else:
            self.pdf2_view.setScene(scene)
            self.pdf2_view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def list_differences(self, diffs):
        diff_text = "\n".join([d for d in diffs if d.startswith('+') or d.startswith('-')])
        self.result_label.setText(f"Diferencias encontradas:\n{diff_text}")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
