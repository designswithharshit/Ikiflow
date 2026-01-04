import json
import os
import datetime
import ctypes

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
    def __init__(self, filename="history.json"):
        self.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        self.ensure_file_exists()

    def ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def save_session(self, duration_planned, duration_actual, break_duration, status, app_data):
        """
        :param app_data: A dictionary e.g., {"VS Code": 1200, "Chrome": 300} (seconds)
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "focus_planned": duration_planned,
            "focus_actual": duration_actual,
            "break_selected": break_duration,
            "status": status,
            "app_usage": app_data  # SAVES THE FULL REPORT
        }

        try:
            with open(self.filepath, 'r') as f:
                history = json.load(f)
        except:
            history = []

        history.append(entry)

        with open(self.filepath, 'w') as f:
            json.dump(history, f, indent=4)
            
        print(f"Saved: {status} | Apps: {len(app_data)} detected")