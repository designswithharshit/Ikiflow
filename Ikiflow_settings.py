import os
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QComboBox, QButtonGroup, QScrollArea, 
                               QGroupBox, QCheckBox, QLineEdit, QFormLayout, 
                               QFrame, QGraphicsDropShadowEffect, QScrollBar,
                               QGridLayout, QSizePolicy) 
from PySide6.QtCore import (Qt, Signal, QRectF, QPoint, QPropertyAnimation, 
                            QEasingCurve, QSettings, QTimer, QAbstractAnimation, 
                            QParallelAnimationGroup)
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QCursor

# --- CONSTANTS ---
ACCENT       = "#0984E3"  
ACCENT_FADE  = "rgba(9, 132, 227, 0.15)"
TEXT_MAIN    = "#2D3436" 
TEXT_DIM     = "#636E72" 
TEXT_QUIET   = "#A4AAB0" 
BG_CARD      = "#FFFFFF"
BG_SOFT      = "#F8F9FA" 
BORDER_SOFT  = "#ECEFF1"
SUCCESS      = "#00B894"
WARNING      = "#FAB1A0"

# --- SUPPORTED APPS LIST ---
SUPPORTED_APPS = [
    # --- DESIGN & CREATIVE ---
    "Adobe Illustrator", "Photoshop", "InDesign", "Premiere", 
    "After Effects", "Lightroom", "Adobe XD",
    "Blender", "Figma", "Canva", "DaVinci Resolve",
    
    # --- 3D & ENGINEERING ---
    "Unity", "Unreal Editor", "Maya", "3ds Max", 
    "Cinema 4D", "AutoCAD", "SolidWorks",
    
    # --- CODING & DEV ---
    "Visual Studio Code", "Visual Studio", "PyCharm", 
    "IntelliJ IDEA", "Android Studio", "Sublime Text", 
    "WebStorm", "Godot",
    
    # --- WRITING & OFFICE ---
    "Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint",
    "Notion", "Obsidian", "Evernote", "Scrivener", 
    "Notepad", "Notepad++"
]

# --- 0. COLLAPSIBLE BOX (The new feature) ---
class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        # Toggle Button
        self.toggle_button = QPushButton(title)
        self.toggle_button.setStyleSheet("""
            QPushButton { text-align: left; background: transparent; border: none; font-weight: bold; color: #636E72; padding: 5px; }
            QPushButton:hover { color: #0984E3; }
            QPushButton:checked { color: #2D3436; }
        """)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.on_pressed)

        # Content Area (Hidden by default)
        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Main Layout
        self.lay = QVBoxLayout(self)
        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.addWidget(self.toggle_button)
        self.lay.addWidget(self.content_area)
        
        # Animation
        self.anim = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)

    def set_content_layout(self, layout):
        self.content_area.setLayout(layout)

    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setText("▼ " + self.toggle_button.text()[2:] if checked else "▶ " + self.toggle_button.text()[2:])
        
        # Calculate height
        content_height = self.content_area.layout().sizeHint().height()
        
        self.anim.setDirection(QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward)
        self.anim.setStartValue(0)
        self.anim.setEndValue(content_height)
        self.anim.start()

# --- 1. TOGGLE SWITCH ---
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

# --- 4. SETTING CARD ---
class SettingCard(QWidget):
    def __init__(self, title):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0984E3; border: none; background: transparent;")
        self.main_layout.addWidget(lbl_title)
        
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #F0F0F0; border: none;")
        self.main_layout.addWidget(line)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#FFFFFF"))
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
        
        # --- SAFE MODE: Save settings to 'config.ini' in User Profile ---
        # Path: C:\Users\YourName\Ikiflow_Data\config.ini
        base_path = Path(os.environ['USERPROFILE']) / "Ikiflow_Data"
        # Ensure the folder exists (it should, but just in case)
        base_path.mkdir(parents=True, exist_ok=True)
        ini_path = base_path / "config.ini"
        
        # Initialize Settings with Explicit File Path
        self.settings = QSettings(str(ini_path), QSettings.IniFormat)
        
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px 0px 0px 0px; }
            QScrollBar::handle:vertical { background: #D0D0D0; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #B0B0B0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;") 
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20) 
        content_layout.setContentsMargins(5, 5, 5, 5) 

        # --- CARD 1: VISUALS ---
        card_visuals = SettingCard("Widget Appearance")
        
        row_style = QHBoxLayout()
        row_style.addWidget(QLabel("Style Preset:"))
        
        self.combo_style = QComboBox()
        self.combo_style.setStyleSheet("""
            QComboBox { padding: 5px; border: 1px solid #DFE6E9; border-radius: 5px; background-color: #F8F9FA; padding-right: 28px; }
            QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: 1px solid #DFE6E9; background: transparent; }
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #2D3436; selection-background-color: #F1F2F6; selection-color: #0984E3; border: 1px solid #E0E0E0; outline: none; }
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
        btn_preview.setStyleSheet("QPushButton { background-color: #F8F9FA; color: #2D3436; border: 1px solid #DFE6E9; border-radius: 6px; padding: 8px; font-weight: bold;} QPushButton:hover { background-color: #E0E0E0; }")
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

        # --- NEW: APP SELECTION GROUP (Correct Placement) ---
        content_layout.addWidget(self.create_app_selection_group())

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
        self.main_layout.addWidget(scroll)

        # --- CARD 4: HELP & FEEDBACK ---
        card_help = SettingCard("Support")
        btn_feedback = QPushButton("Send Feedback / Report Bug")
        btn_feedback.setCursor(Qt.PointingHandCursor)
        btn_feedback.setStyleSheet("QPushButton { background-color: #0984E3; color: white; border-radius: 6px; padding: 10px; font-weight: bold; border: none;} QPushButton:hover { background-color: #74B9FF; }")
        btn_feedback.clicked.connect(self.feedback_clicked.emit)
        card_help.add_widget(btn_feedback)
        content_layout.addWidget(card_help)

    def update_pref(self, key, value):
        self.preferences[key] = value

    def emit_design_update(self):
        sel_btn = self.color_group.checkedButton()
        color = sel_btn.color if sel_btn else "#0984E3"

        self.settings.setValue("style_idx", self.combo_style.currentIndex())
        self.settings.setValue("radius", self.slider_round.value())
        self.settings.setValue("theme_color", color)

        self.widget_style_updated.emit(
            self.combo_style.currentIndex(),
            self.slider_round.value(),
            color
        )

    def emit_props_update(self):
        self.settings.setValue("scale", self.slider_scale.value())
        self.settings.setValue("opacity", self.slider_op.value())

        self.widget_props_updated.emit(
            self.slider_scale.value(),
            self.slider_op.value()
        )

    def emit_overlay_update(self):
        text = self.input_msg.text()
        if not text: text = "SCREEN REST"
        self.overlay_text_updated.emit(text)

    def load_settings(self):
        style_idx = int(self.settings.value("style_idx", 0))
        radius = int(self.settings.value("radius", 50))
        scale = int(self.settings.value("scale", 100))
        opacity = int(self.settings.value("opacity", 100))
        color = self.settings.value("theme_color", "#0984E3")

        self.combo_style.setCurrentIndex(style_idx)
        self.slider_round.val = radius 
        self.slider_scale.val = scale
        self.slider_op.val = opacity

        for btn in self.color_group.buttons():
            if btn.color == color:
                btn.setChecked(True)
                break

        self.slider_round.update()
        self.slider_scale.update()
        self.slider_op.update()

        QTimer.singleShot(100, self.emit_design_update)
        QTimer.singleShot(100, self.emit_props_update)

    # --- APP SELECTION GROUP (Correct Placement) ---
    def create_app_selection_group(self):
        card = SettingCard("Auto-Start Triggers")
        
        desc = QLabel("Ikiflow detects these apps and offers to start a timer.")
        desc.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; margin-bottom: 5px;")
        desc.setWordWrap(True)
        card.add_widget(desc)
        
        # CollapsibleBox logic
        collapsible = CollapsibleBox("▶  Select Apps to Monitor")
        
        grid = QGridLayout()
        self.app_checks = {} 
        
        sorted_apps = sorted(SUPPORTED_APPS)
        
        for i, app_name in enumerate(sorted_apps):
            chk = QCheckBox(app_name)
            chk.setCursor(Qt.PointingHandCursor)
            chk.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 12px;")
            
            # --- FIX: Default is now False (Unchecked) ---
            is_enabled = self.settings.value(f"app_trigger_{app_name}", False, type=bool)
            chk.setChecked(is_enabled)
            
            chk.toggled.connect(lambda checked, name=app_name: self.save_app_state(name, checked))
            
            self.app_checks[app_name] = chk
            
            row = i // 2
            col = i % 2
            grid.addWidget(chk, row, col)
            
        collapsible.set_content_layout(grid)
        card.add_widget(collapsible)
        
        return card

    def save_app_state(self, app_name, is_checked):
        self.settings.setValue(f"app_trigger_{app_name}", is_checked)
        # print(f"DEBUG: Set {app_name} to {is_checked}") # Commented out for production