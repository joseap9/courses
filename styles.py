# Estilos generales de la aplicación
APP_STYLE = """
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    QPushButton {
        background-color: white;
        border: 2px solid #338AFF;
        color: #338AFF;
        border-radius: 10px;
        padding: 5px 10px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #e6f0ff;
    }
"""

# Estilo de las pestañas principales
MAIN_TAB_STYLE = """
    QTabBar::tab {
        font-size: 16px;
        color: #338AFF;
        padding: 12px 20px;
        border: 1px solid black;
        border-radius: 10px;
    }
    QTabBar::tab:selected {
        font: bold 16px;
        color: #338AFF;
    }
    QTabWidget::pane {
        border-top: 2px solid #338AFF;
    }
"""

# Estilo de las pestañas secundarias
SUB_TAB_STYLE = """
    QTabBar::tab {
        font-size: 14px;
        color: #338AFF;
        padding: 10px 15px;
        border: 1px solid black;
        border-radius: 8px;
    }
    QTabBar::tab:selected {
        font: bold 14px;
        color: #338AFF;
    }
    QTabWidget::pane {
        border-top: 1px solid #338AFF;
    }
"""
