from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit
import pyperclip
from logic import process_csv, friendly_reminder_message, delayed_reminder_message

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

        self.search_label = QLabel("Buscar por First Name")
        self.layout.addWidget(self.search_label)

        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.search_table)
        self.layout.addWidget(self.search_box)

        self.result_label = QLabel("")
        self.layout.addWidget(self.result_label)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.current_table_widget = None

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
                self.populate_grouped_table(df_past, "Fechas Pasadas", delayed_reminder_message)
                self.populate_grouped_table(df_future, "Fechas Futuras", friendly_reminder_message)

    def populate_table(self, df, tab_name):
        table_widget = QTableWidget()
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1])
        table_widget.setHorizontalHeaderLabels(list(df.columns))

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table_widget.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

        self.tabs.addTab(table_widget, tab_name)
        if tab_name == "Todos los Registros":
            self.current_table_widget = table_widget

    def populate_grouped_table(self, df, tab_name, message_function):
        table_widget = QTableWidget()
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(2)  # Username y Courses
        table_widget.setHorizontalHeaderLabels(["Username", "Courses"])

        for row in range(df.shape[0]):
            username_item = QTableWidgetItem(str(df.iat[row, df.columns.get_loc("Username")]))
            table_widget.setItem(row, 0, username_item)

            courses = df.iat[row, df.columns.get_loc("Courses")]
            courses_str = "\n".join([f"{course['Item Title']} (ID: {course['Item ID']})" for course in courses])
            courses_item = QTableWidgetItem(courses_str)
            table_widget.setItem(row, 1, courses_item)

            copy_button = QPushButton("Copiar")
            copy_button.clicked.connect(lambda _, r=row, u=username_item, c=courses: self.copy_message(u.text(), c, message_function))
            table_widget.setCellWidget(row, 2, copy_button)

        self.tabs.addTab(table_widget, tab_name)

    def copy_message(self, username, courses, message_function):
        first_name = courses[0]['First Name'] if courses else ''
        message = message_function(first_name, courses)
        pyperclip.copy(message)

    def search_table(self, text):
        if self.current_table_widget:
            for row in range(self.current_table_widget.rowCount()):
                item = self.current_table_widget.item(row, 0)  # Assuming 'First Name' is in the first column
                if item and text.lower() in item.text().lower():
                    self.current_table_widget.setRowHidden(row, False)
                else:
                    self.current_table_widget.setRowHidden(row, True)
