import math
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QProgressBar, 
                               QSpinBox, QVBoxLayout, QHBoxLayout, QFrame, 
                               QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QStackedWidget, QApplication,
                               QDialog, QLineEdit, QListWidget, QMenu)
from PySide6.QtCore import (Qt, QPoint, QRectF, QTimer, Signal, QSize, QSettings, QPropertyAnimation, QEasingCurve)
from PySide6.QtGui import (QColor, QPainter, QPen, QFont, QAction,)

# --- 1. CUSTOM WINDOW BUTTON ---

class ModernWindowButton(QPushButton):
    """Custom painted minimize/close button."""
    def __init__(self, btn_type="close", parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.btn_type = btn_type
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background on hover
        if self.underMouse():
            bg_color = QColor("#FF7675") if self.btn_type == "close" else QColor("#DFE6E9")
            painter.setBrush(bg_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), 5, 5)
            
        # Icon color
        icon_color = QColor("#FFFFFF") if self.underMouse() and self.btn_type == "close" else QColor("#636E72")
        pen = QPen(icon_color, 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        if self.btn_type == "close":
            painter.drawLine(10, 10, 20, 20)
            painter.drawLine(20, 10, 10, 20)
        elif self.btn_type == "min":
            painter.drawLine(10, 15, 20, 15)

# --- 2. INTENT DIALOG (NEW) ---

class IntentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 450)
        self.selected_mode = "Deep_Single" # Default
        self.final_intent = {} # Stores result
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame { 
                background: #FFFFFF; 
                border-radius: 20px; 
                border: 1px solid #E0E0E0;
            }
        """)
        self.layout.addWidget(self.card)
        
        self.inner = QVBoxLayout(self.card)
        self.inner.setContentsMargins(30, 30, 30, 30)
        
        # Header
        lbl_title = QLabel("Set Your Intent")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #2D3436;")
        self.inner.addWidget(lbl_title)
        
        # Mode Tabs
        self.tabs = QHBoxLayout()
        self.btn_single = self.create_tab_btn("Deep Focus", True)
        self.btn_multi = self.create_tab_btn("Multi Task", False)
        self.btn_free = self.create_tab_btn("Free Mode", False)
        
        self.tabs.addWidget(self.btn_single)
        self.tabs.addWidget(self.btn_multi)
        self.tabs.addWidget(self.btn_free)
        self.inner.addLayout(self.tabs)
        
        # Content Stack
        self.stack = QStackedWidget()
        
        # PAGE 1: Single Task
        p1 = QWidget()
        l1 = QVBoxLayout(p1)
        self.inp_single = QLineEdit()
        self.inp_single.setPlaceholderText("What is your anchor task?")
        self.inp_single.setStyleSheet("QLineEdit { padding: 10px; border: 1px solid #E0E0E0; border-radius: 8px; background: #FAFAFA; color: #2D3436; }")
        l1.addWidget(QLabel("ONE THING ONLY"))
        l1.addWidget(self.inp_single)
        l1.addStretch()
        self.stack.addWidget(p1)
        
        # PAGE 2: Multi Task
        p2 = QWidget()
        l2 = QVBoxLayout(p2)
        self.inp_multi = QLineEdit()
        self.inp_multi.setPlaceholderText("Add a task + Press Enter")
        self.inp_multi.setStyleSheet(self.inp_single.styleSheet())
        self.inp_multi.returnPressed.connect(self.add_multi_task)
        
        self.list_multi = QListWidget()
        self.list_multi.setStyleSheet("QListWidget { border: none; background: transparent; color: #2D3436; }")
        
        l2.addWidget(QLabel("STRUCTURED CHAOS"))
        l2.addWidget(self.inp_multi)
        l2.addWidget(self.list_multi)
        self.stack.addWidget(p2)
        
        # PAGE 3: Free Mode
        p3 = QWidget()
        l3 = QVBoxLayout(p3)
        lbl_free = QLabel("“I am not wasting time—\nI am watching it.”")
        lbl_free.setStyleSheet("color: #636E72; font-style: italic; font-size: 14px;")
        lbl_free.setAlignment(Qt.AlignCenter)
        l3.addStretch()
        l3.addWidget(lbl_free)
        l3.addStretch()
        self.stack.addWidget(p3)
        
        self.inner.addWidget(self.stack)
        
        # Begin Button
        self.btn_begin = QPushButton("Begin Cycle")
        self.btn_begin.setCursor(Qt.PointingHandCursor)
        self.btn_begin.setStyleSheet("""
            QPushButton { background: #2D3436; color: white; border-radius: 10px; padding: 12px; font-weight: bold; }
            QPushButton:hover { background: #000000; }
        """)
        self.btn_begin.clicked.connect(self.accept_intent)
        self.inner.addWidget(self.btn_begin)
        
        # Connections
        self.btn_single.clicked.connect(lambda: self.set_mode("Deep_Single", 0))
        self.btn_multi.clicked.connect(lambda: self.set_mode("Deep_Multi", 1))
        self.btn_free.clicked.connect(lambda: self.set_mode("Free", 2))

    def create_tab_btn(self, text, active):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setCursor(Qt.PointingHandCursor)
        self.update_btn_style(btn)
        return btn

    def update_btn_style(self, btn):
        if btn.isChecked():
            btn.setStyleSheet("background: #0984E3; color: white; border: none; border-radius: 15px; padding: 5px 10px; font-size: 10px; font-weight: bold;")
        else:
            btn.setStyleSheet("background: #F1F2F6; color: #636E72; border: none; border-radius: 15px; padding: 5px 10px; font-size: 10px;")

    def set_mode(self, mode, idx):
        self.selected_mode = mode
        self.stack.setCurrentIndex(idx)
        
        # Update buttons visually
        for b in [self.btn_single, self.btn_multi, self.btn_free]: b.setChecked(False)
        if idx == 0: self.btn_single.setChecked(True)
        if idx == 1: self.btn_multi.setChecked(True)
        if idx == 2: self.btn_free.setChecked(True)
        
        for b in [self.btn_single, self.btn_multi, self.btn_free]: self.update_btn_style(b)

    def add_multi_task(self):
        txt = self.inp_multi.text().strip()
        if txt:
            self.list_multi.addItem("• " + txt)
            self.inp_multi.clear()

    def accept_intent(self):
        # Package data based on mode
        self.final_intent = {"mode": self.selected_mode, "tasks": []}
        
        if self.selected_mode == "Deep_Single":
            task = self.inp_single.text().strip()
            if not task: task = "Deep Work" # Default
            self.final_intent["tasks"] = [task]
            
        elif self.selected_mode == "Deep_Multi":
            items = [self.list_multi.item(i).text().replace("• ", "") for i in range(self.list_multi.count())]
            if not items: items = ["General Focus"]
            self.final_intent["tasks"] = items
            
        elif self.selected_mode == "Free":
            self.final_intent["tasks"] = ["Free Flow"]
            
        self.accept()

# --- 3. CIRCULAR TIME INPUT ---

class CircularTimeInput(QWidget):
    def __init__(self, presets, default_idx=3):
        super().__init__()
        self.presets = presets
        self.setMinimumSize(240, 240)
        self.is_dragging = False
        self.current_value = self.presets[default_idx]
        self.visual_ratio = self.get_ratio_for_value(self.current_value)

        self.spin_box = QSpinBox(self)
        self.spin_box.setRange(1, 180)
        self.spin_box.setValue(self.current_value)
        self.spin_box.setAlignment(Qt.AlignCenter)
        self.spin_box.setButtonSymbols(QSpinBox.NoButtons)
        self.spin_box.setStyleSheet("background: transparent; border: none; font-size: 38px; font-weight: bold; color: #2D3436; padding: 0px;")
        self.spin_box.valueChanged.connect(self.on_spinbox_change)

    def resizeEvent(self, event):
        sb_w, sb_h = 100, 60
        self.spin_box.setGeometry((self.width() - sb_w) // 2, (self.height() - sb_h) // 2 - 10, sb_w, sb_h)
        super().resizeEvent(event)

    def on_spinbox_change(self):
        if not self.is_dragging:
            val = self.spin_box.value()
            self.current_value = val
            self.visual_ratio = self.get_ratio_for_value(val)
            self.update()

    def value(self): return self.spin_box.value()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if (event.position() - QPoint(self.width()/2, self.height()/2)).manhattanLength() > 40: 
                self.is_dragging = True
                self.update_drag(event.position())

    def mouseMoveEvent(self, event):
        if self.is_dragging: self.update_drag(event.position())

    def mouseReleaseEvent(self, event): self.is_dragging = False

    def update_drag(self, pos):
        dx = pos.x() - self.width()/2
        dy = pos.y() - self.height()/2
        bearing = (math.degrees(math.atan2(dy, dx)) + 90) % 360
        shifted = bearing - 225
        if shifted < 0: shifted += 360
        
        if shifted > 270: raw_ratio = 1.0 if shifted < 315 else 0.0
        else: raw_ratio = shifted / 270.0

        self.visual_ratio = raw_ratio
        idx = int(round(raw_ratio * (len(self.presets) - 1)))
        new_val = self.presets[idx]
        
        if new_val != self.current_value:
            self.current_value = new_val
            self.spin_box.blockSignals(True)
            self.spin_box.setValue(new_val)
            self.spin_box.blockSignals(False)
        self.update()

    def get_ratio_for_value(self, val):
        if val <= self.presets[0]: return 0.0
        if val >= self.presets[-1]: return 1.0
        if val in self.presets: return self.presets.index(val) / (len(self.presets)-1)
        for i in range(len(self.presets)-1):
            if self.presets[i] < val < self.presets[i+1]:
                return (i + (val-self.presets[i])/(self.presets[i+1]-self.presets[i])) / (len(self.presets)-1)
        return 0.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height()) - 30
        rect = QRectF((self.width()-size)/2, (self.height()-size)/2, size, size)
        
        painter.setPen(QPen(QColor("#DFE6E9"), 14, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225*16, -270*16)
        
        painter.setPen(QPen(QColor("#0984E3"), 14, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225*16, int(-270*16*self.visual_ratio))
        
        angle = math.radians(225 - (self.visual_ratio * 270))
        cx, cy = rect.center().x(), rect.center().y()
        hx, hy = cx + (size/2)*math.cos(angle), cy - (size/2)*math.sin(angle)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0,0,0,40))
        painter.drawEllipse(QPoint(int(hx), int(hy)+3), 12, 12)
        painter.setBrush(QColor("#0984E3"))
        painter.drawEllipse(QPoint(int(hx), int(hy)), 12, 12)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPoint(int(hx), int(hy)), 5, 5)
        
        painter.setPen(QColor("#636E72"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(QRectF(rect.x(), rect.y()+45, rect.width(), rect.height()), Qt.AlignCenter, "min")

# --- 4. LINEAR INPUT ---

class CustomLinearInput(QWidget):
    def __init__(self, presets, default_idx=2):
        super().__init__()
        self.presets = presets
        self.current_idx = default_idx
        self.setMinimumHeight(80)
        self.dragging = False
        
        self.spin_box = QSpinBox(self)
        self.spin_box.setRange(1, 180)
        self.spin_box.setValue(self.presets[self.current_idx])
        self.spin_box.setAlignment(Qt.AlignCenter)
        self.spin_box.setButtonSymbols(QSpinBox.NoButtons)
        self.spin_box.setStyleSheet("background: #F1F2F6; border-radius: 6px; font-weight: bold; font-size: 16px; color: #2D3436;")
        self.spin_box.resize(50, 35)
        self.spin_box.valueChanged.connect(self.on_spinbox_change)

        self.settings = QSettings()

    def resizeEvent(self, event):
        self.spin_box.move(self.width() - 60, 0)
        super().resizeEvent(event)

    def on_spinbox_change(self):
        val = self.spin_box.value()
        if val in self.presets: self.current_idx = self.presets.index(val)
        else: self.current_idx = min(range(len(self.presets)), key=lambda i: abs(self.presets[i]-val))
        self.update()

    def value(self): return self.spin_box.value()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.snap_to_x(e.position().x())

    def mouseMoveEvent(self, e):
        if self.dragging: self.snap_to_x(e.position().x())
    def mouseReleaseEvent(self, e):
        self.dragging = False
        self.settings.setValue("pos", self.pos())

    def snap_to_x(self, x):
        padding = 20
        ratio = max(0.0, min(1.0, (x-padding)/(self.width()-padding*2)))
        new_idx = int(round(ratio * (len(self.presets)-1)))
        if new_idx != self.current_idx:
            self.current_idx = new_idx
            self.spin_box.blockSignals(True)
            self.spin_box.setValue(self.presets[new_idx])
            self.spin_box.blockSignals(False)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        padding, y = 20, 50
        w_track = self.width() - padding*2
        
        painter.setPen(QPen(QColor("#DFE6E9"), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(padding, y, self.width()-padding, y)
        
        active_w = w_track * (self.current_idx / (len(self.presets)-1))
        painter.setPen(QPen(QColor("#0984E3"), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(padding, y, padding+active_w, y)
        
        hx = padding + active_w
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#0984E3"))
        painter.drawEllipse(QPoint(int(hx), y), 10, 10)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPoint(int(hx), y), 4, 4)
        
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for i, val in enumerate(self.presets):
            tx = padding + w_track * (i/(len(self.presets)-1))
            painter.setPen(QColor("#0984E3") if i == self.current_idx else QColor("#B2BEC3"))
            painter.drawText(QRectF(tx-15, y+15, 30, 20), Qt.AlignCenter, str(val))

# --- 5. FLOATING WIDGET (UPDATED) ---

class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("Ikiflow", "FloatingWidget")
        saved_pos = self.settings.value("pos")
        if saved_pos:
            self.move(saved_pos)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Base size
        self.base_w, self.base_h = 240, 90 # Slightly taller for Task Label
        self.resize(self.base_w, self.base_h)

        # Drag / snap state
        self.dragging = False
        self.offset = QPoint()
        self.is_snapped = False

        # Intent Data State
        self.mode = "Free"
        self.task_list = []
        self.current_task = ""

        # Style defaults
        self.style_idx = 0
        self.corner_r_pct = 50
        self.theme_color = "#0984E3"
        self.bg_color = "#FFFFFF"
        self.text_color = "#2D3436"
        self.bar_bg = "#DFE6E9"

        # Layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("ContainerFrame")
        root.addWidget(self.container)

        inner = QVBoxLayout(self.container)
        self.container_layout = inner
        inner.setContentsMargins(20, 5, 20, 10) # Adjusted margins
        inner.setSpacing(0)

        # 1. New Task Label
        self.lbl_task = QLabel("")
        self.lbl_task.setAlignment(Qt.AlignCenter)
        self.lbl_task.setStyleSheet("font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 0px;")
        
        # 2. Timer
        self.time_lbl = QLabel("Ready")
        self.time_lbl.setAlignment(Qt.AlignCenter)

        # 3. Bar
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)

        inner.addWidget(self.lbl_task)
        inner.addWidget(self.time_lbl)
        inner.addWidget(self.bar)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.apply_style()

    # --- INTENT LOGIC (CLEAN VERSION) ---
    def set_session_data(self, mode, tasks):
        self.mode = mode
        self.task_list = tasks
        
        # FIX: Always hide the label. The user wants a clean timer only.
        self.lbl_task.hide() 
        self.lbl_task.setText("") # Clear it just in case
        
        # We still store the task name so it saves to history.json later
        self.current_task = tasks[0] if tasks else "Focus"

    def contextMenuEvent(self, event):
        # Only show menu if we have multiple tasks
        if self.mode == "Deep_Multi" and len(self.task_list) > 1:
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { background: white; border-radius: 5px; } QMenu::item { padding: 5px 20px; color: #2D3436; } QMenu::item:selected { background: #F1F2F6; }")
            
            lbl = menu.addAction("SWITCH TASK:")
            lbl.setEnabled(False)
            menu.addSeparator()
            
            for t in self.task_list:
                action = menu.addAction(t)
                action.triggered.connect(lambda checked=False, task=t: self.switch_task(task))
            
            menu.exec(event.globalPos())

    def switch_task(self, task_name):
        self.current_task = task_name
        self.lbl_task.setText(task_name)

    # ---------- STYLE ----------
    def apply_style(self):

        self.container.show()
        self.bar.show()
        self.time_lbl.show()
        
        # Logic to show/hide task label based on mode is handled in set_session_data
        # Here we just set colors

        h = max(1, self.height())
        m_y = max(2, int(h * 0.1))
        m_x = max(5, int(self.width() * 0.08))
        
        # Only adjust margins if they changed significantly to avoid jitter
        # Using fixed margins usually works better with the added Label
        
        f_size = max(10, int(h * 0.28))
        r_val = int((self.corner_r_pct / 100.0) * (h / 2))
        if self.style_idx == 0 and not self.is_snapped:
            r_val = h // 2

        bg = self.bg_color
        text_col = self.text_color
        border_css = "border: 2px solid #E0E0E0;"

        if self.is_snapped:
            radius_css = f"""
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: {r_val}px;
                border-bottom-left-radius: {r_val}px;
            """
            border_css = "border: 1px solid transparent;"
        else:
            radius_css = f"border-radius: {r_val}px;"

        if self.style_idx == 2:
            bg = "transparent"
            border_css = "border: none;"
            self.bar.hide()
            text_col = self.theme_color
        elif self.style_idx == 3:
            self.bar.hide()
            f_size = int(f_size * 1.3)
        elif self.style_idx == 4:
            bg = "rgba(255,255,255,0.7)" if self.bg_color != "#2D3436" else "rgba(0,0,0,0.6)"
            border_css = "border: 1px solid rgba(200,200,200,0.5);"

        self.container.setStyleSheet(f"""
            QFrame#ContainerFrame {{
                background-color: {bg};
                {border_css}
                {radius_css}
            }}
        """)

        self.time_lbl.setStyleSheet(f"color:{text_col}; font-size:{f_size}px; font-weight:bold; border: none;")
        
        # Style the task label to match text color but slightly faded
        # Use opacity in color or just inherit text_col
        self.lbl_task.setStyleSheet(f"color:{text_col}; font-size: 11px; font-weight: bold; text-transform: uppercase; border: none;")

        bar_h = max(2, int(h * 0.08))
        self.bar.setFixedHeight(bar_h)

        bar_r = min(int(r_val / 2), bar_h // 2)
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background:{self.bar_bg}; border-radius:{bar_r}px; }}
            QProgressBar::chunk {{ background:{self.theme_color}; border-radius:{bar_r}px; }}
        """)

        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        self.container.update()

    # ---------- SETTINGS ----------
    def update_config(self, style_idx, corner_r_pct, color_hex):
        self.style_idx = style_idx
        self.corner_r_pct = corner_r_pct
        self.theme_color = color_hex

        if color_hex == "#2D3436":
            self.bg_color = "#2D3436"
            self.text_color = "#FFFFFF"
            self.bar_bg = "#636E72"
        else:
            self.bg_color = "#FFFFFF"
            self.text_color = "#2D3436"
            self.bar_bg = "#DFE6E9"

        self.apply_style()

    def apply_settings(self, scale_percent, opacity_val):
        scale = scale_percent / 100
        self.resize(int(self.base_w * scale), int(self.base_h * scale))
        self.opacity_effect.setOpacity(opacity_val / 100)
        self.apply_style()

    # ---------- DRAG + SNAP ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if not self.dragging:
            return

        screen = QApplication.primaryScreen().availableGeometry()
        pos = e.globalPosition().toPoint() - self.offset

        SNAP = 20
        snapped = abs(pos.y() - screen.top()) < SNAP

        if snapped:
            pos.setY(screen.top())

        self.move(pos)

        if snapped != self.is_snapped:
            self.is_snapped = snapped
            self.apply_style()

    def mouseReleaseEvent(self, e):
        self.dragging = False
        self.settings.setValue("pos", self.pos())

    def resizeEvent(self, e):
        self.apply_style()
        super().resizeEvent(e)

# --- 6. OVERLAY WINDOW ---

class OverlayWindow(QWidget):
    """
    Dual-Mode Overlay: 
    1. Check-In (Ask user if done)
    2. Break Mode (Health tips + Timer)
    """
    # Custom signals to talk to MainWindow
    action_break = Signal()
    action_extend = Signal()
    action_cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack allows switching between "Check-In" and "Break" pages
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # --- PAGE 1: CHECK-IN ---
        self.page_checkin = QWidget()
        l_check = QVBoxLayout(self.page_checkin)
        l_check.setAlignment(Qt.AlignCenter)
        
        lbl_q = QLabel("DID YOU FINISH YOUR TASK?")
        lbl_q.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: 800; border: none; font-family: 'Segoe UI';")
        lbl_q.setAlignment(Qt.AlignCenter)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        
        # Yes Button
        btn_yes = QPushButton("YES, START BREAK")
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_yes.setFixedSize(220, 60)
        btn_yes.setStyleSheet("""
            QPushButton { background-color: #00B894; color: white; border-radius: 12px; font-weight: bold; font-size: 16px; border: none; }
            QPushButton:hover { background-color: #00A383; }
        """)
        btn_yes.clicked.connect(lambda: self.action_break.emit())
        
        # No Button
        btn_no = QPushButton("NO, +5 MINUTES")
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.setFixedSize(220, 60)
        btn_no.setStyleSheet("""
            QPushButton { background-color: #0984E3; color: white; border-radius: 12px; font-weight: bold; font-size: 16px; border: none; }
            QPushButton:hover { background-color: #74B9FF; }
        """)
        btn_no.clicked.connect(lambda: self.action_extend.emit())
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)
        btn_layout.addStretch()
        
        l_check.addWidget(lbl_q)
        l_check.addSpacing(50)
        l_check.addLayout(btn_layout)
        
        # --- PAGE 2: BREAK MODE ---
        self.page_break = QWidget()
        l_break = QVBoxLayout(self.page_break)
        l_break.setAlignment(Qt.AlignCenter)

        
        self.tips = [
            "Release your jaw.", "Look at something 20 feet away.",
            "Take a deep belly breath.", "Stretch your shoulders.",
            "Drink a glass of water.", "Relax your forehead."
        ]
        self.tip_timer = QTimer(self)
        self.tip_timer.timeout.connect(self.cycle_tip)
        
        retro_font = "font-family: 'Consolas', 'Courier New', monospace;"
        self.msg_label = QLabel("SCREEN REST")
        self.msg_label.setStyleSheet(f"color: #888888; font-size: 48px; font-weight: bold; background: transparent; border: none; {retro_font} letter-spacing: 2px;")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setFixedWidth(1000)
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet(f"color: #AAAAAA; font-size: 32px; font-weight: normal; margin-top: 30px; border: none; background: transparent; {retro_font}")
        self.timer_label.setAlignment(Qt.AlignCenter)
        
        self.progress = QProgressBar()
        self.progress.setFixedWidth(598)
        self.progress.setFixedHeight(20)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar { background-color: #111111; border: 2px solid #333333; border-radius: 0px; } 
            QProgressBar::chunk { background-color: #AAAAAA; width: 15px; margin: 2px; }
        """)
        
        l_break.addWidget(self.msg_label, 0, Qt.AlignCenter)
        l_break.addWidget(self.timer_label, 0, Qt.AlignCenter)
        l_break.addSpacing(60)
        l_break.addWidget(self.progress, 0, Qt.AlignCenter)
        
        # Add pages to stack
        self.stack.addWidget(self.page_checkin)
        self.stack.addWidget(self.page_break)

    def show_checkin(self):
        """ Show the dark screen with the Question """
        self.tip_timer.stop()
        self.stack.setCurrentIndex(0) # Page 0 is Check-in
        self.showFullScreen()

    def show_break_mode(self):
        """ Switch to the break timer view """
        self.stack.setCurrentIndex(1) # Page 1 is Break Timer
        self.cycle_tip()
        self.tip_timer.start(8000)

    def cycle_tip(self):
        import random
        tip = random.choice(self.tips)
        self.msg_label.setText(tip.upper())

    def update_state(self, current_sec, total_sec):
        mins, secs = divmod(current_sec, 60)
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
        if total_sec > 0:
            pct = int(((total_sec - current_sec) / total_sec) * 100)
            self.progress.setValue(pct)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Full Black Background
        painter.setBrush(QColor(0, 0, 0, 255))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
    def set_message(self, text):
        # Override for custom messages if needed
        self.msg_label.setText(text.upper())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F4 and (event.modifiers() & Qt.AltModifier):
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # When window closes (via Alt+F4), tell Main Window to stop
        self.action_cancelled.emit()
        event.accept()

# --- 7. SNAP SLIDER & GHOST CLOSE BUTTON (FINAL) ---

class SnapSlider(QWidget):
    """A slider that snaps to specific time steps: 5, 10, 15, 30, 45, 60"""
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.steps = [5, 10, 15, 30, 45, 60]
        self.current_idx = 3 # Default to 30 min (index 3)
        self.dragging = False
        self.setCursor(Qt.PointingHandCursor)

    def set_value(self, val):
        if val in self.steps: self.current_idx = self.steps.index(val)
        else: self.current_idx = min(range(len(self.steps)), key=lambda i: abs(self.steps[i]-val))
        self.update()

    def get_value(self): return self.steps[self.current_idx]

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.dragging = True; self.snap_to_x(e.position().x())
    def mouseMoveEvent(self, e):
        if self.dragging: self.snap_to_x(e.position().x())
    def mouseReleaseEvent(self, e): self.dragging = False

    def snap_to_x(self, x):
        width = self.width() - 20
        step_w = width / (len(self.steps) - 1)
        idx = int((x - 10 + (step_w/2)) / step_w)
        idx = max(0, min(idx, len(self.steps) - 1))
        if idx != self.current_idx:
            self.current_idx = idx; self.valueChanged.emit(self.steps[idx]); self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w = self.width() - 20; y = self.height() // 2; step_w = w / (len(self.steps) - 1)
        
        # Track
        p.setPen(QPen(QColor("#DFE6E9"), 4, Qt.SolidLine, Qt.RoundCap)); p.drawLine(10, y, self.width()-10, y)
        # Active
        active_x = 10 + (self.current_idx * step_w)
        p.setPen(QPen(QColor("#0984E3"), 4, Qt.SolidLine, Qt.RoundCap)); p.drawLine(10, y, int(active_x), y)
        
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for i, val in enumerate(self.steps):
            x = 10 + (i * step_w)
            if i == self.current_idx:
                p.setBrush(QColor("#0984E3")); p.setPen(QPen(QColor("#FFFFFF"), 2))
                p.drawEllipse(QPoint(int(x), y), 8, 8)
                p.setPen(QColor("#0984E3")); p.drawText(QRectF(x-15, y-25, 30, 20), Qt.AlignCenter, str(val))
            else:
                p.setBrush(QColor("#DFE6E9")); p.setPen(Qt.NoPen)
                p.drawEllipse(QPoint(int(x), y), 4, 4)
                p.setPen(QColor("#B2BEC3")); p.drawText(QRectF(x-15, y+10, 30, 20), Qt.AlignCenter, str(val))


class GhostCloseButton(QPushButton):
    """A close button (X) that dodges the mouse 12 times around the corners."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        # No stylesheet needed, we paint it manually for perfect control
        self.setCursor(Qt.PointingHandCursor)
        self.dodge_count = 0
        self.max_dodges = 12 
        self.corner_index = 0 

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Determine status
        is_catchable = self.dodge_count >= self.max_dodges
        is_hovered = self.underMouse()

        # --- COLORS ---
        if is_hovered and is_catchable:
            bg_color = QColor("#FF5252") # Nice Red
            icon_color = QColor("#FFFFFF") # White
        else:
            bg_color = Qt.transparent
            icon_color = QColor("#636E72") # Dark Grey

        # 1. Draw Background (Rounded Square)
        if bg_color != Qt.transparent:
            p.setBrush(bg_color)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(self.rect(), 6, 6)

        # 2. Draw "X" Icon (Centered & Clean)
        pen = QPen(icon_color, 2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        
        # Math to center a 10px cross
        center = self.rect().center()
        half_size = 5 
        
        # Line 1 (\)
        p.drawLine(center.x() - half_size, center.y() - half_size, 
                   center.x() + half_size, center.y() + half_size)
        # Line 2 (/)
        p.drawLine(center.x() - half_size, center.y() + half_size, 
                   center.x() + half_size, center.y() - half_size)

    def enterEvent(self, event):
        # Trigger jump if not caught yet
        if self.dodge_count < self.max_dodges:
            self.dodge_count += 1
            self.jump_to_next_corner()
        super().enterEvent(event)
        self.update() # Force repaint

    def leaveEvent(self, event): 
        super().leaveEvent(event)
        self.update()

    def jump_to_next_corner(self):
        parent = self.parentWidget()
        if not parent: return

        m = 10 # Margin from window edge
        w, h = self.width(), self.height()
        pw, ph = parent.width(), parent.height()

        # Define corners in order: [TR, TL, BL, BR]
        corners = [
            QPoint(pw - w - m, m),         # 0: TR
            QPoint(m, m),                  # 1: TL
            QPoint(m, ph - h - m),         # 2: BL
            QPoint(pw - w - m, ph - h - m) # 3: BR
        ]

        # Cycle to next corner
        self.corner_index = (self.corner_index + 1) % 4
        target_pos = corners[self.corner_index]

        # Smooth slide animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(200) 
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(target_pos)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start()


class QuickStartDialog(QDialog):
    """Popup: Cannot be closed via Esc or Alt+F4."""
    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(420, 240)
        
        self.result_action = None
        self.dragging = False
        self.allowed_to_close = False # <--- LOCKDOWN FLAG

        self.settings = QSettings("Ikiflow", "QuickStart")
        self.last_focus = int(self.settings.value("last_focus", 30))
        self.last_break = int(self.settings.value("last_break", 5))

        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10)

        # --- CARD UI ---
        self.card = QFrame()
        self.card.setStyleSheet("background: #FFFFFF; border-radius: 15px;")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(20); shadow.setYOffset(5); shadow.setColor(QColor(0,0,0,40))
        self.card.setGraphicsEffect(shadow)
        layout.addWidget(self.card)

        inner = QVBoxLayout(self.card); inner.setContentsMargins(20, 30, 20, 20); inner.setSpacing(15)

        # 1. Title
        lbl = QLabel(f"Focusing on {app_name}?")
        lbl.setStyleSheet("color: #2D3436; font-size: 16px; font-weight: 800;")
        lbl.setAlignment(Qt.AlignCenter); inner.addWidget(lbl)

        # 2. Controls Row
        control_row = QHBoxLayout()
        self.slider = SnapSlider()
        self.slider.set_value(self.last_focus); self.slider.valueChanged.connect(self.update_btn_text)
        
        self.btn_break = QPushButton(f"{self.last_break}m Break")
        self.btn_break.setFixedSize(80, 40); self.btn_break.setCursor(Qt.PointingHandCursor)
        self.btn_break.setStyleSheet("""
            QPushButton { background: #F1F2F6; color: #636E72; border: 1px solid #DFE6E9; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background: #E0E0E0; color: #2D3436; }
        """)
        self.btn_break.clicked.connect(self.cycle_break)
        control_row.addWidget(self.slider, 1); control_row.addSpacing(10); control_row.addWidget(self.btn_break)
        inner.addLayout(control_row)

        # 3. Start Button
        self.btn_start = QPushButton("Start Focus"); self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(45)
        self.btn_start.setStyleSheet("""
            QPushButton { background: #0984E3; color: white; border-radius: 10px; font-weight: bold; font-size: 14px; border: none; }
            QPushButton:hover { background: #74B9FF; }
        """)
        self.btn_start.clicked.connect(self.accept_start); self.btn_start.setDefault(True)
        inner.addWidget(self.btn_start)
        self.update_btn_text(self.slider.get_value())

        # --- GHOST CLOSE BUTTON ---
        self.ghost_btn = GhostCloseButton(self)
        m = 10
        self.ghost_btn.move(self.width() - self.ghost_btn.width() - m, m)
        self.ghost_btn.clicked.connect(lambda: self.finish("skip"))

    def update_btn_text(self, val): self.btn_start.setText(f"Start {val}m Focus")
    def cycle_break(self):
        opts = [5, 10, 15, 20, 30]
        try: idx = opts.index(int(self.btn_break.text().split("m")[0])); new_val = opts[(idx + 1) % len(opts)]
        except: new_val = 5
        self.btn_break.setText(f"{new_val}m Break"); self.last_break = new_val
        
    def accept_start(self):
        self.settings.setValue("last_focus", self.slider.get_value()); self.settings.setValue("last_break", self.last_break)
        self.finish("start")

    def finish(self, action):
        self.result_action = action
        self.allowed_to_close = True # <--- Unlock closing
        self.accept()

    # --- SECURITY OVERRIDES ---
    
    def keyPressEvent(self, event):
        # BLOCK ESCAPE KEY
        if event.key() == Qt.Key_Escape:
            event.ignore() 
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # BLOCK ALT+F4 (System Close)
        if not self.allowed_to_close:
            event.ignore()
        else:
            super().closeEvent(event)

    # Drag Logic
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.dragging = True; self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self.dragging: self.move(e.globalPosition().toPoint() - self.drag_pos)
    def mouseReleaseEvent(self, e): self.dragging = False