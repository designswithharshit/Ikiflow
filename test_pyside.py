import sys
print("Python version:", sys.version)
try:
    from PySide6.QtWidgets import QApplication
    print("PySide6 imported successfully")
    app = QApplication([])
    print("QApplication created successfully")
except Exception as e:
    print("Error:", e)