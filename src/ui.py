"""FreeFlow UI — pywebview overlay with sticker-pack design."""

import ctypes
import math
import os
import threading
import time

from PIL import Image, ImageDraw
import pystray
import webview

from src.idle_bubble import IdleBubble
from src.fonts import FONT_CSS
from src.windows.settings import SettingsWindow
from src.windows.history import HistoryWindow
from src.windows.onboarding import OnboardingWindow, is_onboarding_done


# ── Screen metrics ─────────────────────────────────────────────────────────
# Important: pywebview expects LOGICAL (DIP) pixels for x/y/width/height on
# Windows. GetSystemMetrics returns PHYSICAL pixels because IdleBubble already
# made the process DPI-aware. We must convert to logical pixels by dividing
# by the DPI scale factor — otherwise overlays land off-screen on hi-DPI displays.
_user32 = ctypes.windll.user32

def _dpi_scale():
    try:
        # User-default DPI for the primary display; 96 = 100%, 192 = 200%, etc.
        dpi = ctypes.windll.user32.GetDpiForSystem()
        return max(dpi / 96.0, 1.0)
    except Exception:
        return 1.0

_DPI = _dpi_scale()
SCREEN_W = int(_user32.GetSystemMetrics(0) / _DPI)   # logical pixels
SCREEN_H = int(_user32.GetSystemMetrics(1) / _DPI)   # logical pixels

# Window sizes per state (width, height) — must be ≥ natural bar height
# so the pink-bordered bar fills edge-to-edge with no dark gap around it.
_SIZES = {
    "idle":       (54, 50),
    "listen":     (360, 54),
    "transcribe": (360, 54),
    "result":     (300, 150),
    "pasted":     (150, 44),
}


def _center_bottom(state):
    """Return (x, y) for bottom-center placement above taskbar."""
    w, h = _SIZES[state]
    return (SCREEN_W - w) // 2, SCREEN_H - h - 80


def _wave_bars(n=32):
    """Generate waveform bar HTML spans (heights set live by setAmp via JS)."""
    return "".join(f'<span data-i="{i}" style="height:4px"></span>' for i in range(n))


# ── HTML overlay ───────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
__FONT_FACE_CSS__

:root {
  --c1: #ff5d8f;
  --c3: #a8e6cf;
  --c4: #c4e86b;
  --ink: #16140f;
  --paper: #fffdf7;
  --bg: #f4f0e8;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body {
  background: #fffdf7;            /* paper — bar bg matches so no margin shows */
  overflow: hidden;
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  user-select: none;
  -webkit-user-select: none;
}

#container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
}

.state { display: none; }
.state.active { display: block; width: 100%; height: 100%; }
/* Idle state still needs flex centering for the bubble */
#s-idle.active { display: flex; align-items: center; justify-content: center; }

/* Smooth fade + slide-in for the active states */
@keyframes slide-up-in {
  from { transform: translateY(8px); opacity: 0; }
  to   { transform: translateY(0);   opacity: 1; }
}
.state.active .listen-bar,
.state.active .transcribe-bar,
.state.active .result-card,
.state.active .pasted-card {
  animation: slide-up-in 180ms ease-out both;
}

/* ── IDLE ────────────────────────────────────────────── */
#s-idle {
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  animation: idle-float 3s ease-in-out infinite;
}
@keyframes idle-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* ── LISTEN ──────────────────────────────────────────── */
.listen-bar {
  width: 100%;
  height: 100%;
  padding: 8px 14px;
  border-radius: 0;
  background: var(--paper);
  border-left: 5px solid var(--c1);
  border-right: 5px solid var(--c1);
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
}

.mic-circle {
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--c1); border: 2.5px solid var(--ink);
  display: grid; place-items: center; flex-shrink: 0;
  box-shadow: 0 0 0 6px rgba(255,93,143,.25);
  animation: pulse-ring 1.4s infinite;
}
@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 6px rgba(255,93,143,.25); }
  50% { box-shadow: 0 0 0 12px rgba(255,93,143,.05); }
}

.listen-info { flex: 1; min-width: 0; }
.listen-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.listen-label { font-size: 14px; font-weight: 600; color: var(--ink); }
.listen-timer {
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 11px; color: rgba(22,20,15,.5); margin-left: auto;
}

.waveform { display: flex; align-items: center; gap: 2px; height: 26px; }
.waveform span {
  display: inline-block;
  width: 3px;
  background: var(--c1);
  border-radius: 2px;
  transition: height 60ms linear;
  min-height: 3px;
}

.listen-hint {
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 10px; color: rgba(22,20,15,.55);
  text-align: right; flex-shrink: 0;
}
.pill-key {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(22,20,15,.06);
  border: 1px solid rgba(22,20,15,.2);
  border-radius: 6px;
  color: var(--ink);
  font-size: 10px;
  margin-top: 2px;
}

/* ── TRANSCRIBE ──────────────────────────────────────── */
.transcribe-bar {
  width: 100%;
  height: 100%;
  padding: 8px 14px;
  border-radius: 0;
  background: var(--paper);
  border-left: 5px solid var(--c1);
  border-right: 5px solid var(--c1);
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
}

.dots-circle {
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--c1); border: 2.5px solid var(--ink);
  display: flex; align-items: center; justify-content: center;
  gap: 3px; flex-shrink: 0;
}
.dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--ink);
  animation: bounce 0.9s infinite;
}
.dot:nth-child(2) { animation-delay: 150ms; }
.dot:nth-child(3) { animation-delay: 300ms; }
@keyframes bounce {
  0%, 100% { transform: translateY(0); opacity: .4; }
  50% { transform: translateY(-4px); opacity: 1; }
}

.transcribe-info { flex: 1; }
.transcribe-label { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.transcribe-meta {
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 11px; color: rgba(0,0,0,.55);
}

.pill-local {
  display: inline-block;
  padding: 4px 10px;
  background: var(--bg);
  border: 2px solid var(--ink);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
}

/* ── RESULT ──────────────────────────────────────────── */
.result-card {
  width: 100%;
  padding: 12px;
  border-radius: 18px;
  background: var(--paper);
  border: 2.5px solid var(--ink);
}
.result-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.check-circle {
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--c4); border: 1.5px solid var(--ink);
  display: grid; place-items: center;
  font-size: 11px; font-weight: 700;
}
.result-status { font-size: 12px; font-weight: 600; }
.result-words {
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 9px; color: rgba(0,0,0,.5); margin-left: auto;
}

.result-text {
  padding: 8px 10px;
  background: var(--bg);
  border: 1.5px dashed var(--ink);
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.4;
  color: rgba(0,0,0,.85);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-footer {
  display: flex; gap: 6px; margin-top: 8px; align-items: center;
}
.btn-sm {
  background: var(--paper);
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: 5px 12px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: default;
  pointer-events: none;
}
.esc-hint {
  margin-left: auto;
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 9px; color: rgba(0,0,0,.5);
}

/* ── PASTED ──────────────────────────────────────────── */
.pasted-card {
  padding: 12px 20px;
  border-radius: 16px;
  background: var(--c4);
  border: 2.5px solid var(--ink);
  box-shadow: 3px 3px 0 var(--ink);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  animation: pasted-pop 0.3s ease-out;
}
.check-big {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--paper); border: 2px solid var(--ink);
  display: grid; place-items: center;
  font-size: 13px; font-weight: 700;
}
@keyframes pasted-pop {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
</head>
<body>
<div id="container">

  <!-- IDLE: floating pink FF speech bubble -->
  <div id="s-idle" class="state active">
    <svg width="38" height="34" viewBox="0 0 64 56"
         style="filter: drop-shadow(0 4px 10px rgba(255,93,143,.55));">
      <path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z"
            fill="var(--c1)" stroke="var(--ink)" stroke-width="2.5" stroke-linejoin="round"/>
      <g fill="var(--ink)">
        <path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/>
        <path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/>
      </g>
      <g fill="var(--ink)">
        <circle cx="49" cy="12" r="1.4"/>
        <circle cx="53" cy="12" r="1" opacity=".6"/>
      </g>
    </svg>
  </div>

  <!-- LISTEN: dark recording bar -->
  <div id="s-listen" class="state">
    <div class="listen-bar">
      <div class="mic-circle">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <rect x="9" y="3" width="6" height="14" rx="3" fill="#fff"/>
          <path d="M5 11v1a7 7 0 0014 0v-1M12 19v3" stroke="#fff" stroke-width="2"
                stroke-linecap="round" fill="none"/>
        </svg>
      </div>
      <div class="listen-info">
        <div class="listen-top">
          <span class="listen-label">écoute…</span>
          <span class="listen-timer" id="timer">00:00:00</span>
        </div>
        <div class="waveform">__WAVE_BARS__</div>
      </div>
      <div class="listen-hint">
        lâche<br><span class="pill-key">Ctrl+␣</span>
      </div>
    </div>
  </div>

  <!-- TRANSCRIBE: light processing bar -->
  <div id="s-transcribe" class="state">
    <div class="transcribe-bar">
      <div class="dots-circle">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
      <div class="transcribe-info">
        <div class="transcribe-label">transcription…</div>
        <div class="transcribe-meta">whisper-small · local</div>
      </div>
      <span class="pill-local">&#129504; local</span>
    </div>
  </div>

  <!-- RESULT: compact card -->
  <div id="s-result" class="state">
    <div class="result-card">
      <div class="result-header">
        <span class="check-circle">&#10003;</span>
        <span class="result-status">prêt — clique où tu veux</span>
        <span class="result-words" id="result-words">0 mots</span>
      </div>
      <div class="result-text" id="result-text"></div>
      <div class="result-footer">
        <button class="btn-sm">&#8634; refaire</button>
        <button class="btn-sm">&#9998; éditer</button>
        <span class="esc-hint">&#8617; esc</span>
      </div>
    </div>
  </div>

  <!-- PASTED: brief confirmation -->
  <div id="s-pasted" class="state">
    <div class="pasted-card">
      <span class="check-big">&#10003;</span>
      <span>collé !</span>
    </div>
  </div>

</div>

<script>
var _timerInterval = null;
var _timerStart = 0;

function setState(state, data) {
  // Stop timer if leaving listen state
  if (_timerInterval) {
    clearInterval(_timerInterval);
    _timerInterval = null;
  }

  // Hide all states
  var states = document.querySelectorAll('.state');
  for (var i = 0; i < states.length; i++) {
    states[i].classList.remove('active');
  }

  // Show requested state
  var ids = {
    idle: 's-idle',
    listen: 's-listen',
    transcribe: 's-transcribe',
    result: 's-result',
    pasted: 's-pasted'
  };
  var el = document.getElementById(ids[state]);
  if (el) el.classList.add('active');

  // Start timer for listen state
  if (state === 'listen') {
    _timerStart = Date.now();
    document.getElementById('timer').textContent = '00:00:00';
    _timerInterval = setInterval(function() {
      var elapsed = Math.floor((Date.now() - _timerStart) / 1000);
      var h = String(Math.floor(elapsed / 3600)).padStart(2, '0');
      var m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
      var s = String(elapsed % 60).padStart(2, '0');
      document.getElementById('timer').textContent = h + ':' + m + ':' + s;
    }, 1000);
  }

  // Set result text
  if (state === 'result' && data) {
    document.getElementById('result-text').textContent = data;
    var words = data.trim().split(/\\s+/).length;
    document.getElementById('result-words').textContent = words + ' mots';
  }
}

// Live waveform: setAmp(amp) is called from Python ~20x/s while recording.
// `amp` is 0.0–1.0 (RMS, gain-compensated). We use it + per-bar phase to
// produce an organic, audio-reactive waveform — never a repeating loop.
// Bell-curve waveform: bars peak at the center, fall off toward the edges,
// the whole envelope scaled by the actual voice amplitude. Adds a gentle
// time-based ripple so it feels alive even at constant volume — no random
// noise (that's what made the previous version feel "bizarre").
var _ampSmooth = 0;
function setAmp(amp) {
  var bars = document.querySelectorAll('.waveform span');
  var n = bars.length;
  if (!n) return;
  // Smooth amp: fast attack (catch peaks), slower decay (no flicker).
  if (amp > _ampSmooth) {
    _ampSmooth = _ampSmooth * 0.15 + amp * 0.85;
  } else {
    _ampSmooth = _ampSmooth * 0.65 + amp * 0.35;
  }
  var maxH = 26;
  var ts = Date.now() / 130;
  for (var i = 0; i < n; i++) {
    // Bell shape: 0 at edges, 1 at center.
    var x = (i / (n - 1)) * Math.PI;
    var bell = Math.sin(x);
    bell = bell * bell;                       // sharpen the peak
    // Gentle traveling ripple — gives life without looking mechanical.
    var ripple = 0.75 + 0.25 * Math.sin(ts + i * 0.35);
    var h = Math.max(2, _ampSmooth * maxH * bell * ripple * 1.6);
    bars[i].style.height = h.toFixed(1) + 'px';
  }
}
</script>
</body></html>""".replace("__WAVE_BARS__", _wave_bars(32)).replace("__FONT_FACE_CSS__", FONT_CSS)


# ── Tray icon ──────────────────────────────────────────────────────────────
class TrayIcon:
    COLORS = {
        "ready": "#ff5d8f",
        "recording": "#ff8c00",
        "transcribing": "#a8e6cf",
    }

    def __init__(self, on_quit, on_settings=None, on_history=None, on_onboarding=None, on_main=None):
        self._on_quit = on_quit
        self._on_settings = on_settings or (lambda: None)
        self._on_history = on_history or (lambda: None)
        self._on_onboarding = on_onboarding or (lambda: None)
        self._on_main = on_main or (lambda: None)
        self._icon = None

    @staticmethod
    def _make_icon(color):
        """Create a tray icon with the FF branding.

        Cream "FF" on a colored rounded square — matches assets/freeflow.ico
        (same brand language) but lets us recolor the background per state
        (pink=ready, orange=recording, mint=transcribing).
        """
        ff_color = "#fffdf7"   # cream — matches the .ico
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Rounded square background
        d.rounded_rectangle([4, 4, 60, 60], radius=14, fill=color, outline="#16140f", width=2)
        # "ff" mark (simplified) — cream so it pops against the colored bg
        d.rectangle([18, 20, 22, 44], fill=ff_color)
        d.rectangle([18, 20, 30, 24], fill=ff_color)
        d.rectangle([18, 30, 28, 34], fill=ff_color)
        d.rectangle([34, 20, 38, 44], fill=ff_color)
        d.rectangle([34, 20, 46, 24], fill=ff_color)
        d.rectangle([34, 30, 44, 34], fill=ff_color)
        return img

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem("Ouvrir FreeFlow", lambda: self._on_main(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("FreeFlow", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Historique", lambda: self._on_history()),
            pystray.MenuItem("Réglages", lambda: self._on_settings()),
            pystray.MenuItem("Bienvenue", lambda: self._on_onboarding()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quitter", lambda: self._on_quit()),
        )
        self._icon = pystray.Icon(
            "freeflow",
            self._make_icon(self.COLORS["ready"]),
            "FreeFlow",
            menu,
        )
        threading.Thread(target=self._icon.run, daemon=True).start()

    def set_state(self, state):
        if self._icon:
            self._icon.icon = self._make_icon(
                self.COLORS.get(state, self.COLORS["ready"])
            )

    def stop(self):
        if self._icon:
            self._icon.stop()


# ── Main UI class ──────────────────────────────────────────────────────────
class FreeFlowUI:
    def __init__(self, opacity=0.85, on_quit=None, amp_provider=None):
        self._external_quit = on_quit
        self._opacity = opacity
        self._window = None
        self._ready = threading.Event()
        # Audio-reactive waveform: a callable returning current RMS amp (0..1).
        # main.py wires this to AudioRecorder.get_current_amplitude.
        self._amp_provider = amp_provider or (lambda: 0.0)
        self._amp_polling = False
        self.tray = TrayIcon(
            on_quit=self.quit,
            on_settings=self.open_settings,
            on_history=self.open_history,
            on_onboarding=self.open_onboarding,
            on_main=self.open_main_window,
        )
        # Floating FF bubble (tkinter) — replaces the pywebview idle window.
        self.bubble = IdleBubble(gap_above_taskbar=110)
        # Secondary windows (opened on demand).
        self._settings_win = None
        self._history_win = None
        self._onboarding_win = None

    def start(self):
        """Start the UI main loop (blocks)."""
        self.tray.start()
        # Start the floating bubble BEFORE webview.start() (which blocks).
        try:
            self.bubble.start()
        except Exception:
            import traceback
            traceback.print_exc()
        x, y = _center_bottom("idle")
        w, h = _SIZES["idle"]
        self._window = webview.create_window(
            "FreeFlow",
            html=_HTML,
            width=w,
            height=h,
            x=x,
            y=y,
            frameless=True,
            on_top=True,
            background_color="#fffdf7",
            min_size=(40, 12),
        )

        def _on_start():
            # Give the page time to load before allowing JS calls
            time.sleep(1.5)
            self._ready.set()
            # Warm up the JS bridge (first call takes ~3s)
            try:
                self._window.evaluate_js("1+1")
            except Exception:
                pass
            # Hide the pywebview overlay — the tkinter bubble owns the idle state.
            try:
                self._window.hide()
            except Exception:
                pass
            # Show the floating FF bubble as the idle indicator.
            try:
                self.bubble.show()
            except Exception:
                pass
            # First-launch onboarding.
            try:
                if not is_onboarding_done():
                    self.open_onboarding()
            except Exception:
                import traceback
                traceback.print_exc()

        webview.start(func=_on_start, debug=False)

    # ── Secondary windows ─────────────────────────────────────────────────
    def open_settings(self):
        """Open the Réglages window (creates a new pywebview window)."""
        try:
            self._settings_win = SettingsWindow()
            self._settings_win.open()
        except Exception:
            import traceback
            traceback.print_exc()

    def open_history(self):
        """Open the Historique window (fresh load each time)."""
        try:
            self._history_win = HistoryWindow()
            self._history_win.open()
        except Exception:
            import traceback
            traceback.print_exc()

    def open_onboarding(self):
        """Open the Bienvenue (onboarding) window."""
        try:
            self._onboarding_win = OnboardingWindow()
            self._onboarding_win.open()
        except Exception:
            import traceback
            traceback.print_exc()

    def open_main_window(self):
        """Open the FreeFlow main window (history + chart). Runs in a thread."""
        from src.windows.main_window import MainWindow
        def _open():
            try:
                mw = MainWindow()
                mw.open()
            except Exception:
                import traceback
                traceback.print_exc()
        # pywebview create_window is fine to call from any thread; the window
        # registers with the existing webview loop.
        import threading
        threading.Thread(target=_open, daemon=True).start()

    def _js(self, code):
        """Safely evaluate JavaScript in the overlay."""
        if not self._window:
            return
        if not self._ready.is_set():
            return
        try:
            self._window.evaluate_js(code)
        except Exception:
            import traceback
            traceback.print_exc()

    def _resize(self, state):
        """Resize and reposition the overlay window for a given state."""
        if not self._window:
            return
        w, h = _SIZES[state]
        x, y = _center_bottom(state)
        try:
            self._window.resize(w, h)
            self._window.move(x, y)
        except Exception:
            pass

    def _show_window(self):
        """Reveal the overlay window (was hidden when idle)."""
        if not self._window:
            return
        try:
            self._window.show()
        except Exception:
            pass

    def _show_state(self, state, data=None):
        """Render an active state smoothly.

        Order matters to avoid the flash of stale content:
          1. hide the floating bubble
          2. resize + move the overlay window WHILE STILL HIDDEN
          3. setState in the DOM (CSS animation triggers on `.active`)
          4. tiny delay so layout/paint can settle
          5. show the window — the bar slides up cleanly
        """
        # 1) Bubble out of the way (tkinter call, marshalled to its main loop).
        try:
            self.bubble.hide()
        except Exception:
            pass

        # 2) Resize/move while the window is still hidden.
        self._resize(state)

        # 3) Push the new state into the DOM.
        if state == "result" and data is not None:
            safe = data.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
            self._js(f"setState('result','{safe}')")
        else:
            self._js(f"setState('{state}')")

        # 4) Let the DOM update / animation arm before revealing the window.
        time.sleep(0.03)

        # 5) Reveal — animation plays on the freshly-rendered content.
        self._show_window()

    def show_recording(self):
        self._show_state("listen")
        self.tray.set_state("recording")
        self._start_amp_poll()

    def show_transcribing(self):
        self._stop_amp_poll()
        self._show_state("transcribe")
        self.tray.set_state("transcribing")

    def _start_amp_poll(self):
        """Push audio amplitude to JS so the waveform reacts to the voice."""
        if self._amp_polling:
            return
        self._amp_polling = True
        def _loop():
            while self._amp_polling:
                try:
                    amp = float(self._amp_provider())
                    # Don't go through self._js (adds a print per call) — call
                    # evaluate_js directly. 20 Hz polling = 1200 calls/min.
                    if self._window and self._ready.is_set():
                        self._window.evaluate_js(f"setAmp({amp:.4f})")
                except Exception:
                    pass
                time.sleep(0.1)  # 10 Hz
        threading.Thread(target=_loop, daemon=True).start()

    def _stop_amp_poll(self):
        self._amp_polling = False

    def show_result(self, text):
        self._show_state("result", data=text)
        self.tray.set_state("ready")

    def show_click_to_paste(self, text):
        """Show result and wait for click-to-paste."""
        self.show_result(text)
        self._start_paste_poll()

    def _start_paste_poll(self):
        """Poll injector state in a thread, show 'colle' when done."""
        def _poll():
            from src.injector import _lock, _pending_text
            while True:
                with _lock:
                    done = _pending_text is None
                if done:
                    self._show_state("pasted")
                    time.sleep(1.5)
                    self.hide()
                    return
                time.sleep(0.1)
        threading.Thread(target=_poll, daemon=True).start()

    def hide(self):
        # Hide the active overlay and bring the floating idle bubble back.
        self._stop_amp_poll()
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
        try:
            self.bubble.show()
        except Exception:
            pass
        self.tray.set_state("ready")

    def stop(self):
        self.quit()

    def quit(self):
        self.tray.stop()
        try:
            self.bubble.stop()
        except Exception:
            pass
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
        if self._external_quit:
            self._external_quit()
