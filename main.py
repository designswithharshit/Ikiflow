import sys
import math
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QSpinBox, 
                               QFrame, QGraphicsOpacityEffect, QProgressBar, 
                               QTabWidget, QGraphicsDropShadowEffect,
                               QStackedWidget, QSystemTrayIcon, QMenu, QDialog, QFileDialog)
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF, QSize, QUrl, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QAction, QIcon, QPixmap
from PySide6.QtMultimedia import QSoundEffect # For simple sound playback
# Add QDesktopServices to QtGui imports
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QAction, QIcon, QPixmap, QDesktopServices

# Add these NEW imports for networking
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import QMessageBox # Add QMessageBox to widgets list

# IMPORT THE SETTINGS FILE
from Ikiflow_feedback import FeedbackDialog
from Ikiflow_settings import SettingsTab

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # FIX: Use the directory of the script file, not the current working directory
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

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

# --- 2. CUSTOM WIDGETS ---

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
    def mouseReleaseEvent(self, e): self.dragging = False

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

# --- 3. FLOATING WIDGET ---

class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Base size
        self.base_w, self.base_h = 240, 80
        self.resize(self.base_w, self.base_h)

        # Drag / snap state
        self.dragging = False
        self.offset = QPoint()
        self.is_snapped = False

        # Style defaults (used by settings)
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
        inner.setContentsMargins(20, 10, 20, 10)

        self.time_lbl = QLabel("Ready")
        self.time_lbl.setAlignment(Qt.AlignCenter)

        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)

        inner.addWidget(self.time_lbl)
        inner.addWidget(self.bar)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.apply_style()

    # ---------- STYLE ----------
    def apply_style(self):

        self.container.show()
        self.bar.show()
        self.time_lbl.show()

        h = max(1, self.height())

        m_y = max(2, int(h * 0.1))
        m_x = max(5, int(self.width() * 0.08))
        if self.container_layout.contentsMargins().top() != m_y:
            self.container_layout.setContentsMargins(m_x, m_y, m_x, m_y)

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

        self.time_lbl.setStyleSheet(
            f"color:{text_col}; font-size:{f_size}px; font-weight:bold;"
        )

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

    def resizeEvent(self, e):
        self.apply_style()
        super().resizeEvent(e)

# --- 4. OVERLAY WINDOW (Dual Mode) ---

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
        btn_yes.clicked.connect(self.action_break.emit)
        
        # No Button
        btn_no = QPushButton("NO, +5 MINUTES")
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.setFixedSize(220, 60)
        btn_no.setStyleSheet("""
            QPushButton { background-color: #0984E3; color: white; border-radius: 12px; font-weight: bold; font-size: 16px; border: none; }
            QPushButton:hover { background-color: #74B9FF; }
        """)
        btn_no.clicked.connect(self.action_extend.emit)
        
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


# --- Sound Engine ---

class SoundEngine:
    def __init__(self):
        self.effect = QSoundEffect()
        self.effect.setLoopCount(-2) # Infinite loop
        self.effect.setVolume(0.5)

    def load_sound(self, file_path):
        # Determine if it's a local user file or an internal resource
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
        else:
            # Fallback for internal resource (noise.wav)
            url = QUrl.fromLocalFile(resource_path(file_path))
            
        self.effect.setSource(url)

    def play(self):
        self.effect.play()

    def stop(self):
        self.effect.stop()
    def __init__(self):
        self.effect = QSoundEffect()
        # FIX: Use -2 directly instead of QSoundEffect.Infinite
        self.effect.setLoopCount(-2) 
        self.effect.setVolume(0.5) # 50% volume

    def load_sound(self, filename):
        path = resource_path(filename)
        self.effect.setSource(QUrl.fromLocalFile(path))

    def play(self):
        self.effect.play()

    def stop(self):
        self.effect.stop()
        
# --- 5. MAIN WINDOW ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_version = "2.0.2"
        self.setWindowTitle("Ikiflow")
        self.setWindowIcon(QIcon(resource_path("IkiflowIcon.ico")))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 550)
        
        self.dragging = False
        self.offset = QPoint()
        
        self.is_running = False
        self.is_paused = False
        self.total_time = 0
        self.time_left = 0
        self.is_break = False
        
        self.overlay = OverlayWindow()
        
        # --- NEW CONNECTIONS ---
        self.overlay.action_break.connect(self.start_actual_break)
        self.overlay.action_extend.connect(lambda: self.extend_session(5))
        # -----------------------

        self.floater = FloatingWidget()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        # --- NEW: Init Sound Engine ---
        self.sound_engine = SoundEngine()
        self.sound_engine.load_sound("noise.wav") # Make sure you have this file!
        self.is_ambient_on = False
        
        # Setup UI and Tray
        self.init_ui()
        self.setup_tray()

        # Inside MainWindow __init__
        self.overlay = OverlayWindow()
        
        self.overlay.action_break.connect(self.start_actual_break)
        self.overlay.action_extend.connect(lambda: self.extend_session(5))
        
        # --- ADD THIS CONNECTION ---
        self.overlay.action_cancelled.connect(self.stop_timer)
        # ---------------------------

        QTimer.singleShot(2000, self.check_for_updates)

    # ---------- New Function ----------

    def browse_noise_file(self):
        # Open File Dialog (WAV only for now to ensure compatibility)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Noise", "", "Audio Files (*.wav)")
        
        if file_path:
            # 1. Stop current sound if playing
            was_playing = self.btn_ambient.isChecked()
            self.sound_engine.stop()
            
            # 2. Load new sound
            self.sound_engine.load_sound(file_path)
            
            # 3. Resume if it was already on
            if was_playing:
                self.sound_engine.play()

    def init_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(10, 10, 10, 10) 

        self.card = QFrame()
        self.card.setObjectName("MainCard")
        self.card.setStyleSheet("QFrame#MainCard { background-color: #FFFFFF; border-radius: 20px; border: 1px solid #E0E0E0; }")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 15, 20, 25)
        card_layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Ikiflow")
        title.setObjectName("Title")
        
        # Use custom ModernWindowButton
        btn_min = ModernWindowButton("min")
        btn_min.clicked.connect(self.hide_to_tray)
        
        btn_close = ModernWindowButton("close")
        btn_close.clicked.connect(self.hide_to_tray)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_min)
        header_layout.addSpacing(5)
        header_layout.addWidget(btn_close)
        card_layout.addLayout(header_layout)
        
        # Stacked View
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_setup_page())
        self.stack.addWidget(self.create_active_page())
        
        card_layout.addWidget(self.stack)
        root_layout.addWidget(self.card)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("IkiflowIcon.ico")))
        
        tray_menu = QMenu()
        action_show = QAction("Show / Hide", self)
        action_show.triggered.connect(self.toggle_window)
        tray_menu.addAction(action_show)
        tray_menu.addSeparator()
        self.action_pause = QAction("Pause Timer", self)
        self.action_pause.triggered.connect(self.toggle_pause)
        self.action_pause.setEnabled(False)
        tray_menu.addAction(self.action_pause)
        action_quit = QAction("Quit Application", self)
        action_quit.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        self.tray_icon.show()

    def generate_tray_icon(self, color_hex):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        return QIcon(pixmap)

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def hide_to_tray(self):
        self.hide()
        self.tray_icon.showMessage("Ikiflow", "Running in background.", QSystemTrayIcon.Information, 2000)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, event):
        if self.dragging: self.move(event.globalPosition().toPoint() - self.offset)
    def mouseReleaseEvent(self, event): self.dragging = False

    def open_feedback_dialog(self):
        dlg = FeedbackDialog(self)
        dlg.exec()

    def create_setup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_timer_tab(), "Timer")
        
        # --- NEW SETTINGS TAB INSTANCE ---
        self.settings_tab = SettingsTab()
        self.settings_tab.widget_style_updated.connect(self.floater.update_config)
        self.settings_tab.widget_props_updated.connect(self.floater.apply_settings)
        self.settings_tab.preview_toggled.connect(self.toggle_preview)
        self.settings_tab.overlay_text_updated.connect(self.overlay.set_message)
        self.settings_tab.feedback_clicked.connect(self.open_feedback_dialog)
        
        self.tabs.addTab(self.settings_tab, "Settings")
        
        self.btn_start = QPushButton("Start Focus Session")
        self.btn_start.setObjectName("ActionBtn")
        self.btn_start.clicked.connect(self.start_timer)
        self.btn_start.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.tabs)
        layout.addWidget(self.btn_start)
        return page

    def create_active_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 40, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_status = QLabel("Focus Mode Active")
        self.lbl_status.setObjectName("StatusLabel")
        self.lbl_status.setAlignment(Qt.AlignCenter)

        self.lbl_big_timer = QLabel("00:00")
        self.lbl_big_timer.setObjectName("BigTimer")
        self.lbl_big_timer.setAlignment(Qt.AlignCenter)
        
        # --- NEW: Noise Controls Layout ---
        noise_layout = QHBoxLayout()
        noise_layout.setAlignment(Qt.AlignCenter)
        
        # 1. The Toggle Button
        self.btn_ambient = QPushButton("Turn On Noise")
        self.btn_ambient.setCursor(Qt.PointingHandCursor)
        self.btn_ambient.setCheckable(True)
        self.btn_ambient.setFixedWidth(140)
        self.btn_ambient.setStyleSheet("""
            QPushButton { color: #636E72; background: transparent; border: 1px solid #DFE6E9; border-radius: 15px; padding: 5px; font-weight: bold; }
            QPushButton:checked { background-color: #E17055; color: white; border: none; }
        """)
        self.btn_ambient.clicked.connect(self.toggle_ambient)
        
        # 2. The Browse Button [...]
        self.btn_browse = QPushButton("...")
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.setFixedSize(30, 30)
        self.btn_browse.setToolTip("Select custom .wav file")
        self.btn_browse.setStyleSheet("""
            QPushButton { color: #636E72; background: transparent; border: 1px solid #DFE6E9; border-radius: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #DFE6E9; }
        """)
        self.btn_browse.clicked.connect(self.browse_noise_file)
        
        noise_layout.addWidget(self.btn_ambient)
        noise_layout.addSpacing(5)
        noise_layout.addWidget(self.btn_browse)
        # ----------------------------------
        
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("PauseBtn")
        self.btn_pause.setCursor(Qt.PointingHandCursor)
        self.btn_pause.clicked.connect(self.toggle_pause)

        self.btn_stop = QPushButton("Stop Session")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_timer)

        layout.addStretch()
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_big_timer)
        layout.addSpacing(10)
        
        # Add the new horizontal layout here
        layout.addLayout(noise_layout)
        
        layout.addStretch()
        layout.addWidget(self.btn_pause)
        layout.addSpacing(10)
        layout.addWidget(self.btn_stop)
        return page

    def create_timer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_f = QLabel("Focus Duration")
        lbl_f.setObjectName("LabelBold")
        lbl_f.setAlignment(Qt.AlignCenter)
        h_layout_circle = QHBoxLayout()
        h_layout_circle.addStretch()
        self.input_focus = CircularTimeInput(presets=[5, 10, 15, 20, 25, 30, 45, 60, 90, 120], default_idx=5)
        h_layout_circle.addWidget(self.input_focus)
        h_layout_circle.addStretch()

        lbl_b = QLabel("Break Duration (minutes)")
        lbl_b.setObjectName("LabelBold")
        self.input_break = CustomLinearInput([1, 2, 3, 5, 10, 15, 20, 25, 30], default_idx=3)

        layout.addWidget(lbl_f)
        layout.addLayout(h_layout_circle)
        layout.addSpacing(15)
        layout.addWidget(lbl_b)
        layout.addWidget(self.input_break)
        layout.addStretch()
        return tab

    def toggle_preview(self):
        if self.floater.isVisible(): self.floater.hide()
        else:
            self.floater.show()
            self.settings_tab.emit_design_update() # Sync current design

    # --- Toggle_ambient ---

    def toggle_ambient(self):
        if self.btn_ambient.isChecked():
            self.btn_ambient.setText("Noise On")
            self.sound_engine.play()
        else:
            self.btn_ambient.setText("Turn On Noise")
            self.sound_engine.stop()

    def start_timer(self):
        if self.is_running: return
        self.is_running = True
        self.is_paused = False
        self.is_break = False
        
        mins = self.input_focus.value()
        self.total_time = mins * 60
        self.time_left = self.total_time
        
        self.stack.setCurrentIndex(1)
        self.lbl_status.setText("Focus Mode Active")
        self.lbl_status.setStyleSheet("color: #636E72; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        self.btn_pause.setText("Pause")
        self.action_pause.setEnabled(True)
        
        self.floater.show()
        self.settings_tab.emit_design_update()
        self.settings_tab.emit_props_update()
        self.timer.start(1000)
        self.update_display()

    def toggle_pause(self):
        if not self.is_running: return
        
        if self.is_paused:
            self.is_paused = False
            self.timer.start(1000)
            self.btn_pause.setText("Pause")
            self.action_pause.setText("Pause Timer")
            self.lbl_status.setText("Focus Mode Active")
        else:
            self.is_paused = True
            self.timer.stop()
            self.btn_pause.setText("Resume")
            self.action_pause.setText("Resume Timer")
            self.lbl_status.setText("Session Paused")

    def start_actual_break(self):
        self.is_break = True
        mins = self.input_break.value()
        self.total_time = mins * 60
        self.time_left = self.total_time

        self.lbl_status.setText("Break Time")
        self.lbl_status.setStyleSheet("color: #00B894; font-size: 18px; font-weight: bold; background: transparent; border: none;")

        # Switch overlay to timer mode
        self.overlay.show_break_mode()
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()
        self.is_running = False
        self.is_paused = False
        self.is_break = False
        
        self.floater.hide()
        self.overlay.hide()
        self.stack.setCurrentIndex(0)
        self.action_pause.setEnabled(False)
        self.action_pause.setText("Pause Timer")

    # ---------- New Functions ----------

    def check_for_updates(self):
        print("Checking for updates...")
        self.nam = QNetworkAccessManager(self)
        self.nam.finished.connect(self.handle_update_response)
        
        # PASTE YOUR RAW GITHUB URL HERE
        url_str = "https://raw.githubusercontent.com/designswithharshit/Ikiflow/refs/heads/main/Version.txt"
        self.nam.get(QNetworkRequest(QUrl(url_str)))

    def handle_update_response(self, reply):
        if reply.error() == QNetworkReply.NoError:
            # Get version from GitHub
            remote_version = reply.readAll().data().decode('utf-8').strip()
            
            # Compare strings (Simple check: is it different?)
            if remote_version != self.current_version:
                self.show_update_dialog(remote_version)
        
        reply.deleteLater()

    def show_update_dialog(self, new_ver):
        # Create a modern dark-theme message box
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setText(f"<b>A new version ({new_ver}) is available!</b>")
        msg.setInformativeText("Would you like to download it now?")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        # Style the popup to match your app
        msg.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #2D3436; font-size: 14px; }
            QPushButton { 
                background-color: #0984E3; color: white; 
                padding: 5px 15px; border-radius: 5px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #74B9FF; }
        """)
        
        if msg.exec() == QMessageBox.Yes:
            # Open your GitHub Releases page
            release_url = "https://raw.githubusercontent.com/designswithharshit/Ikiflow/releases/latest"
            QDesktopServices.openUrl(QUrl(release_url))

    def tick(self):
        self.time_left -= 1
        self.update_display()

        if self.is_break:
            # Break Logic
            self.overlay.update_state(self.time_left, self.total_time)
            if self.time_left <= 0: self.stop_timer()
        else:
            # Focus Logic
            pct = 0
            if self.total_time > 0: pct = int(((self.total_time - self.time_left) / self.total_time) * 100)
            self.floater.time_lbl.setText(self.format_time(self.time_left))
            self.floater.bar.setValue(100 - pct)
            
            # --- LOOP LOGIC: Show Check-In Overlay ---
            if self.time_left <= 0: 
                self.timer.stop() 
                self.floater.hide()
                self.overlay.show_checkin()

    def extend_session(self, minutes):
        self.overlay.hide()
        self.is_break = False

        # Add time
        self.time_left += (minutes * 60)
        self.total_time += (minutes * 60)

        self.timer.start(1000)
        self.floater.show()

    def update_display(self):
        self.lbl_big_timer.setText(self.format_time(self.time_left))

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())