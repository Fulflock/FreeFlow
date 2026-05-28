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
from src.updater import start_background_check


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
            amp_provider=self.recorder.get_current_amplitude,
        )
        self.history = DictationHistory()
        self.recording = False
        self._record_start_time = 0
        self._setup_hotkey()

    def _setup_hotkey(self):
        import keyboard

        combo = self.config.get("hotkey_combo", ["ctrl", "space"])
        # keyboard lib uses '+' joined string syntax: "ctrl+space"
        self._hotkey_str = "+".join(combo)
        self._press_lock = threading.Lock()
        self._last_press_ts = 0.0

        # The slow work (start/stop audio, show overlay) must NEVER run inside
        # the keyboard-hook thread — Windows will silently disable the hook if
        # the callback takes >~300ms. We capture under the lock only briefly,
        # flip the `recording` flag, and dispatch the real work to a worker thread.

        def _press_worker():
            try:
                self._on_hotkey_press()
            except RuntimeError as mic_err:
                # Microphone unavailable — show a user-friendly error dialog.
                self.recording = False
                try:
                    self.ui.hide()
                except Exception:
                    pass
                error_msg = str(mic_err)
                def _show_error():
                    try:
                        import tkinter as _tk
                        from tkinter import messagebox as _mbox
                        root = _tk.Tk()
                        root.withdraw()
                        _mbox.showerror(
                            "FreeFlow — micro indisponible",
                            f"Le micro n'est pas disponible.\n\n{error_msg}\n\n"
                            "Vérifie tes paramètres Windows → Confidentialité → Microphone, "
                            "et que ton micro est bien branché.",
                        )
                        root.destroy()
                    except Exception:
                        import traceback
                        traceback.print_exc()
                threading.Thread(target=_show_error, daemon=True).start()
            except Exception:
                self.recording = False  # rollback so next press can retry
                import traceback
                traceback.print_exc()

        def _release_worker():
            try:
                self._on_hotkey_release()
            except Exception:
                import traceback
                traceback.print_exc()

        def on_press_event(*_args):
            with self._press_lock:
                if self.recording:
                    return  # already recording, ignore key auto-repeat
                now = time.time()
                if now - self._last_press_ts < 0.08:
                    return  # debounce auto-repeat
                self._last_press_ts = now
                self.recording = True  # flip flag under lock
            # Run actual work off-hook-thread — must return fast
            threading.Thread(target=_press_worker, daemon=True).start()

        def on_release_event(_event):
            should_stop = False
            with self._press_lock:
                if self.recording:
                    self.recording = False
                    should_stop = True
            if should_stop:
                threading.Thread(target=_release_worker, daemon=True).start()

        # Register the combo trigger (fires when ctrl+space is pressed)
        try:
            keyboard.add_hotkey(
                self._hotkey_str,
                on_press_event,
                suppress=True,
                trigger_on_release=False,
            )
        except Exception:
            import traceback
            traceback.print_exc()

        # Hook each key individually so release of EITHER fires stop -
        # robust to user releasing keys in any order.
        for key_name in combo:
            try:
                keyboard.on_release_key(key_name, on_release_event, suppress=False)
            except Exception:
                import traceback
                traceback.print_exc()

        # Watchdog: force-stop if recording stuck > 30s
        def _watchdog():
            while True:
                time.sleep(2)
                if self.recording and (time.time() - self._record_start_time) > 30:
                    with self._press_lock:
                        if self.recording:
                            try:
                                self._on_hotkey_release()
                            except Exception:
                                import traceback
                                traceback.print_exc()

        threading.Thread(target=_watchdog, daemon=True).start()

    def _on_hotkey_press(self):
        # Flag already flipped to True by the event callback. Just do the work.
        self._record_start_time = time.time()
        self.recorder.start_recording()
        self.ui.show_recording()

    def _on_hotkey_release(self):
        # Flag already flipped to False by the event callback.
        audio_data = self.recorder.stop_recording()
        self.ui.show_transcribing()

        def do_transcribe():
            try:
                if audio_data is None or len(audio_data) < 1600:
                    self.ui.hide()
                    return
                duration = max(0.0, time.time() - self._record_start_time) if self._record_start_time > 0 else 0.0
                text = self.transcriber.transcribe(audio_data)
                stripped = (text or "").strip()
                if stripped:
                    self.history.save(stripped, duration)
                    self.ui.show_click_to_paste(stripped)
                    paste_at_cursor(stripped)
                else:
                    self.ui.hide()
            except Exception:
                import traceback
                traceback.print_exc()

        threading.Thread(target=do_transcribe, daemon=True).start()

    def quit(self):
        try:
            import keyboard as _kb
            _kb.unhook_all()
        except Exception:
            pass
        self.ui.stop()

    def run(self):
        print("FreeFlow — Chargement du modele Whisper...")
        self.transcriber.warm_up()
        print("FreeFlow — Pret ! Maintiens Ctrl+Space pour dicter.")

        # Background updater — polls GitHub Releases once per day.
        # Silent + non-blocking; respects `update_check_enabled` + `github_repo`
        # in config.json. If a new version is found, shows a tkinter dialog
        # asking the user to install (downloads + auto-restarts).
        try:
            start_background_check(self.config)
        except Exception:
            import traceback
            traceback.print_exc()

        # On manual launch (no --silent), pop the Main Window so the user sees
        # something after double-clicking the desktop shortcut.
        silent = any(a in ("--silent", "--minimized") for a in sys.argv[1:])
        if not silent:
            def _open_main_when_ready():
                try:
                    # Tiny delay so the pywebview bubble backend has booted.
                    time.sleep(1.2)
                    self.ui.open_main_window()
                except Exception:
                    import traceback
                    traceback.print_exc()
            threading.Thread(target=_open_main_when_ready, daemon=True).start()

        self.ui.start()


if __name__ == "__main__":
    # Single-instance guard — exit silently if FreeFlow is already running.
    try:
        import win32event
        import win32api
        import winerror
        _mutex = win32event.CreateMutex(None, False, "Local\\FreeFlow_SingleInstance_Mutex_v1")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            sys.exit(0)
    except ImportError:
        pass  # pywin32 not installed — proceed without enforcement

    app = FreeFlow()
    app.run()
