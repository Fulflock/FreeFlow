import time
import threading
import ctypes

import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()
_pending_text = None
_lock = threading.Lock()
_watcher_running = False

VK_LBUTTON = 0x01


def _is_left_click_pressed() -> bool:
    return ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000 != 0


def _watch_for_click():
    global _pending_text, _watcher_running

    while True:
        with _lock:
            if _pending_text is None:
                _watcher_running = False
                return

        if _is_left_click_pressed():
            time.sleep(0.05)
            while _is_left_click_pressed():
                time.sleep(0.01)
            time.sleep(0.15)

            with _lock:
                text = _pending_text
                _pending_text = None

            if text:
                _do_paste(text)

            _watcher_running = False
            return

        time.sleep(0.02)


def _do_paste(text: str) -> None:
    try:
        old_clipboard = pyperclip.paste()
    except pyperclip.PyperclipException:
        old_clipboard = None

    pyperclip.copy(text)

    _keyboard.press(Key.ctrl)
    _keyboard.press("v")
    _keyboard.release("v")
    _keyboard.release(Key.ctrl)

    time.sleep(0.15)

    if old_clipboard is not None:
        pyperclip.copy(old_clipboard)
    else:
        pyperclip.copy("")


def paste_at_cursor(text: str) -> None:
    global _pending_text, _watcher_running
    with _lock:
        _pending_text = text
    if not _watcher_running:
        _watcher_running = True
        threading.Thread(target=_watch_for_click, daemon=True).start()
