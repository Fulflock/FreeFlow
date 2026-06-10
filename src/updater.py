"""FreeFlow auto-updater — polls GitHub Releases for new versions.

How it works (zero-server, free):
1. Benjamin pushes code to GitHub, tags a release `v0.X.Y`, uploads
   `FreeFlow-Setup.exe` as a release asset.
2. App starts → background thread waits 20s → calls GitHub Releases API
   (`/repos/<owner>/<repo>/releases/latest`).
3. If `tag_name` > `CURRENT_VERSION`: show a tkinter dialog
   "Mise à jour disponible — installer ?".
4. On accept: download Setup.exe to %TEMP%, launch it silently with
   `/CLOSEAPPLICATIONS /RESTARTAPPLICATIONS`, exit current process.
   Inno Setup replaces the binary and restarts the app.

Configuration via `config.json`:
- `update_check_enabled` (bool, default True)
- `github_repo` (str, e.g. "ruvnet/freeflow") — leave empty to disable
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from typing import Optional

# Bumped on every release. MUST match `MyAppVersion` in installer.iss
# and be tagged as `v0.X.Y` on GitHub.
CURRENT_VERSION = "0.1.2"

# Source of truth for the auto-updater. config.json can override via the
# `github_repo` key, but if it's missing/empty we fall back to this constant
# so the updater works out of the box without any user setup.
_FALLBACK_GITHUB_REPO = "Fulflock/FreeFlow"

# GitHub API: 60 unauth requests / hour / IP. We call ~1×/day, fine.
_API_TMPL = "https://api.github.com/repos/{repo}/releases/latest"
_USER_AGENT = f"FreeFlow-Updater/{CURRENT_VERSION}"
_CHECK_DELAY_SECONDS = 20   # wait before first check, let app fully boot
_CHECK_INTERVAL_HOURS = 24  # only one check per day


def _parse_version(v: str) -> tuple[int, ...]:
    """'v0.2.10' or '0.2.10' → (0, 2, 10). Bad input → (0,)."""
    cleaned = re.sub(r"[^\d.]", "", (v or "").lstrip("v"))
    parts = [p for p in cleaned.split(".") if p]
    try:
        return tuple(int(p) for p in parts) or (0,)
    except ValueError:
        return (0,)


def _is_newer(remote: str, local: str) -> bool:
    return _parse_version(remote) > _parse_version(local)


def _http_get_json(url: str, timeout: int = 8) -> Optional[dict]:
    """Single retry, never raises."""
    req = urllib.request.Request(url, headers={
        "User-Agent": _USER_AGENT,
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, TimeoutError, OSError):
        return None


def _http_download(url: str, dest: str, timeout: int = 60) -> bool:
    """Stream download to dest. Returns True on success."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError,
            TimeoutError, OSError):
        return False


def fetch_latest_release(repo: str) -> Optional[dict]:
    """Query GitHub for the latest release.

    Returns a normalized dict {tag, version, setup_url, body} or None.
    """
    if not repo or "/" not in repo:
        return None
    data = _http_get_json(_API_TMPL.format(repo=repo))
    if not data:
        return None
    tag = data.get("tag_name") or ""
    # Find the FreeFlow-Setup.exe asset
    setup_url = None
    for asset in (data.get("assets") or []):
        name = (asset.get("name") or "").lower()
        if name.endswith("setup.exe") and "freeflow" in name:
            setup_url = asset.get("browser_download_url")
            break
    if not setup_url:
        return None
    return {
        "tag": tag,
        "version": tag.lstrip("v"),
        "setup_url": setup_url,
        "body": data.get("body") or "",
    }


def _ask_user(title: str, message: str) -> bool:
    """Modal Yes/No via tkinter (runs in this thread, blocks)."""
    try:
        # Import inside the function to avoid loading tkinter for users
        # who disable the updater. tkinter is already imported by idle_bubble.
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        result = messagebox.askyesno(title, message, parent=root)
        root.destroy()
        return bool(result)
    except Exception:
        return False


def _install_update(setup_url: str, new_version: str) -> bool:
    """Download Setup.exe → launch installer silently → exit app.

    Returns True if launched (process will exit shortly). Returns False on
    download failure (app continues running).
    """
    tmp_path = os.path.join(
        tempfile.gettempdir(),
        f"FreeFlow-Setup-{new_version}.exe",
    )
    if not _http_download(setup_url, tmp_path, timeout=180):
        return False
    try:
        # /CLOSEAPPLICATIONS = ask Inno to wait for FreeFlow to close before
        # replacing files. /RESTARTAPPLICATIONS = relaunch after install.
        # /VERYSILENT = no UI. /SUPPRESSMSGBOXES = no error dialogs.
        subprocess.Popen(
            [
                tmp_path,
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/CLOSEAPPLICATIONS",
                "/RESTARTAPPLICATIONS",
            ],
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            close_fds=True,
        )
    except OSError:
        return False
    # Give the installer 1s to start, then quit ourselves so the installer
    # can replace files. Inno Setup will relaunch the new FreeFlow.exe.
    threading.Timer(1.0, lambda: os._exit(0)).start()
    return True


def _check_once(config: dict) -> None:
    """One full update-check cycle. Safe to call from a background thread."""
    repo = (config.get("github_repo") or _FALLBACK_GITHUB_REPO or "").strip()
    if not repo:
        return  # no repo configured → silently skip
    rel = fetch_latest_release(repo)
    if not rel:
        return
    if not _is_newer(rel["version"], CURRENT_VERSION):
        return  # already on the latest

    msg = (
        f"FreeFlow {rel['version']} est disponible "
        f"(tu es en {CURRENT_VERSION}).\n\n"
        f"L'installation prend ~30 secondes. "
        f"L'app se ferme, se met à jour, puis se relance toute seule.\n\n"
        f"Installer maintenant ?"
    )
    if _ask_user("Mise à jour FreeFlow", msg):
        _install_update(rel["setup_url"], rel["version"])


def start_background_check(config: dict) -> None:
    """Spawn the once-per-day update check in a daemon thread. Non-blocking."""
    if not config.get("update_check_enabled", True):
        return
    if not (config.get("github_repo") or _FALLBACK_GITHUB_REPO or "").strip():
        return  # nothing to check against

    def _loop():
        time.sleep(_CHECK_DELAY_SECONDS)
        while True:
            try:
                _check_once(config)
            except Exception:
                pass
            time.sleep(_CHECK_INTERVAL_HOURS * 3600)

    t = threading.Thread(target=_loop, daemon=True, name="freeflow-updater")
    t.start()
