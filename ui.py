from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit, QHBoxLayout
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
        self.layout.addWidget(self.search_box)

        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_table)
        self.layout.addWidget(self.search_button)

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
        for username, user_courses in df.groupby('Username'):
            user_courses.reset_index(drop=True, inplace=True)
            table_widget = QTableWidget()
            table_widget.setRowCount(user_courses.shape[0])
            table_widget.setColumnCount(len(user_courses.columns) + 1)  # Añadir una columna para el botón de copiar
            table_widget.setHorizontalHeaderLabels(list(user_courses.columns) + ["Acciones"])

            for row in range(user_courses.shape[0]):
                for col in range(user_courses.shape[1]):
                    table_widget.setItem(row, col, QTableWidgetItem(str(user_courses.iat[row, col])))

                copy_button = QPushButton("Copiar")
                copy_button.clicked.connect(lambda _, r=row: self.copy_row(user_courses.iloc[r]))
                table_widget.setCellWidget(row, user_courses.shape[1], copy_button)

            header_layout = QHBoxLayout()
            header_label = QLabel(f"{user_courses['First Name'][0]} {user_courses['Last Name'][0]} ({user_courses.shape[0]} Cursos Pendientes)")
            copy_all_button = QPushButton("Copiar Todo")
            copy_all_button.clicked.connect(lambda _, u=username: self.copy_all(user_courses, message_function))
            header_layout.addWidget(header_label)
            header_layout.addWidget(copy_all_button)

            header_widget = QWidget()
            header_widget.setLayout(header_layout)
            self.tabs.addTab(table_widget, username)
            self.tabs.setTabBar(header_widget)

    def copy_row(self, row_data):
        message = friendly_reminder_message(row_data['First Name'], [row_data.to_dict()])
        pyperclip.copy(message)

    def copy_all(self, user_courses, message_function):
        first_name = user_courses['First Name'].iloc[0] if not user_courses.empty else ''
        message = message_function(first_name, user_courses.to_dict('records'))
        pyperclip.copy(message)

    def search_table(self):
        text = self.search_box.text().lower()
        if self.current_table_widget:
            for row in range(self.current_table_widget.rowCount()):
                item = self.current_table_widget.item(row, self.current_table_widget.columnCount() - 1)  # Assuming 'First Name' is in the last column
                if item and text in item.text().lower():
                    self.current_table_widget.setRowHidden(row, False)
                else:
                    self.current_table_widget.setRowHidden(row, True)
