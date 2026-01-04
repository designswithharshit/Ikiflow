import os
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from Ikiflow_utils import resource_path       # Import the helper

# --- Sound Engine ---

class SoundEngine:
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