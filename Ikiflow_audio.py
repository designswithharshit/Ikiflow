import os
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from Ikiflow_utils import resource_path       # Import the helper

# --- Sound Engine ---

class SoundEngine:
    def __init__(self):
        self.effect = QSoundEffect()
        self.effect.setLoopCount(-2) # Infinite loop
        self.effect.setVolume(0.5)

    def load_sound(self, file_path):
        # Determine if it's a local user file or an internal resource
        if os.path.exists(file_path):
            url = QUrl.fromLocalFile(file_path)
        else:
            # Fallback for internal resource (noise.wav)
            url = QUrl.fromLocalFile(resource_path(file_path))
            
        self.effect.setSource(url)

    def play(self):
        self.effect.play()

    def stop(self):
        self.effect.stop()
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