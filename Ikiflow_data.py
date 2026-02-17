import json
import os
import ctypes
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

# --- PART 1: WINDOW DETECTOR ---
def get_active_window_title():
    """Returns the title of the currently active window."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        return title if title else "Unknown"
    except Exception:
        return "Unknown"

# --- PART 2: HISTORY MANAGER ---
class HistoryManager:
    def __init__(self):
        # --- THE NUCLEAR OPTION: USER PROFILE FOLDER ---
        # Path: C:\Users\YOUR_NAME\Ikiflow_Data\history.json
        self.app_data_dir = Path(os.environ['USERPROFILE']) / "Ikiflow_Data"
        
        # Create folder
        try:
            self.app_data_dir.mkdir(parents=True, exist_ok=True)
            self.filename = self.app_data_dir / "history.json"
            self.ensure_file_exists()
        except Exception as e:
            self.show_error(f"Init Error: {e}")

    # --- MISSING FUNCTIONS ADDED BELOW ---
    def show_error(self, msg):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Data Error")
        error_box.setText(str(msg))
        error_box.exec()

    def show_success(self, path):
        # You can comment this out later if you want silent saving
        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setText(f"Session Saved Successfully!\nLocation: {path}")
        msg.exec()
    # -------------------------------------

    def ensure_file_exists(self):
        if not self.filename.exists():
            try:
                with open(self.filename, "w") as f:
                    json.dump([], f)
            except Exception as e:
                self.show_error(f"Could not create file: {e}")

    def save_session(self, duration_planned, duration_actual, break_duration, status, app_data):
        # 1. Load existing
        history = []
        if self.filename.exists():
            try:
                with open(self.filename, "r") as f:
                    history = json.load(f)
                    if not isinstance(history, list): history = []
            except:
                history = []

        # 2. Add New Entry
        new_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "focus_planned": duration_planned,
            "focus_actual": duration_actual,
            "break_selected": break_duration,
            "status": status,
            "app_usage": app_data
        }
        
        history.append(new_entry)
        
        # 3. Save Back
        try:
            with open(self.filename, "w") as f:
                json.dump(history, f, indent=4)
            
            # --- POPUP CONFIRMATION ---
            # Once you see this working, add a # before the next line to silence it.
            self.show_success(self.filename) 
            
        except Exception as e:
            self.show_error(f"Save Failed: {e}")