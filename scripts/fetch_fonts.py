"""Fetch Space Grotesk + JetBrains Mono .woff2 files from Google Fonts.

Run once to populate src/assets/fonts/. The runtime then reads these files
locally — no CDN dependency, FreeFlow works fully offline.
"""
import re
import urllib.request
from pathlib import Path

CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Space+Grotesk:wght@400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500;600;700"
    "&display=swap"
)

# Google serves different CSS to different User-Agents. Chrome UA → modern woff2.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

OUT_DIR = Path(__file__).resolve().parents[1] / "src" / "assets" / "fonts"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def main():
    css = fetch(CSS_URL).decode("utf-8", errors="replace")
    # Extract every @font-face block.
    blocks = re.findall(r"@font-face\s*{[^}]+}", css)
    print(f"Found {len(blocks)} @font-face blocks")

    saved = 0
    for block in blocks:
        family_m = re.search(r"font-family:\s*'([^']+)'", block)
        weight_m = re.search(r"font-weight:\s*(\d+)", block)
        style_m = re.search(r"font-style:\s*(\w+)", block)
        url_m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        unicode_m = re.search(r"unicode-range:\s*([^;]+);", block)
        if not (family_m and weight_m and url_m):
            continue

        family = family_m.group(1).replace(" ", "")
        weight = weight_m.group(1)
        style = (style_m.group(1) if style_m else "normal")
        url = url_m.group(1)
        urange = (unicode_m.group(1).strip() if unicode_m else "")
        # Only keep latin (skip vietnamese/cyrillic subsets to save weight).
        if urange and "U+0000-00FF" not in urange and "U+0100-017F" not in urange:
            # Google's "latin" range typically starts at U+0000-00FF; skip others.
            continue

        fname = f"{family}-{weight}-{style}.woff2"
        out = OUT_DIR / fname
        if out.exists():
            print(f"  skip {fname} (already exists)")
            saved += 1
            continue
        print(f"  fetching {fname} ...", end=" ", flush=True)
        data = fetch(url)
        out.write_bytes(data)
        print(f"{len(data)} bytes")
        saved += 1

    print(f"\nDone. {saved} font files in {OUT_DIR}")


if __name__ == "__main__":
    main()
