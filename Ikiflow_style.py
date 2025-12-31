# --- 1. CONFIGURATION & STYLES ---
STYLESHEET = """
QWidget { font-family: 'Segoe UI', sans-serif; color: #2D3436; }

/* Tabs inside the Card */
QTabWidget::pane { border: none; background: transparent; }
QTabWidget::tab-bar { alignment: center; }
QTabBar::tab {
    background: transparent; color: #636E72; padding: 8px 15px;
    font-weight: bold; border-bottom: 3px solid transparent;
    margin-bottom: 5px;
}
QTabBar::tab:selected { color: #0984E3; border-bottom: 3px solid #0984E3; }
QTabBar::tab:hover { color: #0984E3; }

/* Typography */
QLabel { border: none; background: transparent; }
QLabel#Title { font-size: 22px; font-weight: 800; color: #2D3436; }
QLabel#LabelBold { font-size: 13px; font-weight: bold; color: #2D3436; margin-top: 5px; }
QLabel#BigTimer { font-size: 64px; font-weight: 800; color: #2D3436; }
QLabel#StatusLabel { font-size: 16px; font-weight: 600; color: #636E72; }

/* Buttons */
QPushButton#ActionBtn {
    background-color: #0984E3; color: white; border-radius: 12px;
    padding: 12px; font-weight: bold; font-size: 14px; border: none;
}
QPushButton#ActionBtn:hover { background-color: #74B9FF; }

QPushButton#PauseBtn {
    background-color: #FDCB6E; color: #2D3436; border-radius: 12px;
    padding: 12px; font-weight: bold; font-size: 14px; border: none;
}
QPushButton#PauseBtn:hover { background-color: #FFEAA7; }

QPushButton#StopBtn { 
    background-color: #FF7675; color: white; border-radius: 12px; 
    padding: 12px; font-weight: bold; border: none; 
}
QPushButton#StopBtn:hover { background-color: #FF5252; }
"""
