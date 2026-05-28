import json
import os
import sys
import time
import threading
import ctypes
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import uuid4


def _get_foreground_window_title() -> str:
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value or "Unknown"


class DictationHistory:
    def __init__(self, history_dir: str = None):
        self._dir = history_dir or os.path.join(os.path.expanduser("~"), ".freeflow", "history")
        os.makedirs(self._dir, exist_ok=True)
        self._lock = threading.Lock()

    def _day_file(self, d: date = None) -> str:
        d = d or date.today()
        return os.path.join(self._dir, f"{d.isoformat()}.json")

    def _load_day(self, path: str) -> list[dict]:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            # File corrupted — quarantine it and start fresh for the day.
            try:
                corrupt_path = f"{path}.corrupt-{int(time.time())}"
                os.rename(path, corrupt_path)
                print(
                    f"[history] corrupted file {path!r} renamed to {corrupt_path!r}: {e}",
                    file=sys.stderr,
                )
            except OSError as rename_err:
                print(
                    f"[history] could not rename corrupted file {path!r}: {rename_err}",
                    file=sys.stderr,
                )
            return []

    def _save_day(self, path: str, entries: list[dict]):
        # Atomic write: stage to .tmp, then os.replace() — survives a crash mid-write.
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def save(self, text: str, duration_seconds: float = 0) -> dict:
        entry = {
            "id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "duration_seconds": round(duration_seconds, 2),
            "app": _get_foreground_window_title(),
        }
        path = self._day_file()
        with self._lock:
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

    # ── Aggregated word counts per day for the chart ────────────────────
    def get_word_count_per_day(self, days: int = 30) -> list:
        """Return last `days` days as [{date, words, count}], oldest first.

        Days with zero activity are included so the chart x-axis is continuous.
        """
        today = date.today()
        buckets = {}
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            buckets[d.isoformat()] = {"date": d.isoformat(), "words": 0, "count": 0}

        for entry in self.get_all():
            ts = entry.get("timestamp", "")
            day_key = ts[:10]  # 'YYYY-MM-DD'
            if day_key in buckets:
                words = len((entry.get("text") or "").split())
                buckets[day_key]["words"] += words
                buckets[day_key]["count"] += 1

        return list(buckets.values())

    # ── Extended stats for the Main Window header ──────────────────────
    def get_extended_stats(self) -> dict:
        """Stats: total dictations, total words, week words, minutes saved (at 40 wpm)."""
        all_e = self.get_all()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        week_words = 0
        week_count = 0
        for e in all_e:
            try:
                d = datetime.fromisoformat(e.get("timestamp", "")).date()
            except Exception:
                continue
            if d >= week_start:
                week_words += len((e.get("text") or "").split())
                week_count += 1

        total_words = sum(len((e.get("text") or "").split()) for e in all_e)
        minutes_saved = round(total_words / 40)

        return {
            "total_dictations": len(all_e),
            "total_words": total_words,
            "week_words": week_words,
            "week_dictations": week_count,
            "minutes_saved": minutes_saved,
        }

    # ── Yearly heatmap (GitHub-style 365-day grid) ─────────────────────
    def get_yearly_heatmap(self, end_date: Optional[date] = None) -> list[dict]:
        """365 most recent days, [{date: 'YYYY-MM-DD', count: int, words: int}].

        Used by the GitHub-style heatmap. end_date defaults to today.
        """
        end = end_date or date.today()
        buckets = {}
        for i in range(364, -1, -1):
            d = end - timedelta(days=i)
            buckets[d.isoformat()] = {"date": d.isoformat(), "count": 0, "words": 0}

        for entry in self.get_all():
            day_key = (entry.get("timestamp") or "")[:10]
            if day_key in buckets:
                words = len((entry.get("text") or "").split())
                buckets[day_key]["count"] += 1
                buckets[day_key]["words"] += words

        return list(buckets.values())

    # ── Streaks ────────────────────────────────────────────────────────
    def get_streak(self) -> dict:
        """{current: int, longest: int} — consecutive days with ≥1 dictation.

        Current = streak ending today; longest = max all-time.
        """
        days_with_activity = set()
        for entry in self.get_all():
            day_key = (entry.get("timestamp") or "")[:10]
            if day_key:
                days_with_activity.add(day_key)

        if not days_with_activity:
            return {"current": 0, "longest": 0}

        # Current streak: walk back from today
        today = date.today()
        current = 0
        d = today
        while d.isoformat() in days_with_activity:
            current += 1
            d = d - timedelta(days=1)

        # Longest streak: sort all active days, find max consecutive run
        sorted_days = sorted(
            datetime.fromisoformat(s).date() for s in days_with_activity
        )
        longest = 1
        run = 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                run += 1
                longest = max(longest, run)
            else:
                run = 1
        longest = max(longest, current)

        return {"current": current, "longest": longest}

    # ── Hourly distribution (24h clock) ────────────────────────────────
    def get_hourly_distribution(self) -> list[int]:
        """24-element list: counts at each hour aggregated across all dictations."""
        bins = [0] * 24
        for entry in self.get_all():
            ts = entry.get("timestamp") or ""
            try:
                h = datetime.fromisoformat(ts).hour
                bins[h] += 1
            except Exception:
                continue
        return bins

    # ── App breakdown (top N) ──────────────────────────────────────────
    def get_app_breakdown(self, top_n: int = 5) -> list[dict]:
        """[{app: str, count: int, words: int}] for top_n apps by count desc.

        Excludes self-dictations into FreeFlow's own windows (circular and
        misleading), filesystem paths, and obviously-broken titles — they
        all bucket as '— autres —'.
        """
        def _classify(raw: str) -> "str | None":
            """Return canonical app name, or None to SKIP entry entirely."""
            low = raw.lower()
            # Skip self-dictations entirely (circular, not meaningful).
            if "freeflow" in low or "free flow" in low or "wispr" in low:
                return None
            if not raw or low == "unknown":
                return "— autres —"
            # Filesystem paths → group as "Système"
            if (len(raw) >= 3 and raw[1:3] == ":\\") or raw.startswith("/"):
                return "Système"
            # Weird control-char-style prefix (e.g. "※ Load certification…")
            if raw[:1] in {"※", "​", "﻿"}:
                return "— autres —"
            return raw

        bucket: dict[str, dict] = {}
        for entry in self.get_all():
            raw = (entry.get("app") or "").strip()
            key = _classify(raw)
            if key is None:
                continue  # FreeFlow itself — skip
            b = bucket.setdefault(key, {"app": key, "count": 0, "words": 0})
            b["count"] += 1
            b["words"] += len((entry.get("text") or "").split())

        ordered = sorted(bucket.values(), key=lambda x: x["count"], reverse=True)
        return ordered[:top_n]

    # ── Best dictation of the current week ─────────────────────────────
    def get_best_dictation_this_week(self) -> "dict | None":
        """Most notable dictation of current week (Mon-Sun): longest words,
        tiebreak on duration. Returns {id, timestamp, text, words, app,
        duration} or None if empty.
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        best = None
        best_words = -1
        best_dur = -1.0
        for entry in self.get_all():
            try:
                d = datetime.fromisoformat(entry.get("timestamp", "")).date()
            except Exception:
                continue
            if d < week_start:
                continue
            words = len((entry.get("text") or "").split())
            dur = float(entry.get("duration_seconds") or 0)
            if words > best_words or (words == best_words and dur > best_dur):
                best_words = words
                best_dur = dur
                best = entry

        if not best:
            return None
        return {
            "id": best.get("id"),
            "timestamp": best.get("timestamp"),
            "text": best.get("text") or "",
            "words": best_words,
            "app": best.get("app") or "",
            "duration": float(best.get("duration_seconds") or 0),
        }

    # ── WPM stats ──────────────────────────────────────────────────────
    def get_wpm_stats(self) -> dict:
        """{avg_wpm: float, total_minutes_saved: int}.

        avg_wpm computed across dictations with duration > 0.5s.
        total_minutes_saved compares to a 40-wpm typing baseline.
        """
        total_words = 0
        total_minutes = 0.0
        for entry in self.get_all():
            dur = float(entry.get("duration_seconds") or 0)
            if dur <= 0.5:
                continue
            words = len((entry.get("text") or "").split())
            if words <= 0:
                continue
            total_words += words
            total_minutes += dur / 60.0

        if total_minutes <= 0 or total_words <= 0:
            return {"avg_wpm": 0.0, "total_minutes_saved": 0}

        avg_wpm = total_words / total_minutes
        if avg_wpm <= 0:
            return {"avg_wpm": 0.0, "total_minutes_saved": 0}

        minutes_saved = total_words * (1.0 / 40.0 - 1.0 / avg_wpm)
        return {
            "avg_wpm": round(avg_wpm, 1),
            "total_minutes_saved": max(0, int(round(minutes_saved))),
        }

    # ── Delete a single entry by id (used by the Supprimer button) ─────
    def delete_entry(self, entry_id) -> bool:
        """Remove one entry from its per-day JSON file. Returns True if removed.

        Storage pattern: one JSON file per day at self._dir/YYYY-MM-DD.json.
        Each entry has an 'id' field (uuid4 hex) set in save().
        """
        if not entry_id:
            return False
        target = str(entry_id)
        with self._lock:
            try:
                files = os.listdir(self._dir)
            except FileNotFoundError:
                return False
            for f in files:
                if not f.endswith(".json"):
                    continue
                path = os.path.join(self._dir, f)
                try:
                    entries = self._load_day(path)
                except Exception:
                    continue
                new_entries = [e for e in entries if str(e.get("id")) != target]
                if len(new_entries) != len(entries):
                    if new_entries:
                        self._save_day(path, new_entries)
                    else:
                        try:
                            os.remove(path)
                        except OSError:
                            self._save_day(path, new_entries)
                    return True
        return False
