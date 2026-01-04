import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

print("Starting minimal test...")

try:
    app = QApplication(sys.argv)
    print("QApplication created")

    window = QWidget()
    window.setWindowTitle("Test")
    window.resize(300, 200)

    layout = QVBoxLayout()
    label = QLabel("Hello World!")
    layout.addWidget(label)
    window.setLayout(layout)

    window.show()
    print("Window shown")

    # Don't call app.exec() for this test
    print("Test completed successfully")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()