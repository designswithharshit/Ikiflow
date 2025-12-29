# ⏳ Ikiflow (formerly Lumina Focus)

**A distraction-free focus timer designed to keep you in the flow.**

Ikiflow is a modern productivity tool built with **Python & PySide6**. It replaces the rigid "Pomodoro" structure with a flexible **Task Loop** system—letting you finish your thought before taking a break.

| Home Screen | Settings | Timer Run |
| :---: | :---: | :---: |
|<img width="400" height="601" alt="MainWindow" src="https://github.com/user-attachments/assets/d342da5a-ee12-4cbd-b857-65a8240c9fa4" /> | <img width="400" height="601" alt="WidgetCustomization" src="https://github.com/user-attachments/assets/ae1aab65-c841-44f3-889e-1c28fc9423ce" /> | <img width="400" height="601" alt="TimerRunScreen" src="https://github.com/user-attachments/assets/8846c1ce-0180-4faf-ab75-90f38a2d2a2a" /> |


## ✨ Key Features

### 🧠 The Task Loop
Unlike standard timers that force you to stop, Ikiflow respects your focus.
* When the timer hits `00:00`, the screen dims and asks: **"Did you finish your task?"**
* **NO:** Instantly adds **+5 Minutes** so you can wrap up.
* **YES:** Starts the recovery break.

### 🌑 Smart Break Overlay
A fullscreen, dark-mode overlay designed to rest your eyes and mind.
* **Health Tips:** Cycles through ergonomic reminders (e.g., *"Relax your jaw"*, *"Look 20ft away"*).
* **Minimalist UI:** No distractions, just a subtle progress bar.

### 🎧 Ambient Audio Engine
* **Instant Focus:** One-click toggle for built-in **Brown Noise**.
* **Custom Audio:** Load your own local `.wav` loops (Rain, Lo-Fi, Forest) using the Browse `...` button.

### ⚡ Smart System
* **Auto-Update:** Checks for the latest version on startup.
* **Tray Support:** Minimizes silently to the system tray.
* **Cancel Logic:** `Alt+F4` correctly cancels a break and resets the session.

---

## 📦 Download & Install

**No installation required.** Ikiflow is a portable application.

1. Go to the [Releases Page](../../releases/latest).
2. Download `Ikiflow.exe`.
3. Run it!

---

## 🛠️ For Developers

If you want to run the source code or build it yourself:

### 1. Requirements
* Python 3.10+
* PySide6

### 2. Setup
```bash
# Clone the repo
git clone [https://github.com/YOUR_USERNAME/Ikiflow.git](https://github.com/YOUR_USERNAME/Ikiflow.git)
cd Ikiflow

# Install dependencies
pip install PySide6
```

### 3. Running the App
```bash
python main.py
```

### 4. Building the .exe
```bash
python -m PyInstaller --noconsole --onefile --icon="IkiflowIcon.ico" --add-data "IkiflowIcon.ico;." --add-data "noise.wav;." --name="Ikiflow" main.py
```
<br></br>
> Built with ❤️ by **Harshit**
