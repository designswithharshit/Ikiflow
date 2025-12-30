import sys
import platform
import requests
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                               QTextEdit, QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt

class FeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help Improve Ikiflow")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; font-family: 'Segoe UI', sans-serif; color: #2D3436; }
            QLabel { border: none; background: transparent; }
            QLabel#Title { font-size: 22px; font-weight: 800; color: #2D3436; }
            QLabel#LabelBold { font-size: 13px; font-weight: bold; color: #2D3436; margin-top: 5px; }
            QLineEdit, QTextEdit, QComboBox { 
                padding: 8px; border: 1px solid #DFE6E9; border-radius: 5px; background: #FAFAFA; 
            }
            QPushButton {
                background-color: #0984E3; color: white; border-radius: 12px;
                padding: 12px; font-weight: bold; font-size: 14px; border: none; margin-top: 10px;
            }
            QPushButton:hover { background-color: #74B9FF; }
        """)

        layout = QVBoxLayout(self)

        # Header
        title = QLabel("Feedback & Bug Report")
        title.setObjectName("Title")
        layout.addWidget(title)

        # Type
        type_label = QLabel("Feedback Type")
        type_label.setObjectName("LabelBold")
        layout.addWidget(type_label)
        self.type_box = QComboBox()
        self.type_box.addItems(["Bug Report", "Feature Request", "General Feedback"])
        layout.addWidget(self.type_box)

        # Message
        msg_label = QLabel("Message")
        msg_label.setObjectName("LabelBold")
        layout.addWidget(msg_label)
        self.message_box = QTextEdit()
        self.message_box.setPlaceholderText("Please describe your thoughts or the bug...")
        self.message_box.setFixedHeight(100)
        layout.addWidget(self.message_box)

        # Email
        email_label = QLabel("Email (Optional)")
        email_label.setObjectName("LabelBold")
        layout.addWidget(email_label)
        self.email_box = QLineEdit()
        self.email_box.setPlaceholderText("For follow-up...")
        layout.addWidget(self.email_box)

        # Send Button
        self.send_btn = QPushButton("Send Feedback")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_feedback)
        layout.addWidget(self.send_btn)

    def send_feedback(self):
        msg = self.message_box.toPlainText().strip()
        if not msg:
            QMessageBox.warning(self, "Empty", "Please enter a message.")
            return

        self.send_btn.setText("Sending...")
        self.send_btn.setEnabled(False)

        # Prepare Data
        payload = {
            "type": self.type_box.currentText(),
            "message": msg,
            "email": self.email_box.text(),
            "app_version": "2.0.2", # You can pass this dynamically if you want
            "os": f"{platform.system()} {platform.release()}"
        }

        # Send to Formspree
        # REPLACE 'your_form_id' WITH YOUR ACTUAL ID FROM FORMSPREE
        form_url = "https://formspree.io/f/meeqbply" 

        try:
            response = requests.post(form_url, json=payload, timeout=10)
            
            if response.status_code == 200 or response.ok:
                QMessageBox.information(self, "Thank You", "Feedback sent successfully!")
                self.accept()
            else:
                raise Exception("Server Error")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", "Could not send feedback. Check internet connection.")
            self.send_btn.setText("Send Feedback")
            self.send_btn.setEnabled(True)