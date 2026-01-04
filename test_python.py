with open("test.log", "w") as f:
    f.write("Python is working\n")
    import sys
    f.write(f"Python version: {sys.version}\n")
    try:
        import PySide6
        f.write("PySide6 imported successfully\n")
    except Exception as e:
        f.write(f"PySide6 import error: {e}\n")