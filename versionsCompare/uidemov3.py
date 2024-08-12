import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
import fitz  # PyMuPDF

class PDFComparator(QWidget):
    def __init__(self):
        super().__init__()
        
        self.pdf1 = None
        self.pdf2 = None
        self.differences = []
        self.current_diff_index = 0
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Labels to show PDFs
        self.label_pdf1 = QLabel("PDF1 Preview")
        self.label_pdf2 = QLabel("PDF2 Preview")
        layout.addWidget(self.label_pdf1)
        layout.addWidget(self.label_pdf2)
        
        # Label to show difference description
        self.diff_label = QLabel("Diferencia actual: ")
        layout.addWidget(self.diff_label)
        
        # Buttons to navigate differences
        self.prev_button = QPushButton("Anterior Diferencia")
        self.prev_button.clicked.connect(self.prev_diff)
        layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Siguiente Diferencia")
        self.next_button.clicked.connect(self.next_diff)
        layout.addWidget(self.next_button)
        
        # Load PDF buttons
        self.load_pdf1_button = QPushButton("Select First PDF")
        self.load_pdf1_button.clicked.connect(self.load_pdf1)
        layout.addWidget(self.load_pdf1_button)
        
        self.load_pdf2_button = QPushButton("Select Second PDF")
        self.load_pdf2_button.clicked.connect(self.load_pdf2)
        layout.addWidget(self.load_pdf2_button)
        
        self.setLayout(layout)
        self.setWindowTitle('PDF Comparator')
        self.show()
        
    def load_pdf1(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.pdf1 = fitz.open(file_name)
            self.compare_pdfs()

    def load_pdf2(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.pdf2 = fitz.open(file_name)
            self.compare_pdfs()
        
    def compare_pdfs(self):
        if self.pdf1 and self.pdf2:
            self.differences = []
            # Assumes both PDFs have the same number of pages for simplicity
            for page_num in range(min(len(self.pdf1), len(self.pdf2))):
                page1 = self.pdf1.load_page(page_num)
                page2 = self.pdf2.load_page(page_num)
                
                lines1 = self.get_lines_from_page(page1)
                lines2 = self.get_lines_from_page(page2)
                
                min_len = min(len(lines1), len(lines2))
                for i in range(min_len):
                    line1 = lines1[i]
                    line2 = lines2[i]
                    
                    # Compare words in the line
                    for word1, word2 in zip(line1, line2):
                        if word1[4] != word2[4]:
                            self.differences.append((page_num, word1, word2))
                    # Check for extra words in either line
                    if len(line1) > len(line2):
                        for word in line1[len(line2):]:
                            self.differences.append((page_num, word, ('SD',) * 5))
                    elif len(line2) > len(line1):
                        for word in line2[len(line1):]:
                            self.differences.append((page_num, ('SD',) * 5, word))
            
            if self.differences:
                self.current_diff_index = 0
                self.show_difference()

    def get_lines_from_page(self, page):
        text = page.get_text("words")
        lines = []
        current_line = []
        y0 = text[0][1] if text else 0  # Initialize y0 to the y-coordinate of the first word
        for word in text:
            if abs(word[1] - y0) > 5:  # A new line is detected if the y-coordinate changes significantly
                lines.append(current_line)
                current_line = []
                y0 = word[1]
            current_line.append(word)
        if current_line:
            lines.append(current_line)
        return lines

    def show_difference(self):
        if not self.differences:
            return
        
        page_num, word1, word2 = self.differences[self.current_diff_index]
        
        image1 = self.render_page(self.pdf1, page_num)
        image2 = self.render_page(self.pdf2, page_num)
        
        pixmap1 = QPixmap.fromImage(image1)
        pixmap2 = QPixmap.fromImage(image2)
        
        # Highlight differences
        self.highlight_difference(pixmap1, word1)
        self.highlight_difference(pixmap2, word2)
        
        self.label_pdf1.setPixmap(pixmap1)
        self.label_pdf2.setPixmap(pixmap2)
        
        # Update label with description
        desc = f"PDF1: {word1[4]} - PDF2: {word2[4]}"
        self.diff_label.setText(f"Diferencia actual: {desc}")
    
    def highlight_difference(self, pixmap, word):
        if word[0] != 'SD':
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 0, 0))
            
            # Convertir coordenadas flotantes a enteros
            rect = fitz.Rect(word[:4])
            x0, y0, x1, y1 = int(rect.x0), int(rect.y0), int(rect.x1), int(rect.y1)
            painter.drawRect(x0, y0, x1 - x0, y1 - y0)
            
            painter.end()

    def render_page(self, pdf, page_num):
        page = pdf.load_page(page_num)
        pix = page.get_pixmap()
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        return image
    
    def prev_diff(self):
        if self.current_diff_index > 0:
            self.current_diff_index -= 1
            self.show_difference()
    
    def next_diff(self):
        if self.current_diff_index < len(self.differences) - 1:
            self.current_diff_index += 1
            self.show_difference()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFComparator()
    sys.exit(app.exec_())
