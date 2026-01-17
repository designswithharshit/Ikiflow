import json
import os
import calendar
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QScrollArea, QGraphicsDropShadowEffect, QPushButton)
from PySide6.QtCore import Qt, Signal, QRectF, QSize, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QBrush

# --- 0. DESIGN SYSTEM CONSTANTS ---
ACCENT       = "#0984E3"  # Ikiflow Blue
ACCENT_FADE  = "rgba(9, 132, 227, 0.15)" # Subtle background blue
TEXT_MAIN    = "#2D3436"  # Deep Grey (Primary)
TEXT_DIM     = "#636E72"  # Muted Grey (Secondary)
TEXT_QUIET   = "#A4AAB0"  # Very light grey (Labels)
BG_CARD      = "#FFFFFF"
BG_SOFT      = "#F8F9FA"  # Off-white backgrounds
BORDER_SOFT  = "#ECEFF1"
SUCCESS      = "#00B894"
WARNING      = "#FAB1A0"

# --- 1. DATA ENGINE ---
class AnalyzerData:
    def __init__(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(base_path, "history.json")
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'w') as f: json.dump([], f)
            except: pass

    def load_data(self):
        try:
            with open(self.filepath, 'r') as f: return json.load(f)
        except: return []

    def get_stats(self):
        data = self.load_data()
        if not data: return {"streak": 0, "total_hours": 0.0, "daily_avg": 0, "consistency": 0}

        total_mins = sum(entry.get("focus_actual", 0) for entry in data)
        dates = set(entry.get("date") for entry in data)
        avg = total_mins / len(dates) if dates else 0

        daily_map = {d: 0 for d in dates}
        streak = 0
        check = datetime.now()
        if check.strftime("%Y-%m-%d") not in daily_map:
            check -= timedelta(days=1)
        while check.strftime("%Y-%m-%d") in daily_map:
            streak += 1
            check -= timedelta(days=1)

        # Logic Extra: Consistency Score (Simple metric 0-100 based on streak)
        consistency = min(100, int((streak / 7) * 100))

        return {
            "streak": streak,
            "total_hours": round(total_mins / 60, 1),
            "daily_avg": int(avg),
            "consistency": consistency
        }

    def get_month_map(self, year, month):
        data = self.load_data()
        prefix = f"{year}-{month:02d}"
        status_map = {}
        for entry in data:
            if entry.get("date", "").startswith(prefix):
                try:
                    day = int(entry["date"].split("-")[2])
                    status = entry.get("status", "Skipped")
                    current = status_map.get(day, "empty")
                    if status == "Completed": status_map[day] = "filled"
                    elif current != "filled": status_map[day] = "outline"
                except: continue
        return status_map

    def get_week_data(self, anchor_date):
        data = self.load_data()
        start = anchor_date - timedelta(days=anchor_date.weekday())
        week_data = []
        for i in range(7):
            d = start + timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            mins = sum(e.get("focus_actual", 0) for e in data if e.get("date") == d_str)
            week_data.append((d_str, mins))
        return week_data

    def get_sessions_for_date(self, date_str):
        data = self.load_data()
        return [s for s in data if s.get("date") == date_str]


# --- 2. COMPONENTS ---

class StatCard(QFrame):
    def __init__(self, title, value, icon_char):
        super().__init__()
        self.setFixedSize(160, 80)
        # Cleaner, softer border
        self.setStyleSheet(f"QFrame {{ background-color: {BG_SOFT}; border-radius: 12px; border: 1px solid {BORDER_SOFT}; }}")
        
        l = QVBoxLayout(self)
        l.setContentsMargins(15, 10, 15, 10)
        
        h = QHBoxLayout()
        t = QLabel(title.upper())
        # Visual Hierarchy: Muted title
        t.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 9px; font-weight: 700; letter-spacing: 1px; border: none;")
        
        i = QLabel(icon_char)
        # Visual Hierarchy: Icon as background texture
        i.setStyleSheet(f"color: {ACCENT_FADE}; font-size: 28px; border: none;")
        
        h.addWidget(t)
        h.addStretch()
        h.addWidget(i)
        
        v = QLabel(str(value))
        # Visual Hierarchy: Dominant Value
        v.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 24px; font-weight: 900; border: none; background: transparent;")
        
        l.addLayout(h)
        l.addWidget(v)

class ExpandableSessionItem(QFrame):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.is_expanded = False
        
        # Base Style
        self.setStyleSheet(f"""
            QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER_SOFT}; border-radius: 8px; }}
            QFrame:hover {{ border: 1px solid {ACCENT}; }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(0) # Will animate this logic later

        # --- A. HEADER ---
        self.header = QWidget()
        self.header.setStyleSheet("border:none;")
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(0, 0, 0, 0)
        
        ts = datetime.fromisoformat(self.session["timestamp"])
        lbl_time = QLabel(ts.strftime("%I:%M %p"))
        # Stronger time contrast
        lbl_time.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 13px; font-weight: 800; border: none;")
        
        # Logic Extra: Quality Badge
        planned = self.session.get("focus_planned", 1)
        actual = self.session.get("focus_actual", 0)
        ratio = actual / planned if planned > 0 else 0
        
        status_text = "GOOD"
        status_col = SUCCESS
        if ratio < 0.6: 
            status_text = "DISTRACTED"
            status_col = WARNING
        elif ratio >= 1.0:
            status_text = "DEEP FOCUS"
            status_col = ACCENT

        lbl_stat = QLabel(status_text)
        lbl_stat.setStyleSheet(f"color: {status_col}; font-size: 9px; font-weight: 800; border: 1px solid {status_col}; border-radius: 4px; padding: 2px 6px;")
        
        self.arrow = QLabel("▼")
        self.arrow.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 10px; border: none;")
        
        hl.addWidget(lbl_time)
        hl.addSpacing(10)
        hl.addWidget(lbl_stat)
        hl.addStretch()
        hl.addWidget(self.arrow)
        self.layout.addWidget(self.header)

        # --- B. DETAILS ---
        self.details = QWidget()
        self.details.setStyleSheet("border:none;")
        dl = QVBoxLayout(self.details)
        dl.setContentsMargins(0, 10, 0, 0)
        
        # Grid Stats
        gf = QFrame()
        gf.setStyleSheet(f"background: {BG_SOFT}; border-radius: 6px; border: none;")
        g = QHBoxLayout(gf)
        g.setContentsMargins(10, 10, 10, 10)
        
        brk = self.session.get("break_selected", 0)
        status_raw = self.session.get("status", "Skipped")
        skip = "Yes" if status_raw == "Skipped" else "No"
        
        def mk_stat(l, v):
            c = QWidget()
            vl = QVBoxLayout(c)
            vl.setContentsMargins(0,0,0,0)
            t = QLabel(l)
            t.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 9px; border: none;")
            val = QLabel(v)
            val.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 12px; font-weight: bold; border: none;")
            vl.addWidget(t)
            vl.addWidget(val)
            return c
            
        g.addWidget(mk_stat("Timer", f"{planned}m"))
        g.addWidget(mk_stat("Actual", f"{actual}m"))
        g.addWidget(mk_stat("Break", f"{brk}m"))
        g.addWidget(mk_stat("Skip", skip))
        dl.addWidget(gf)
        
        # App Usage
        apps = self.session.get("app_usage", {})
        if apps:
            la = QLabel("APP USAGE")
            la.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 9px; font-weight: bold; margin-top: 5px;")
            dl.addWidget(la)
            s_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)
            max_v = max([v for k, v in s_apps]) if s_apps else 1
            
            for n, sec in s_apps:
                if n == "Focus Timer" or sec < 5: continue
                row = QHBoxLayout()
                nl = QLabel(n[:18])
                nl.setFixedWidth(100)
                nl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
                
                bar_bg = QFrame()
                bar_bg.setFixedHeight(4)
                bar_bg.setStyleSheet(f"background: {BORDER_SOFT}; border-radius: 2px;")
                
                bar_fill = QFrame(bar_bg)
                bar_fill.setFixedHeight(4)
                # Calmer bars using transparency
                bar_fill.setStyleSheet(f"background: rgba(9, 132, 227, 0.6); border-radius: 2px;") 
                bar_fill.setFixedWidth(int((sec/max_v)*100))
                
                mins = sec // 60
                tl = QLabel(f"{mins}m")
                tl.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 10px;")
                
                row.addWidget(nl)
                row.addWidget(bar_bg, 1)
                row.addWidget(tl)
                dl.addLayout(row)
        
        self.layout.addWidget(self.details)
        self.details.hide()

    def mousePressEvent(self, e):
        if self.is_expanded:
            self.details.hide()
            self.arrow.setText("▼")
            self.setStyleSheet(f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER_SOFT}; border-radius: 8px; }} QFrame:hover {{ border: 1px solid {ACCENT}; }}")
            self.layout.setSpacing(0) # Collapse spacing
        else:
            self.details.show()
            self.arrow.setText("▲")
            self.setStyleSheet(f"QFrame {{ background: {BG_CARD}; border: 1px solid {ACCENT}; border-radius: 8px; }}")
            self.layout.setSpacing(8) # Breathe spacing
            
        self.is_expanded = not self.is_expanded
        self.parentWidget().adjustSize()

class MonthGrid(QWidget):
    dayClicked = Signal(str)
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setFixedSize(280, 240)
        self.view_date = datetime.now()

    def set_date(self, date_obj):
        self.view_date = date_obj
        self.update()

    def mousePressEvent(self, e):
        start_y, cell, gap = 45, 28, 8
        grid_y = start_y + 30
        if e.position().y() < grid_y: return
        col = int(e.position().x() // (cell + gap))
        row = int((e.position().y() - grid_y) // (cell + gap))
        cal = calendar.monthcalendar(self.view_date.year, self.view_date.month)
        if 0 <= row < len(cal) and 0 <= col < 7:
            day = cal[row][col]
            if day != 0:
                self.dayClicked.emit(f"{self.view_date.year}-{self.view_date.month:02d}-{day:02d}")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        days = ["M", "T", "W", "T", "F", "S", "S"]
        start_y, cell, gap = 45, 28, 8
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(QColor(TEXT_QUIET)) # Faded headers
        for i, d in enumerate(days):
            p.drawText(QRectF(i*(cell+gap), start_y, cell, 20), Qt.AlignCenter, d)

        cal = calendar.monthcalendar(self.view_date.year, self.view_date.month)
        status_map = self.engine.get_month_map(self.view_date.year, self.view_date.month)
        grid_y = start_y + 30
        
        today = datetime.now()

        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0: continue
                rect = QRectF(c*(cell+gap), grid_y + r*(cell+gap), cell, cell)
                st = status_map.get(day, "empty")
                
                # Logic Extra: Today Indicator
                is_today = (day == today.day and 
                            self.view_date.month == today.month and 
                            self.view_date.year == today.year)

                if st == "filled":
                    p.setBrush(QColor(ACCENT))
                    p.setPen(Qt.NoPen)
                    p.drawRoundedRect(rect, 6, 6)
                    p.setPen(QColor("#FFFFFF"))
                elif st == "outline":
                    p.setBrush(Qt.NoBrush)
                    p.setPen(QPen(QColor(ACCENT), 2))
                    p.drawRoundedRect(rect, 6, 6)
                    p.setPen(QColor(ACCENT))
                else:
                    # Faded empty cells
                    p.setBrush(QColor("#FAFBFC")) 
                    p.setPen(Qt.NoPen)
                    p.drawRoundedRect(rect, 6, 6)
                    p.setPen(QColor(TEXT_QUIET))
                
                if is_today:
                    p.setPen(QPen(QColor(TEXT_MAIN), 2))
                    # Draw subtle ring for today
                    p.setBrush(Qt.NoBrush)
                    p.drawRoundedRect(rect.adjusted(1,1,-1,-1), 6, 6)
                    if st == "filled": p.setPen(QColor("#FFFFFF")) # Keep text white if filled
                
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(rect, Qt.AlignCenter, str(day))

class EnergyChart(QWidget):
    daySelected = Signal(str)
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setMinimumHeight(140)
        self.week_anchor = datetime.now()
        self.data = []
        self.sel_idx = -1
        self.refresh_data()

    def set_anchor(self, date_obj):
        self.week_anchor = date_obj
        self.refresh_data()
        start = self.week_anchor - timedelta(days=self.week_anchor.weekday())
        try:
            diff = (date_obj - start).days
            if 0 <= diff < 7: self.sel_idx = diff
            else: self.sel_idx = -1
        except: self.sel_idx = -1
        self.update()

    def refresh_data(self):
        self.data = self.engine.get_week_data(self.week_anchor)
        
        # Logic Extra: Insight calculation
        total = sum(m for _, m in self.data)
        if total == 0: self.insight = "Low focus week"
        elif total < 300: self.insight = "Building momentum"
        else: self.insight = "Strong focus rhythm"
        
        self.update()

    def get_insight(self):
        return getattr(self, 'insight', "")

    def mousePressEvent(self, e):
        w = self.width() / 7
        self.sel_idx = int(e.position().x() // w)
        if 0 <= self.sel_idx < 7:
            self.daySelected.emit(self.data[self.sel_idx][0])
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width() / 7, self.height()
        max_v = max([d[1] for d in self.data] + [60])
        labels = ["M", "T", "W", "T", "F", "S", "S"]
        for i, (date, mins) in enumerate(self.data):
            x = i * w
            
            # Rounded, soft selection
            if i == self.sel_idx:
                p.setBrush(QColor(BG_SOFT))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(x+4, 4, w-8, h-8, 12, 12)
            
            bh = (mins / max_v) * (h - 40)
            bh = max(4, bh) if mins > 0 else 0
            
            # Transparent inactive bars
            col = QColor(ACCENT) if mins > 0 else QColor("#DFE6E9")
            if mins == 0: col.setAlpha(100) # Fade empty bars more
            
            p.setBrush(col)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(x + w/2 - 5, h - 30 - bh, 10, bh, 5, 5)
            
            p.setPen(QColor(TEXT_DIM))
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.drawText(QRectF(x, h-25, w, 20), Qt.AlignCenter, labels[i])

class Timeline(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)
    def update_date(self, date_str):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        sessions = self.engine.get_sessions_for_date(date_str)
        if not sessions:
            lbl = QLabel("No sessions for this day.")
            lbl.setStyleSheet(f"color: {TEXT_QUIET}; font-style: italic; margin-top: 20px; border: none;")
            lbl.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(lbl)
            return
        sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        for s in sessions:
            self.layout.addWidget(ExpandableSessionItem(s))

# --- 3. MAIN ANALYZER WINDOW ---
class AnalyzerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reflection")
        self.resize(850, 620)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.engine = AnalyzerData()
        self.current_month_date = datetime.now()
        self.current_week_date = datetime.now()
        
        root = QVBoxLayout(self)
        self.card = QFrame()
        self.card.setStyleSheet(f"background: {BG_CARD}; border-radius: 20px;")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0,0,0,40))
        self.card.setGraphicsEffect(shadow)
        root.addWidget(self.card)
        
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Header
        h_row = QHBoxLayout()
        title = QLabel("Reflection")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {TEXT_MAIN};")
        btn_close = QPushButton("×")
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"background: transparent; color: {TEXT_QUIET}; font-size: 24px; border: none;")
        btn_close.clicked.connect(self.close)
        h_row.addWidget(title)
        h_row.addStretch()
        h_row.addWidget(btn_close)
        layout.addLayout(h_row)

        # Stats
        stats = self.engine.get_stats()
        stat_row = QHBoxLayout()
        stat_row.addWidget(StatCard("Streak", f"{stats['streak']}", "🔥"))
        stat_row.addWidget(StatCard("Total Hours", f"{stats['total_hours']}", "⏳"))
        # Logic Extra: Showing Consistency instead of Avg (Switchable)
        stat_row.addWidget(StatCard("Consistency", f"{stats['consistency']}%", "⚡"))
        stat_row.addStretch()
        layout.addLayout(stat_row)
        
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {BORDER_SOFT}; margin: 5px 0;")
        layout.addWidget(line)

        # Content
        main_content = QHBoxLayout()
        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        
        # Month Nav
        month_nav = QHBoxLayout()
        self.btn_prev_m = self.create_nav_btn("<", self.prev_month)
        self.lbl_month = QLabel()
        self.lbl_month.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {TEXT_MAIN};")
        self.btn_next_m = self.create_nav_btn(">", self.next_month)
        month_nav.addWidget(self.btn_prev_m)
        month_nav.addStretch()
        month_nav.addWidget(self.lbl_month)
        month_nav.addStretch()
        month_nav.addWidget(self.btn_next_m)
        left_col.addLayout(month_nav)
        
        self.month_grid = MonthGrid(self.engine)
        left_col.addWidget(self.month_grid)
        
        # Week Nav & Chart
        week_container = QVBoxLayout()
        week_container.setSpacing(5)
        
        lbl_w_title = QLabel("WEEKLY FLOW")
        lbl_w_title.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        week_container.addWidget(lbl_w_title)
        
        week_nav = QHBoxLayout()
        self.btn_prev_w = self.create_nav_btn("<", self.prev_week)
        
        self.lbl_week_range = QLabel()
        self.lbl_week_range.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 12px; font-weight: bold;")
        self.lbl_week_range.setAlignment(Qt.AlignCenter)

        self.btn_next_w = self.create_nav_btn(">", self.next_week)
        
        week_nav.addWidget(self.btn_prev_w)
        week_nav.addWidget(self.lbl_week_range, 1) 
        week_nav.addWidget(self.btn_next_w)
        week_container.addLayout(week_nav)
        
        self.chart = EnergyChart(self.engine) 
        week_container.addWidget(self.chart)
        
        # Logic Extra: Weekly Insight Label
        self.lbl_insight = QLabel("Loading...")
        self.lbl_insight.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: bold; margin-top: 5px;")
        self.lbl_insight.setAlignment(Qt.AlignCenter)
        week_container.addWidget(self.lbl_insight)
        
        left_col.addLayout(week_container)
        left_col.addStretch()
        main_content.addLayout(left_col)

        # Right Col
        right_col = QVBoxLayout()
        lbl_detail = QLabel("SESSION DETAIL")
        lbl_detail.setStyleSheet(f"color: {TEXT_QUIET}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        right_col.addWidget(lbl_detail)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        self.timeline = Timeline(self.engine)
        scroll.setWidget(self.timeline)
        right_col.addWidget(scroll)
        main_content.addLayout(right_col, 1)
        layout.addLayout(main_content)

        # Init
        self.chart.daySelected.connect(self.timeline.update_date)
        self.month_grid.dayClicked.connect(self.jump_to_date)
        self.update_month_header()
        self.update_week_header()
        self.month_grid.set_date(self.current_month_date)
        self.chart.set_anchor(self.current_week_date)
        self.timeline.update_date(self.current_week_date.strftime("%Y-%m-%d"))

    def create_nav_btn(self, text, func):
        b = QPushButton(text)
        b.setFixedSize(24, 24)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{ background: {BG_SOFT}; border-radius: 12px; font-weight: bold; color: {TEXT_DIM}; border: none;}}
            QPushButton:hover {{ background: #DFE6E9; color: {TEXT_MAIN}; }}
        """)
        b.clicked.connect(func)
        return b

    def update_week_header(self):
        start = self.current_week_date - timedelta(days=self.current_week_date.weekday())
        end = start + timedelta(days=6)
        if start.year == end.year:
            text = f"{start.strftime('%b %d')} - {end.strftime('%b %d')}"
        else:
            text = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        self.lbl_week_range.setText(text)
        # Update Insight Label
        self.lbl_insight.setText(self.chart.get_insight())

    def prev_month(self):
        first = self.current_month_date.replace(day=1)
        self.current_month_date = first - timedelta(days=1)
        self.update_month_header()
        self.month_grid.set_date(self.current_month_date)

    def next_month(self):
        days = calendar.monthrange(self.current_month_date.year, self.current_month_date.month)[1]
        self.current_month_date += timedelta(days=days)
        self.update_month_header()
        self.month_grid.set_date(self.current_month_date)

    def update_month_header(self):
        self.lbl_month.setText(self.current_month_date.strftime("%B %Y"))

    def prev_week(self):
        self.current_week_date -= timedelta(days=7)
        self.chart.set_anchor(self.current_week_date)
        self.update_week_header()

    def next_week(self):
        self.current_week_date += timedelta(days=7)
        self.chart.set_anchor(self.current_week_date)
        self.update_week_header()

    def jump_to_date(self, date_str):
        d = datetime.strptime(date_str, "%Y-%m-%d")
        self.current_week_date = d
        self.chart.set_anchor(d)
        self.update_week_header()
        self.timeline.update_date(date_str)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)