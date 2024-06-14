# Main tab style
MAIN_TAB_STYLE = """
    QTabBar::tab {
        font-size: 16px;
        color: #338AFF;
        padding: 12px 20px;
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

# Sub tab style
SUB_TAB_STYLE = """
    QTabBar::tab {
        font-size: 14px;
        color: #338AFF;
        padding: 10px 15px;
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