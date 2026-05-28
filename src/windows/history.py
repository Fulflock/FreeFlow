"""FreeFlow History window — list past dictations from DictationHistory."""

import html as _html
from datetime import datetime, date, timedelta

import webview

from src.history import DictationHistory
from src.fonts import FONT_CSS


_BASE_CSS = """
__FONT_FACE_CSS__

:root {
  --c1: #ff5d8f;
  --c3: #a8e6cf;
  --c4: #c4e86b;
  --c5: #ffd166;
  --ink: #16140f;
  --paper: #fffdf7;
  --bg: #f4f0e8;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body {
  height: 100%;
  background: var(--bg);
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: var(--ink);
}
body { display: flex; flex-direction: column; }

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 22px 26px 8px;
  gap: 16px;
}
.title {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -.8px;
}
.title .count {
  background: var(--c5);
  border: 2px solid var(--ink);
  border-radius: 10px;
  padding: 0 8px;
  display: inline-block;
  transform: rotate(-2deg);
  box-shadow: 2px 2px 0 var(--ink);
  margin-right: 4px;
}
.subtitle {
  font-size: 13px;
  color: rgba(0,0,0,.65);
  margin-top: 6px;
}

.actions { display: flex; gap: 8px; }
.btn-outline {
  background: transparent;
  color: var(--ink);
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: 7px 14px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
.btn-outline:hover { background: var(--paper); }

.search-row {
  margin: 12px 26px 8px;
  background: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 14px;
  box-shadow: 3px 3px 0 var(--ink);
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.search-row .icon { font-size: 14px; color: rgba(0,0,0,.5); }
.search-row input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  font-size: 14px;
  padding: 4px 0;
  color: var(--ink);
}
.search-row input::placeholder { color: rgba(0,0,0,.4); }
.chips { display: flex; gap: 6px; padding-left: 10px; border-left: 1px solid rgba(0,0,0,.12); }
.chip {
  font-size: 11px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1.5px solid var(--ink);
  background: var(--bg);
  cursor: pointer;
  user-select: none;
}
.chip.active { background: var(--c1); color: var(--ink); }

.list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 26px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.entry {
  background: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 3px 3px 0 var(--ink);
}
.entry .head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 10px;
}
.entry .stamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgba(0,0,0,.6);
}
.entry .app-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  background: var(--c3);
  border: 1.5px solid var(--ink);
  border-radius: 6px;
  padding: 1px 8px;
  margin-right: 6px;
}
.entry .meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgba(0,0,0,.55);
  display: flex;
  align-items: center;
  gap: 8px;
}
.entry .text {
  font-size: 14px;
  line-height: 1.45;
  color: rgba(0,0,0,.88);
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.entry .row-actions { display: flex; gap: 6px; }
.btn-sm {
  background: var(--paper);
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: 4px 12px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  color: var(--ink);
}
.btn-sm:hover { background: var(--c5); }
.btn-sm.primary { background: var(--c4); }

.badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  background: var(--bg);
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  padding: 1px 8px;
}

/* Empty state */
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  color: rgba(0,0,0,.7);
}
.empty .bubble {
  width: 110px; height: 96px;
  margin-bottom: 16px;
}
.empty h3 {
  font-size: 22px;
  letter-spacing: -.5px;
  margin-bottom: 6px;
}
.empty p {
  font-size: 14px;
  color: rgba(0,0,0,.6);
  max-width: 360px;
  line-height: 1.5;
}
.empty .hint {
  margin-top: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  padding: 6px 12px;
  background: var(--paper);
  border: 2px solid var(--ink);
  border-radius: 999px;
  box-shadow: 2px 2px 0 var(--ink);
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,.18); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,.3); }
""".replace("__FONT_FACE_CSS__", FONT_CSS)


def _humanize_timestamp(iso_ts: str) -> str:
    """Convert an ISO timestamp into 'aujourd'hui · 14:32' etc."""
    try:
        dt = datetime.fromisoformat(iso_ts)
    except Exception:
        return iso_ts
    today = date.today()
    yesterday = today - timedelta(days=1)
    if dt.date() == today:
        prefix = "aujourd'hui"
    elif dt.date() == yesterday:
        prefix = "hier"
    else:
        prefix = dt.strftime("%d/%m/%Y")
    return f"{prefix} · {dt.strftime('%H:%M')}"


def _build_entries_html(entries: list) -> str:
    """Render dictation entries as HTML cards (newest first)."""
    if not entries:
        return ""

    # Newest first
    sorted_entries = sorted(
        entries,
        key=lambda e: e.get("timestamp", ""),
        reverse=True,
    )

    parts = []
    for e in sorted_entries:
        text = e.get("text", "")
        word_count = len(text.split()) if text else 0
        duration = e.get("duration_seconds", 0) or 0
        try:
            dur_str = f"{float(duration):.0f}s"
        except Exception:
            dur_str = "—"
        stamp = _humanize_timestamp(e.get("timestamp", ""))
        app_name = (e.get("app") or "—").strip() or "—"
        # Compact app name to first ~24 chars to keep the row tidy.
        if len(app_name) > 24:
            app_name = app_name[:21] + "…"

        parts.append(f"""
        <div class="entry">
          <div class="head">
            <div class="meta">
              <span class="app-name">{_html.escape(app_name)}</span>
              <span class="stamp">{_html.escape(stamp)}</span>
            </div>
            <div class="meta">
              <span class="badge">{word_count} mots</span>
              <span class="badge">{_html.escape(dur_str)}</span>
            </div>
          </div>
          <div class="text">{_html.escape(text)}</div>
          <div class="row-actions">
            <button class="btn-sm primary">⎘ Copier</button>
            <button class="btn-sm">↺ Renvoyer</button>
          </div>
        </div>
        """)
    return "\n".join(parts)


def _build_empty_state() -> str:
    """Friendly empty state with the FF bubble icon."""
    return """
    <div class="empty">
      <svg class="bubble" viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">
        <path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z"
              fill="#ff5d8f" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/>
        <g fill="#16140f">
          <path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/>
          <path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/>
        </g>
      </svg>
      <h3>Encore aucune dictée</h3>
      <p>Maintiens <b>Ctrl + Espace</b>, parle, lâche.<br>
         Ton premier essai apparaîtra ici, stocké en local.</p>
      <div class="hint">Ctrl + Espace</div>
    </div>
    """


def _build_html(entries: list) -> str:
    total_words = sum(len((e.get("text") or "").split()) for e in entries)
    has_entries = bool(entries)
    entries_section = (
        f'<div class="list">{_build_entries_html(entries)}</div>'
        if has_entries
        else _build_empty_state()
    )
    # Hide search bar in empty state (no point searching nothing).
    search_section = "" if not has_entries else """
    <div class="search-row">
      <span class="icon">🔍</span>
      <input id="search" placeholder="cherche dans tes dictées…" />
      <div class="chips">
        <span class="chip active" data-filter="all">Tout</span>
        <span class="chip" data-filter="today">Aujourd'hui</span>
        <span class="chip" data-filter="week">Cette semaine</span>
      </div>
    </div>
    """

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Historique — FreeFlow</title>
<style>{_BASE_CSS}</style>
</head>
<body>

<div class="topbar">
  <div>
    <div class="title"><span class="count">{len(entries)}</span> dictées</div>
    <div class="subtitle">{total_words} mots au total · stocké en local sur ta machine</div>
  </div>
  <div class="actions">
    <button class="btn-outline">↓ Exporter</button>
    <button class="btn-outline">🗑 Vider</button>
  </div>
</div>

{search_section}
{entries_section}

<script>
// Live search filter on the entries list.
var search = document.getElementById('search');
if (search) {{
  search.addEventListener('input', function(){{
    var q = search.value.toLowerCase();
    document.querySelectorAll('.entry').forEach(function(card){{
      var txt = card.textContent.toLowerCase();
      card.style.display = q && txt.indexOf(q) === -1 ? 'none' : '';
    }});
  }});
}}

// Filter chips (today / week / all)
document.querySelectorAll('.chip').forEach(function(chip){{
  chip.addEventListener('click', function(){{
    document.querySelectorAll('.chip').forEach(function(c){{ c.classList.remove('active'); }});
    chip.classList.add('active');
    // Filter logic placeholder — currently all chips show all entries.
    // Stamps are localized text so we keep this as a UI-only toggle.
  }});
}});
</script>
</body></html>"""


class HistoryWindow:
    """Standalone history window — reads entries via DictationHistory."""

    def __init__(self):
        self._window = None

    def _load_entries(self) -> list:
        try:
            return DictationHistory().get_all() or []
        except Exception:
            # If history is unreadable for any reason, render empty state.
            return []

    def open(self):
        entries = self._load_entries()
        html = _build_html(entries)
        self._window = webview.create_window(
            "Historique — FreeFlow",
            html=html,
            width=720,
            height=600,
            frameless=False,
            on_top=False,
            background_color="#f4f0e8",
        )
        return self._window
