import json
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QRectF, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QBrush

# --- HELPER: DATA PROCESSOR ---
class AnalyticsEngine:
    def __init__(self):
        self.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

    def load_data(self):
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            return data
        except:
            return []

    def get_stats(self):
        data = self.load_data()
        if not data:
            return {"total_hours": 0, "streak": 0, "daily_avg": 0, "daily_map": {}}

        # 1. Map Date -> Minutes
        daily_map = {} # "2025-07-23": 45
        total_mins = 0
        
        for entry in data:
            date = entry.get("date")
            mins = entry.get("focus_actual", 0)
            daily_map[date] = daily_map.get(date, 0) + mins
            total_mins += mins

        # 2. Calculate Streak
        streak = 0
        check_date = datetime.now()
        while True:
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str in daily_map and daily_map[date_str] > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                # Allow missing "today" if we haven't started yet
                if date_str == datetime.now().strftime("%Y-%m-%d") and streak == 0:
                    check_date -= timedelta(days=1)
                    continue
                break

        # 3. Averages
        unique_days = len(daily_map)
        avg = total_mins / unique_days if unique_days > 0 else 0

        return {
            "total_hours": round(total_mins / 60, 1),
            "streak": streak,
            "daily_avg": int(avg),
            "daily_map": daily_map
        }

# --- WIDGET 1: WEEKLY BAR CHART ---
class WeeklyChart(QWidget):
    def __init__(self, daily_map):
        super().__init__()
        self.daily_map = daily_map
        self.setMinimumHeight(180)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Config
        w, h = self.width(), self.height()
        bar_width = (w - 60) / 7
        max_val = 120 # Cap bars at 2 hours (120 mins) for visual scaling
        
        days = []
        today = datetime.now()
        # Get last 7 days names (Mon, Tue...) and dates
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            days.append((d.strftime("%a"), d.strftime("%Y-%m-%d")))

        # Draw Bars
        for i, (day_name, date_str) in enumerate(days):
            mins = self.daily_map.get(date_str, 0)
            
            # Calculate Height
            # Example: 60 mins / 120 max = 0.5 (50% height)
            ratio = min(1.0, mins / max_val)
            bar_h = int(ratio * (h - 50)) 
            bar_h = max(4, bar_h) # Minimum visible height

            x = int(15 + i * (bar_width + 5))
            y = h - 30 - bar_h

            # Color Logic (Highlight Today)
            color = QColor("#0984E3") if i == 6 else QColor("#DFE6E9")
            if mins == 0: color = QColor("#F1F2F6")

            # Draw Bar
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, int(bar_width), bar_h, 6, 6)

            # Draw Label (Mon, Tue)
            painter.setPen(QColor("#636E72"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(QRectF(x, h - 25, bar_width, 20), Qt.AlignCenter, day_name[0])
            
            # Draw Value on top if > 0
            if mins > 0:
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(QRectF(x, y - 20, bar_width, 20), Qt.AlignCenter, str(mins))

# --- WIDGET 2: HEATMAP GRID ---
class HeatmapGrid(QWidget):
    def __init__(self, daily_map):
        super().__init__()
        self.daily_map = daily_map
        self.setMinimumHeight(140)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        box_size = 18
        gap = 4
        start_x = 10
        start_y = 10

        # Show last 4 weeks (28 days)
        today = datetime.now()
        
        # We draw columns (Weeks)
        for week in range(5): 
            for day in range(7): # 0=Sun, 6=Sat
                # Calculate date backwards
                # This simple logic fills a 5x7 grid
                offset = (4 - week) * 7 + (6 - day)
                target_date = today - timedelta(days=offset)
                date_str = target_date.strftime("%Y-%m-%d")
                
                mins = self.daily_map.get(date_str, 0)

                # Color Scale (GitHub Style)
                if mins == 0: color = QColor("#F1F2F6") # Grey
                elif mins < 30: color = QColor("#74B9FF") # Light Blue
                elif mins < 60: color = QColor("#0984E3") # Medium Blue
                else: color = QColor("#2D3436") # Dark / Deep Focus

                x = start_x + week * (box_size + gap)
                y = start_y + day * (box_size + gap)

                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(x, y, box_size, box_size, 4, 4)

# --- MAIN TAB ---
class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = AnalyticsEngine()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setSpacing(20)

        # Get Data
        stats = self.engine.get_stats()

        # 1. IMPACT STATS (Header)
        row_stats = QHBoxLayout()
        row_stats.addWidget(self.create_stat_card("🔥 Streak", f"{stats['streak']} Days"))
        row_stats.addWidget(self.create_stat_card("⏳ Total", f"{stats['total_hours']} hrs"))
        row_stats.addWidget(self.create_stat_card("⚡ Avg", f"{stats['daily_avg']} m/day"))
        self.main_layout.addLayout(row_stats)

        # 2. WEEKLY RHYTHM
        card_weekly = self.create_card_container("Weekly Rhythm")
        card_weekly.layout().addWidget(WeeklyChart(stats['daily_map']))
        self.main_layout.addWidget(card_weekly)

        # 3. CONSISTENCY GRID
        card_heat = self.create_card_container("Consistency (30 Days)")
        card_heat.layout().addWidget(HeatmapGrid(stats['daily_map']))
        self.main_layout.addWidget(card_heat)

        # 4. TOP APPS (Simple Text List)
        # Using the new app_usage data
        card_apps = self.create_card_container("Top Distractions / Tools")
        lbl_apps = QLabel(self.get_top_apps_text(self.engine.load_data()))
        lbl_apps.setStyleSheet("color: #636E72; font-family: 'Consolas'; font-size: 12px;")
        card_apps.layout().addWidget(lbl_apps)
        self.main_layout.addWidget(card_apps)

        self.main_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def create_stat_card(self, title, value):
        frame = QFrame()
        frame.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #E0E0E0;")
        l = QVBoxLayout(frame)
        l.setContentsMargins(15, 15, 15, 15)
        
        t = QLabel(title)
        t.setStyleSheet("color: #636E72; font-size: 12px; font-weight: bold;")
        
        v = QLabel(value)
        v.setStyleSheet("color: #2D3436; font-size: 20px; font-weight: 800;")
        
        l.addWidget(t)
        l.addWidget(v)
        return frame

    def create_card_container(self, title):
        frame = QFrame()
        frame.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E0E0E0;")
        l = QVBoxLayout(frame)
        l.setContentsMargins(20, 20, 20, 20)
        
        head = QLabel(title)
        head.setStyleSheet("color: #0984E3; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        l.addWidget(head)
        return frame

    def get_top_apps_text(self, data):
        # Aggregate all app usage
        total_usage = {}
        for entry in data:
            apps = entry.get("app_usage", {})
            if isinstance(apps, dict):
                for app, sec in apps.items():
                    total_usage[app] = total_usage.get(app, 0) + sec
        
        # Sort by most used
        sorted_apps = sorted(total_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not sorted_apps: return "No app data recorded yet."
        
        text = ""
        for i, (name, sec) in enumerate(sorted_apps):
            mins = sec // 60
            text += f"{i+1}. {name} — {mins} min\n"
        return text.strip()