from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem
import pyperclip
from logic import process_csv

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Analyzer")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.label = QLabel("Seleccione un archivo CSV")
        self.layout.addWidget(self.label)

        self.button = QPushButton("Seleccionar archivo CSV")
        self.button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.button)

        self.result_label = QLabel("")
        self.layout.addWidget(self.result_label)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo CSV", "", "Archivos CSV (*.csv)", options=options)
        if file_name:
            df_all, df_past, df_future = process_csv(file_name)
            if isinstance(df_all, str) or isinstance(df_past, str) or isinstance(df_future, str):
                self.result_label.setText(f"Error: {df_all}")
            else:
                self.tabs.clear()
                self.populate_table(df_all, "Todos los Registros")
                self.populate_table(df_past, "Fechas Pasadas", add_copy_buttons=True, message_template="Hola {First_Name}, los cursos: {Item_Title} están pendientes")
                self.populate_table(df_future, "Fechas Futuras", add_copy_buttons=True, message_template="Hola {First_Name}, recuerda que los cursos: {Item_Title} empiezan pronto")

    def populate_table(self, df, tab_name, add_copy_buttons=False, message_template=""):
        table_widget = QTableWidget()
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1] + (1 if add_copy_buttons else 0))
        table_widget.setHorizontalHeaderLabels(list(df.columns) + ([""] if add_copy_buttons else []))

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table_widget.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

            if add_copy_buttons:
                copy_button = QPushButton("Copiar")
                copy_button.clicked.connect(lambda _, r=row, btn=copy_button, tpl=message_template: self.copy_to_clipboard(df, r, btn, tpl))
                table_widget.setCellWidget(row, df.shape[1], copy_button)

        self.tabs.addTab(table_widget, tab_name)

    def copy_to_clipboard(self, df, row, button, message_template):
        try:
            print("Columnas del DataFrame:", df.columns)
            name = df.iat[row, df.columns.get_loc("First Name")]
            course = df.iat[row, df.columns.get_loc("Item Title")]
            message = message_template.format(First_Name=name, Item_Title=course)
            pyperclip.copy(message)
            button.setText("✔")
        except KeyError as e:
            print(f"Error al acceder a la columna: {e}")
            self.result_label.setText(f"Error: {e}")
