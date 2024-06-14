from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import pyperclip
from logic import process_csv, friendly_reminder_message, delayed_reminder_message
import styles

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Analyzer")
        self.setGeometry(100, 100, 1200, 800)

        self.layout = QVBoxLayout()

        self.file_layout = QHBoxLayout()
        self.label = QLabel("Seleccione un archivo CSV")
        self.file_layout.addWidget(self.label)

        self.button = QPushButton("Seleccionar archivo CSV")
        self.button.clicked.connect(self.open_file_dialog)
        self.file_layout.addWidget(self.button)
        self.layout.addLayout(self.file_layout)

        # Agregar una imagen
        self.image_label = QLabel()
        pixmap = QPixmap('path/to/your/image.png')  # Reemplaza con la ruta de tu imagen
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.image_label)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(styles.MAIN_TAB_STYLE)
        self.layout.addWidget(self.tabs)

        self.all_records_tab = QWidget()
        self.all_records_layout = QVBoxLayout()
        self.all_records_table = QTableWidget()
        self.all_records_layout.addWidget(self.all_records_table)
        self.all_records_tab.setLayout(self.all_records_layout)
        self.tabs.addTab(self.all_records_tab, "Todos los Registros")

        self.delayed_courses_tab = QWidget()
        self.delayed_courses_layout = QVBoxLayout()
        self.delayed_tabs = QTabWidget()
        self.delayed_tabs.setStyleSheet(styles.SUB_TAB_STYLE)
        self.delayed_courses_layout.addWidget(self.delayed_tabs)
        self.delayed_courses_tab.setLayout(self.delayed_courses_layout)
        self.tabs.addTab(self.delayed_courses_tab, "Delayed Courses")

        self.future_courses_tab = QWidget()
        self.future_courses_layout = QVBoxLayout()
        self.future_tabs = QTabWidget()
        self.future_tabs.setStyleSheet(styles.SUB_TAB_STYLE)
        self.future_courses_layout.addWidget(self.future_tabs)
        self.future_courses_tab.setLayout(self.future_courses_layout)
        self.tabs.addTab(self.future_courses_tab, "Courses About to Past Due")

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.current_table_widget = self.all_records_table

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo CSV", "", "Archivos CSV (*.csv)", options=options)
        if file_name:
            df_all, df_past, df_future = process_csv(file_name)
            if isinstance(df_all, str) or isinstance(df_past, str) or isinstance(df_future, str):
                self.result_label.setText(f"Error: {df_all}")
            else:
                self.populate_table(df_all, self.all_records_table)
                self.populate_grouped_table(df_past, self.delayed_tabs, delayed_reminder_message)
                self.populate_grouped_table(df_future, self.future_tabs, friendly_reminder_message)

    def populate_table(self, df, table_widget):
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1])
        table_widget.setHorizontalHeaderLabels(list(df.columns))

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table_widget.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

        if table_widget == self.all_records_table:
            self.current_table_widget = table_widget

    def populate_grouped_table(self, df, tab_widget, message_function):
        for username, user_courses in df.groupby('Username'):
            user_courses.reset_index(drop=True, inplace=True)
            user_tab = QWidget()
            user_layout = QVBoxLayout()
            user_tab.setLayout(user_layout)

            table_widget = QTableWidget()
            table_widget.setRowCount(user_courses.shape[0])
            table_widget.setColumnCount(len(user_courses.columns) + 1)  # Añadir una columna para el botón de copiar
            table_widget.setHorizontalHeaderLabels(list(user_courses.columns) + ["Acciones"])
            table_widget.horizontalHeader().setStretchLastSection(True)

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
            user_layout.addWidget(header_widget)
            user_layout.addWidget(table_widget)

            tab_widget.addTab(user_tab, f"{user_courses['First Name'][0]} {user_courses['Last Name'][0]}")

    def copy_row(self, row_data):
        message = friendly_reminder_message(row_data['First Name'], [row_data.to_dict()])
        pyperclip.copy(message)

    def copy_all(self, user_courses, message_function):
        first_name = user_courses['First Name'].iloc[0] if not user_courses.empty else ''
        message = message_function(first_name, user_courses.to_dict('records'))
        pyperclip.copy(message)
