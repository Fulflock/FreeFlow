import json
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio import AudioRecorder
from src.transcriber import Transcriber
from src.injector import paste_at_cursor
from src.ui import FreeFlowUI
from src.history import DictationHistory


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    base = get_base_path()
    for candidate in [os.path.join(base, "config.json"), os.path.join(base, "_internal", "config.json")]:
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


class FreeFlow:
    def __init__(self):
        self.config = load_config()
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(
            model_size=self.config.get("model_size", "base"),
            language=self.config.get("language", "fr"),
        )
        self.ui = FreeFlowUI(
            opacity=self.config.get("overlay_opacity", 0.85),
            on_quit=self.quit,
        )
        self.history = DictationHistory()
        self.recording = False
        self._record_start_time = 0
        self._setup_hotkey()

    def _setup_hotkey(self):
        from pynput import keyboard

        combo = self.config.get("hotkey_combo", ["ctrl", "space"])
        self._held_keys = set()
        self._combo_keys = set()
        for k in combo:
            if k in ("ctrl", "ctrl_l", "ctrl_r"):
                self._combo_keys.add(keyboard.Key.ctrl_l)
            elif k in ("shift", "shift_l", "shift_r"):
                self._combo_keys.add(keyboard.Key.shift_l)
            elif k in ("alt", "alt_l", "alt_r"):
                self._combo_keys.add(keyboard.Key.alt_l)
            elif k == "space":
                self._combo_keys.add(keyboard.Key.space)
            else:
                self._combo_keys.add(keyboard.KeyCode.from_char(k))

        def on_press(key):
            normalized = self._normalize_key(key)
            self._held_keys.add(normalized)
            if self._combo_keys.issubset(self._held_keys) and not self.recording:
                self._on_hotkey_press()

        def on_release(key):
            normalized = self._normalize_key(key)
            if self.recording and normalized in self._combo_keys:
                self._on_hotkey_release()
            self._held_keys.discard(normalized)

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.daemon = True

    @staticmethod
    def _normalize_key(key):
        from pynput import keyboard
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return keyboard.Key.ctrl_l
        if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            return keyboard.Key.shift_l
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            return keyboard.Key.alt_l
        return key

    def _on_hotkey_press(self):
        self.recording = True
        self._record_start_time = time.time()
        self.recorder.start_recording()
        self.ui.show_recording()

    def _on_hotkey_release(self):
        if not self.recording:
            return
        self.recording = False
        audio_data = self.recorder.stop_recording()
        self.ui.show_transcribing()

        def do_transcribe():
            if audio_data is None or len(audio_data) < 1600:
                self.ui.hide()
                return
            duration = time.time() - self._record_start_time
            text = self.transcriber.transcribe(audio_data)
            if text.strip():
                self.history.save(text.strip(), duration)
                self.ui.show_click_to_paste(text.strip())
                paste_at_cursor(text.strip())
            else:
                self.ui.hide()

        threading.Thread(target=do_transcribe, daemon=True).start()

    def quit(self):
        self.ui.stop()

    def run(self):
        print("FreeFlow — Chargement du modèle Whisper...")
        self.transcriber.warm_up()
        print("FreeFlow — Prêt ! Maintiens Ctrl+Space pour dicter.")
        self._listener.start()
        self.ui.start()


if __name__ == "__main__":
    app = FreeFlow()
    app.run()
