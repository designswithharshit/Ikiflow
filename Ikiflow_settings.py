from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QComboBox, QButtonGroup, QScrollArea, 
                               QGroupBox, QCheckBox, QLineEdit, QFormLayout, 
                               QFrame, QGraphicsDropShadowEffect, QScrollBar)
from PySide6.QtCore import Qt, Signal, QRectF, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QCursor

# --- 1. MODERN TOGGLE SWITCH ---
class ToggleSwitch(QCheckBox):
    def __init__(self, text=""):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(50, 28)
        self.setText("")
        
    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        track_color = QColor("#BDC3C7") 
        if self.isChecked():
            track_color = QColor("#0984E3") 
            
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 0, 50, 28, 14, 14)
        
        thumb_x = 26 if self.isChecked() else 4
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(thumb_x, 4, 20, 20)

# --- 2. CUSTOM SLIDER ---
class ModernSettingsSlider(QWidget):
    valueChanged = Signal(int)
    def __init__(self, min_val=0, max_val=100, default_val=50, suffix=""):
        super().__init__()
        self.min_val, self.max_val, self.val = min_val, max_val, default_val
        self.suffix = suffix
        self.setMinimumHeight(35)
        self.dragging = False

    def value(self): return self.val
    
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.update_val(e.position().x())
    def mouseMoveEvent(self, e):
        if self.dragging: self.update_val(e.position().x())
    def mouseReleaseEvent(self, e): self.dragging = False
    
    def update_val(self, x):
        padding, txt_w = 10, 40
        ratio = max(0.0, min(1.0, (x-padding)/(self.width()-padding*2-txt_w)))
        new_val = self.min_val + int(ratio*(self.max_val-self.min_val))
        if new_val != self.val:
            self.val = new_val
            self.valueChanged.emit(self.val)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pad, y, txt_w = 10, self.height()//2, 40
        track_w = self.width() - pad*2 - txt_w
        
        painter.setPen(QPen(QColor("#DFE6E9"), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(pad, y, pad+track_w, y)
        
        active_w = track_w * ((self.val-self.min_val)/(self.max_val-self.min_val))
        painter.setPen(QPen(QColor("#0984E3"), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(pad, y, pad+active_w, y)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#0984E3"))
        painter.drawEllipse(QPoint(int(pad+active_w), y), 8, 8)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPoint(int(pad+active_w), y), 3, 3)
        
        painter.setPen(QColor("#2D3436"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(QRectF(self.width()-txt_w, 0, txt_w, self.height()), Qt.AlignCenter, f"{self.val}{self.suffix}")

# --- 3. COLOR BUTTON ---
class ColorPresetButton(QPushButton):
    def __init__(self, color_hex, is_selected=False):
        super().__init__()
        self.color = color_hex
        self.setFixedSize(26, 26)
        self.setCheckable(True)
        self.setChecked(is_selected)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3, 3, -3, -3)
        
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect)
        
        if self.color.upper() == "#FFFFFF":
             painter.setPen(QPen(QColor("#DFE6E9"), 1))
             painter.setBrush(Qt.NoBrush)
             painter.drawEllipse(rect)

        if self.isChecked():
            painter.setPen(QPen(QColor("#2D3436"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(self.rect().adjusted(1,1,-1,-1))

# --- 4. SETTING CARD (Paint-Based) ---
class SettingCard(QWidget):
    def __init__(self, title):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        lbl_title = QLabel(title)
        # Explicitly remove border/background for title
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0984E3; border: none; background: transparent;")
        self.main_layout.addWidget(lbl_title)
        
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #F0F0F0; border: none;")
        self.main_layout.addWidget(line)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # White Card Background
        painter.setBrush(QColor("#FFFFFF"))
        # Subtle Border
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 12, 12)

    def add_widget(self, widget):
        self.main_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self.main_layout.addLayout(layout)

# --- 5. MAIN SETTINGS TAB ---

class SettingsTab(QWidget):
    preview_toggled = Signal()
    widget_style_updated = Signal(int, int, str)
    widget_props_updated = Signal(int, int) 
    overlay_text_updated = Signal(str)
    feedback_clicked = Signal()
    
    preferences = {
        "minimize_to_tray": True,
        "sound_enabled": True,
        "auto_start_break": False
    }

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        # Seamless Scrollbar CSS
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px 0px 0px 0px; }
            QScrollBar::handle:vertical { background: #D0D0D0; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #B0B0B0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;") # Force transparent
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20) # More breathing room between cards
        content_layout.setContentsMargins(5, 5, 5, 5) # Tight margins so cards are wide

        # --- CARD 1: VISUALS ---
        card_visuals = SettingCard("Widget Appearance")
        
        row_style = QHBoxLayout()
        row_style.addWidget(QLabel("Style Preset:"))
        
        # --- FIXED DROPDOWN MENU STYLE ---
        self.combo_style = QComboBox()
        # This explicit style ensures the popup list (QAbstractItemView) is white
        self.combo_style.setStyleSheet("""
            QComboBox { 
                padding: 5px; 
                border: 1px solid #DFE6E9; 
                border-radius: 5px; 
                background-color: #F8F9FA;
                padding-right: 28px; 
            }
            QComboBox::drop-down { 
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #DFE6E9;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #2D3436;
                selection-background-color: #F1F2F6;
                selection-color: #0984E3;
                border: 1px solid #E0E0E0;
                outline: none;
            }
        """)
        self.combo_style.addItems(["Standard Pill", "Modern Box", "Minimal Text", "Bold & Barless", "Glass Panel"])
        self.combo_style.currentIndexChanged.connect(self.emit_design_update)
        
        row_style.addWidget(self.combo_style, 1)
        card_visuals.add_layout(row_style)

        row_color = QHBoxLayout()
        row_color.addWidget(QLabel("Accent Color:"))
        self.color_group = QButtonGroup(self)
        colors = [("#0984E3", True), ("#E17055", False), ("#00B894", False), ("#2D3436", False), ("#FFFFFF", False)]
        for hex_code, active in colors:
            btn = ColorPresetButton(hex_code, active)
            btn.clicked.connect(self.emit_design_update)
            self.color_group.addButton(btn)
            row_color.addWidget(btn)
        row_color.addStretch()
        card_visuals.add_layout(row_color)

        card_visuals.add_widget(QLabel("Corner Roundness"))
        self.slider_round = ModernSettingsSlider(0, 100, 50, "%")
        self.slider_round.valueChanged.connect(self.emit_design_update)
        card_visuals.add_widget(self.slider_round)

        card_visuals.add_widget(QLabel("Size Scale"))
        self.slider_scale = ModernSettingsSlider(30, 150, 100, "%")
        self.slider_scale.valueChanged.connect(self.emit_props_update)
        card_visuals.add_widget(self.slider_scale)

        card_visuals.add_widget(QLabel("Opacity"))
        self.slider_op = ModernSettingsSlider(20, 100, 100, "%")
        self.slider_op.valueChanged.connect(self.emit_props_update)
        card_visuals.add_widget(self.slider_op)

        btn_preview = QPushButton("Toggle Desktop Preview")
        btn_preview.setStyleSheet("""
            QPushButton { background-color: #F8F9FA; color: #2D3436; border: 1px solid #DFE6E9; border-radius: 6px; padding: 8px; font-weight: bold;}
            QPushButton:hover { background-color: #E0E0E0; }
        """)
        btn_preview.clicked.connect(self.preview_toggled.emit)
        card_visuals.add_widget(btn_preview)
        
        content_layout.addWidget(card_visuals)

        # --- CARD 2: OVERLAY ---
        card_overlay = SettingCard("Break Screen")
        self.input_msg = QLineEdit("SCREEN REST")
        self.input_msg.setPlaceholderText("Enter screen message...")
        self.input_msg.setStyleSheet("QLineEdit { padding: 10px; border: 1px solid #DFE6E9; border-radius: 6px; background: #FAFAFA; } QLineEdit:focus { border: 1px solid #0984E3; }")
        self.input_msg.textChanged.connect(self.emit_overlay_update)
        card_overlay.add_widget(QLabel("Custom Message:"))
        card_overlay.add_widget(self.input_msg)
        content_layout.addWidget(card_overlay)

        # --- CARD 3: SYSTEM ---
        card_sys = SettingCard("System & Behavior")
        
        def create_toggle_row(text, key, default=True):
            row = QHBoxLayout()
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 13px; background: transparent; border: none;")
            toggle = ToggleSwitch()
            toggle.setChecked(default)
            toggle.stateChanged.connect(lambda: self.update_pref(key, toggle.isChecked()))
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(toggle)
            return row, toggle

        row_tray, self.chk_tray = create_toggle_row("Minimize to Tray on Close", "minimize_to_tray")
        card_sys.add_layout(row_tray)
        
        row_sound, self.chk_sound = create_toggle_row("Sound Notifications", "sound_enabled")
        card_sys.add_layout(row_sound)
        
        row_auto, self.chk_auto = create_toggle_row("Auto-start Break", "auto_start_break", False)
        card_sys.add_layout(row_auto)
        
        content_layout.addWidget(card_sys)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # --- CARD 4: HELP & FEEDBACK ---
        card_help = SettingCard("Support")
        
        btn_feedback = QPushButton("Send Feedback / Report Bug")
        btn_feedback.setCursor(Qt.PointingHandCursor)
        btn_feedback.setStyleSheet("""
            QPushButton { background-color: #0984E3; color: white; border-radius: 6px; padding: 10px; font-weight: bold; border: none;}
            QPushButton:hover { background-color: #74B9FF; }
        """)
        # Emit signal when clicked
        btn_feedback.clicked.connect(self.feedback_clicked.emit)
        
        card_help.add_widget(btn_feedback)
        content_layout.addWidget(card_help)

    def update_pref(self, key, value):
        self.preferences[key] = value

    def emit_design_update(self):
        sel_btn = self.color_group.checkedButton()
        color = sel_btn.color if sel_btn else "#0984E3"
        self.widget_style_updated.emit(
            self.combo_style.currentIndex(),
            self.slider_round.value(),
            color
        )

    def emit_props_update(self):
        self.widget_props_updated.emit(
            self.slider_scale.value(),
            self.slider_op.value()
        )

    def emit_overlay_update(self):
        text = self.input_msg.text()
        if not text: text = "SCREEN REST"
        self.overlay_text_updated.emit(text)

        