import json
import os
import ctypes
from datetime import datetime, date
from uuid import uuid4


def _get_foreground_window_title() -> str:
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value or "Unknown"


class DictationHistory:
    def __init__(self, history_dir: str = None):
        self._dir = history_dir or os.path.join(os.path.expanduser("~"), ".whisperflow", "history")
        os.makedirs(self._dir, exist_ok=True)

    def _day_file(self, d: date = None) -> str:
        d = d or date.today()
        return os.path.join(self._dir, f"{d.isoformat()}.json")

    def _load_day(self, path: str) -> list[dict]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_day(self, path: str, entries: list[dict]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def save(self, text: str, duration_seconds: float = 0) -> dict:
        entry = {
            "id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "duration_seconds": round(duration_seconds, 2),
            "app": _get_foreground_window_title(),
        }
        path = self._day_file()
        entries = self._load_day(path)
        entries.append(entry)
        self._save_day(path, entries)
        return entry

    def get_today(self) -> list[dict]:
        return self._load_day(self._day_file())

    def get_all(self) -> list[dict]:
        all_entries = []
        for f in sorted(os.listdir(self._dir)):
            if f.endswith(".json"):
                all_entries.extend(self._load_day(os.path.join(self._dir, f)))
        return all_entries

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [e for e in self.get_all() if q in e["text"].lower()]

    def get_stats(self) -> dict:
        all_e = self.get_all()
        today_e = self.get_today()
        return {
            "total_dictations": len(all_e),
            "total_words": sum(len(e["text"].split()) for e in all_e),
            "today_dictations": len(today_e),
            "today_words": sum(len(e["text"].split()) for e in today_e),
        }
