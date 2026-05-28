"""Self-hosted fonts for FreeFlow — no CDN dependency.

Reads the .woff2 files bundled under src/assets/fonts/ at import time,
base64-encodes them, and exposes `FONT_CSS` — a `<style>`-ready string
containing the full @font-face declarations. Each HTML payload swaps the
Google Fonts @import for this constant so the app renders correctly
even with no internet (airplane mode, sandboxed env, first launch
behind a corporate proxy, etc.).
"""

import base64
import os
import sys
from pathlib import Path


def _fonts_dir() -> Path:
    """Locate src/assets/fonts/ whether we're running from source or a
    PyInstaller --onefile bundle (sys._MEIPASS)."""
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", ""))
        for cand in (
            meipass / "src" / "assets" / "fonts",
            meipass / "assets" / "fonts",
            meipass / "fonts",
        ):
            if cand.is_dir():
                return cand
    return Path(__file__).resolve().parent / "assets" / "fonts"


# Order matters: list once, derive @font-face for each.
_FONTS = [
    ("Space Grotesk", 400, "SpaceGrotesk-400-normal.woff2"),
    ("Space Grotesk", 500, "SpaceGrotesk-500-normal.woff2"),
    ("Space Grotesk", 600, "SpaceGrotesk-600-normal.woff2"),
    ("Space Grotesk", 700, "SpaceGrotesk-700-normal.woff2"),
    ("JetBrains Mono", 400, "JetBrainsMono-400-normal.woff2"),
    ("JetBrains Mono", 500, "JetBrainsMono-500-normal.woff2"),
    ("JetBrains Mono", 600, "JetBrainsMono-600-normal.woff2"),
    ("JetBrains Mono", 700, "JetBrainsMono-700-normal.woff2"),
]


def _build_css() -> str:
    parts = []
    base = _fonts_dir()
    for family, weight, fname in _FONTS:
        path = base / fname
        if not path.exists():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        b64 = base64.b64encode(data).decode("ascii")
        parts.append(
            f"@font-face{{font-family:'{family}';font-style:normal;"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
        )
    return "\n".join(parts)


# Built once at import — kept in memory for the rest of the process.
FONT_CSS: str = _build_css()
