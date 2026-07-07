"""FreeFlow configuration — load/save with a user-writable override layer.

Two layers, merged at load time (later wins):
  1. DEFAULTS         — hard-coded baseline below.
  2. bundled config   — config.json shipped next to the exe (read-only baseline
                        the packager can tweak). Optional.
  3. user config      — ~/.freeflow/config.json — the ONLY file we ever write.
                        Created on first save. Survives reinstalls/upgrades.

The running app reads the merged result. The Settings window writes user
overrides via save_config(). Most settings take effect on next launch; the
"launch at startup" toggle is applied immediately by writing/removing a
Startup-folder shortcut.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

# ── Paths ────────────────────────────────────────────────────────────────────
_USER_DIR = os.path.join(os.path.expanduser("~"), ".freeflow")
USER_CONFIG_PATH = os.path.join(_USER_DIR, "config.json")

# ── Baseline ─────────────────────────────────────────────────────────────────
DEFAULTS: dict = {
    "hotkey_combo": ["ctrl", "space"],
    "language": "fr",
    "model_size": "base",
    "overlay_position": "bottom_right",
    "overlay_opacity": 0.85,
    "update_check_enabled": True,
    "github_repo": "",
    # New in 0.1.1 — surfaced by the Settings window:
    "launch_at_startup": False,
    "auto_punctuation": True,
    # Custom dictionary: words/names FreeFlow should recognize better
    # (proper nouns, jargon, brand names). Passed to Whisper as "hotwords".
    "custom_words": [],
    # Voice snippets: say the trigger phrase → it expands to the full text.
    # Each item is {"trigger": "...", "expansion": "..."}.
    "snippets": [],
    # Max length of a single dictation, in seconds (safety cap for a stuck key).
    # 300 = 5 min. Raise it if you dictate very long monologues.
    "max_dictation_seconds": 300,
}

# Keys the Settings window is allowed to write. Anything else is ignored on
# save so a malformed/hostile payload can't inject arbitrary config.
_SETTABLE_KEYS = {
    "hotkey_combo", "language", "model_size", "overlay_opacity",
    "launch_at_startup", "auto_punctuation", "update_check_enabled",
    "custom_words", "snippets", "max_dictation_seconds",
}


def _bundled_base_path() -> str:
    """Directory holding the bundled config.json (next to exe, or repo root)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_config() -> dict:
    """Return the merged config: DEFAULTS <- bundled <- user overrides."""
    cfg = dict(DEFAULTS)

    base = _bundled_base_path()
    for candidate in (
        os.path.join(base, "config.json"),
        os.path.join(base, "_internal", "config.json"),
    ):
        if os.path.exists(candidate):
            cfg.update(_read_json(candidate))
            break

    if os.path.exists(USER_CONFIG_PATH):
        cfg.update(_read_json(USER_CONFIG_PATH))

    return cfg


def _atomic_write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def save_config(updates: dict) -> dict:
    """Merge `updates` (whitelisted keys only) into the USER config file.

    Returns the new fully-merged config. Side effect: if `launch_at_startup`
    changed, the Startup shortcut is created/removed immediately.
    """
    clean = {k: v for k, v in (updates or {}).items() if k in _SETTABLE_KEYS}

    # Start from whatever the user has already overridden (not the merged view),
    # so we never accidentally bake DEFAULTS/bundled values into the user file.
    user = _read_json(USER_CONFIG_PATH)
    user.update(clean)
    _atomic_write(USER_CONFIG_PATH, user)

    if "launch_at_startup" in clean:
        try:
            set_launch_at_startup(bool(clean["launch_at_startup"]))
        except Exception:
            pass  # best-effort; persisted either way

    return load_config()


# ── Launch-at-startup (Windows Startup-folder shortcut, no admin) ────────────
def _startup_shortcut_path() -> str:
    appdata = os.environ.get("APPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Roaming"
    )
    return os.path.join(
        appdata, "Microsoft", "Windows", "Start Menu",
        "Programs", "Startup", "FreeFlow.lnk",
    )


def _app_exe_path() -> str | None:
    """Path to the installed FreeFlow.exe, or None when running from source."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return None


def set_launch_at_startup(enabled: bool) -> bool:
    """Create or remove the Startup-folder shortcut. Returns True on success.

    The shortcut launches FreeFlow with --silent so it boots straight to the
    tray without popping the main window on every login.
    """
    link = _startup_shortcut_path()

    if not enabled:
        try:
            if os.path.exists(link):
                os.remove(link)
            return True
        except OSError:
            return False

    exe = _app_exe_path()
    if not exe or not os.path.exists(exe):
        # Running from source (dev) — nothing meaningful to register.
        return False
    try:
        import win32com.client  # provided by pywin32, already bundled

        shell = win32com.client.Dispatch("WScript.Shell")
        sc = shell.CreateShortcut(link)
        sc.TargetPath = exe
        sc.Arguments = "--silent"
        sc.WorkingDirectory = os.path.dirname(exe)
        sc.IconLocation = exe
        sc.Description = "FreeFlow — dictée vocale locale"
        sc.Save()
        return True
    except Exception:
        return False


def is_launch_at_startup() -> bool:
    return os.path.exists(_startup_shortcut_path())
