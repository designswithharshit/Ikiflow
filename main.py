import sys
import os
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QFrame, 
                               QGraphicsDropShadowEffect, QStackedWidget, 
                               QSystemTrayIcon, QMenu, QFileDialog, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt, QTimer, QUrl, QPoint
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices, QColor, QPainter, QAction, QPen
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

# --- YOUR CUSTOM MODULES ---
from Ikiflow_utils import resource_path
from Ikiflow_style import STYLESHEET
from Ikiflow_audio import SoundEngine
from Ikiflow_components import (ModernWindowButton, CircularTimeInput, 
                                CustomLinearInput, FloatingWidget, OverlayWindow)
from Ikiflow_settings import SettingsTab
from Ikiflow_feedback import FeedbackDialog
from Ikiflow_data import HistoryManager, get_active_window_title
from Ikiflow_analyzer import AnalyzerWindow

# --- 5. MAIN WINDOW ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_version = "2.3.2"
        self.setWindowTitle("Ikiflow")
        try:
            self.setWindowIcon(QIcon(resource_path("IkiflowIcon.ico")))
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")
        # Temporarily remove frameless hint to test
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
        
        # --- NEW CONNECTIONS ---
        # Moved to after setup_tray
        
        self.floater = FloatingWidget()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.history_manager = HistoryManager()

        # --- NEW: App Tracking Setup ---
        self.session_app_data = {}  # Stores {"App Name": seconds_used}
        self.tracker_timer = QTimer()
        # self.tracker_timer.timeout.connect(self.track_current_app)
        # -------------------------------

        self.session_start_time = None
        self.detected_app = "None"

        # --- NEW: Init Sound Engine ---
        self.sound_engine = SoundEngine()
        try:
            self.sound_engine.load_sound("noise.wav") # Make sure you have this file!
            print("Sound loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load sound file: {e}")
        self.is_ambient_on = False
        
        # Inside MainWindow __init__
        self.overlay = OverlayWindow()
        
        # Setup UI and Tray
        self.init_ui()
        self.setup_tray()
        
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
        self.settings_tab = SettingsTab()
        
        # ... (Connect your settings signals here as before) ...
        self.settings_tab.widget_style_updated.connect(self.floater.update_config)
        self.settings_tab.widget_props_updated.connect(self.floater.apply_settings)
        self.settings_tab.preview_toggled.connect(self.toggle_preview)
        self.settings_tab.overlay_text_updated.connect(self.overlay.set_message)
        self.settings_tab.feedback_clicked.connect(self.open_feedback_dialog)
        
        # ONLY TWO TABS NOW (Distraction Free)
        self.tabs.addTab(self.create_timer_tab(), "Timer")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # --- ACTION BUTTONS ---
        action_layout = QHBoxLayout()
        
        # 1. Analyzer Button (Small Notebook Icon)
        btn_analyze = QPushButton("📊") # Or use an icon
        btn_analyze.setFixedSize(50, 50)
        btn_analyze.setToolTip("Open Reflection Journal")
        btn_analyze.setCursor(Qt.PointingHandCursor)
        btn_analyze.setStyleSheet("""
            QPushButton { background: #F1F2F6; border-radius: 12px; font-size: 20px; border: none; }
            QPushButton:hover { background: #DFE6E9; }
        """)
        btn_analyze.clicked.connect(self.open_analyzer)
        
        # 2. Start Button (Big)
        self.btn_start = QPushButton("Start Focus Session")
        self.btn_start.setObjectName("ActionBtn")
        self.btn_start.clicked.connect(self.start_timer)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        
        action_layout.addWidget(btn_analyze)
        action_layout.addSpacing(10)
        action_layout.addWidget(self.btn_start, 1) # 1 = Stretch

        layout.addWidget(self.tabs)
        layout.addLayout(action_layout) # Add the layout, not just the button
        return page

    def open_analyzer(self):
        # Create it if it doesn't exist, or just show it
        if not hasattr(self, 'analyzer_window') or self.analyzer_window is None:
            self.analyzer_window = AnalyzerWindow()
        
        self.analyzer_window.show()
        self.analyzer_window.activateWindow()

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

    # --- Tracking Function ---

    def track_current_app(self):
        # 1. Get Title
        title = get_active_window_title()
        
        # 2. Smart Renaming (Improved)
        app_name = title
        
        # A. Priority: Check for known creative apps (The "Adobe" Fix)
        # These apps often put the filename first, e.g. "Project.ai @ 50%... - Adobe Illustrator"
        keywords = {
            "Illustrator": "Adobe Illustrator",
            "Photoshop": "Adobe Photoshop",
            "Indesign": "Adobe InDesign",
            "Premiere": "Adobe Premiere",
            "After Effects": "Adobe After Effects",
            "Canva": "Canva",
            "Figma": "Figma",
            "Notion": "Notion",
            "Code": "Visual Studio Code",
            "Chrome": "Google Chrome",
            "Edge": "Microsoft Edge",
            "Firefox": "Firefox",
            "Ikiflow": "Focus Timer"
        }
        
        found_keyword = False
        for key, clean_name in keywords.items():
            if key in title:
                app_name = clean_name
                found_keyword = True
                break
        
        # B. Fallback: Clean mess if no keyword found
        if not found_keyword:
            if " - " in title:
                app_name = title.split(" - ")[-1] # Take the end part
            elif " | " in title:
                app_name = title.split(" | ")[-1]

        # 3. Add exactly 1 second
        if app_name in self.session_app_data:
            self.session_app_data[app_name] += 1
        else:
            self.session_app_data[app_name] = 1
        
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

        # --- NEW: Start Tracking ---
        self.session_app_data = {}  # Reset data
        # self.tracker_timer.start(5000) # Check every 5 seconds
        # ---------------------------

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
        # --- FIX: SAVE SESSION NOW ---
        # Now we know the user is truly done, including any extensions.
        planned_mins = self.input_focus.value() # Initial goal
        
        # Calculate actual time based on total accumulated time
        elapsed_seconds = self.total_time  # Since time_left is 0, total_time is what we did
        actual_mins = elapsed_seconds // 60
        
        # Capture final app usage state
        self.track_current_app()
        
        self.history_manager.save_session(
            duration_planned=planned_mins,
            duration_actual=actual_mins,
            break_duration=self.input_break.value(),
            status="Completed",
            app_data=self.session_app_data
        )
        # -----------------------------

        self.is_break = True
        self.sound_engine.stop()
        self.btn_ambient.setChecked(False)
        self.btn_ambient.setText("Turn On Noise")

        mins = self.input_break.value()
        self.total_time = mins * 60
        self.time_left = self.total_time

        self.lbl_status.setText("Break Time")
        self.lbl_status.setStyleSheet("color: #00B894; font-size: 18px; font-weight: bold; background: transparent; border: none;")

        # Switch overlay to timer mode
        self.overlay.show_break_mode()
        self.timer.start(1000)

    def stop_timer(self):

        # --- NEW: Stop Tracking ---
        # self.tracker_timer.stop()

        if self.is_running and not self.is_break:
            elapsed_seconds = self.total_time - self.time_left
            actual_mins = elapsed_seconds // 60
            planned_mins = self.total_time // 60

            if actual_mins >= 1:
                self.history_manager.save_session(
                    duration_planned=planned_mins,
                    duration_actual=actual_mins,
                    break_duration=self.input_break.value(),
                    status="Skipped",
                    app_data=self.session_app_data  # <--- PASS DATA HERE
                )
    # ---------------------------

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
            release_url = f"https://github.com/designswithharshit/Ikiflow/releases/download/v{new_ver}/Ikiflow.exe"
            QDesktopServices.openUrl(QUrl(release_url))

    def tick(self):
        self.time_left -= 1
        self.update_display()

        # 2. THE FIX: Record exactly 1 second of data right now
        if not self.is_break and self.time_left > 0:
            self.track_current_app()

        if self.is_break:
            # Break Logic
            self.overlay.update_state(self.time_left, self.total_time)
            
            # FIX 2: Auto-End Break -> Start Focus (Loop)
            if self.time_left <= 0:
                self.is_break = False
                self.overlay.hide()
                
                # Reset Focus Timer
                mins = self.input_focus.value()
                self.total_time = mins * 60
                self.time_left = self.total_time
                
                # Update Status
                self.lbl_status.setText("Focus Mode Active")
                self.lbl_status.setStyleSheet("color: #636E72; font-size: 16px; font-weight: 600; background: transparent; border: none;")
                
                # Show Floater
                self.floater.show()
                
                # Restart Sound if "Noise On" was active
                if self.btn_ambient.isChecked():
                     self.sound_engine.play()

        else:
            # Focus Logic
            pct = 0
            if self.total_time > 0: 
                pct = int(((self.total_time - self.time_left) / self.total_time) * 100)
            
            self.floater.time_lbl.setText(self.format_time(self.time_left))
            self.floater.bar.setValue(100 - pct)
            
            # End of Focus -> Show Check-In
            if self.time_left <= 0:
                self.timer.stop()
                
                # --- FIX: DO NOT SAVE HERE ---
                # We just show the check-in. We wait for the user to 
                # click "Start Break" or "Stop" before saving.
                # -----------------------------
                
                self.floater.hide()
                self.overlay.show_checkin()
                self.sound_engine.stop()
                
                # Bring window to front so they see the check-in
                self.setWindowState(Qt.WindowNoState)
                self.show()
                self.raise_()
                self.activateWindow()

    def extend_session(self, minutes):
        self.overlay.hide()
        self.is_break = False

        # Add time
        self.time_left += (minutes * 60)
        self.total_time += (minutes * 60)

        # FIX 1: Force show normal before starting to ensure it's not minimized
        self.floater.setWindowState(Qt.WindowNoState)
        self.floater.show()
        self.floater.raise_()
        self.floater.activateWindow()

        self.timer.start(1000)
        self.floater.show()

    def update_display(self):
        self.lbl_big_timer.setText(self.format_time(self.time_left))

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

def check_single_instance():
    """Check if another instance is already running and handle it appropriately."""
    socket = QLocalSocket()
    socket.connectToServer("Ikiflow_SingleInstance")
    
    if socket.waitForConnected(500):  # Wait 500ms for connection
        # Another instance is running, bring it to front
        socket.write(b"SHOW_WINDOW")
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return False  # Don't start a new instance
    
    # No other instance running, start the server
    server = QLocalServer()
    server.listen("Ikiflow_SingleInstance")
    return True, server

if __name__ == "__main__":
    # Check for single instance
    result = check_single_instance()
    if not result:
        sys.exit(0)  # Another instance is already running
    
    is_single_instance, local_server = result
    
    app = QApplication(sys.argv)
    
    # --- IMPORTANT: This allows QSettings to work globally ---
    app.setOrganizationName("DesignWithHarshit")
    app.setApplicationName("Ikiflow")
    # ---------------------------------------------------------
    
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLESHEET)
    
    window = None
    
    # Create and show main window
    def show_main_window():
        global window
        window = MainWindow()
        window.show()
        window.raise_()
        window.activateWindow()
    
    show_main_window()
    
    # Connect to the local server to handle show window requests
    def handle_new_connection():
        socket = local_server.nextPendingConnection()
        if socket:
            socket.readyRead.connect(lambda: handle_show_request(socket))
    
    def handle_show_request(socket):
        data = socket.readAll().data().decode()
        if data == "SHOW_WINDOW" and window is not None:
            window.show()
            window.raise_()
            window.activateWindow()
        socket.disconnectFromServer()
    
    local_server.newConnection.connect(handle_new_connection)
    
    sys.exit(app.exec())