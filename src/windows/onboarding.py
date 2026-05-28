"""FreeFlow Onboarding window — 4-step welcome flow shown on first launch."""

import json
import os
from datetime import datetime

import webview

from src.fonts import FONT_CSS


# ── Persistence helpers ─────────────────────────────────────────────────────

_FREEFLOW_DIR = os.path.join(os.path.expanduser("~"), ".freeflow")
_ONBOARDING_FLAG = os.path.join(_FREEFLOW_DIR, "onboarding_done.json")


def is_onboarding_done() -> bool:
    """Has the user already completed (or skipped) onboarding?"""
    return os.path.exists(_ONBOARDING_FLAG)


def mark_onboarding_done():
    """Persist the onboarding-done flag in ~/.freeflow/."""
    try:
        os.makedirs(_FREEFLOW_DIR, exist_ok=True)
        with open(_ONBOARDING_FLAG, "w", encoding="utf-8") as f:
            json.dump(
                {"done": True, "timestamp": datetime.now().isoformat()},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception:
        # Best-effort — onboarding still completes even if we cannot persist.
        pass


# ── HTML ────────────────────────────────────────────────────────────────────

ONBOARDING_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Bienvenue — FreeFlow</title>
<style>
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
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: var(--ink);
  background:
    radial-gradient(rgba(0,0,0,.06) 1px, transparent 1px) 0 0 / 20px 20px,
    var(--bg);
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

/* ── Top bar with close ─────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  flex-shrink: 0;
}
.topbar .stamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgba(0,0,0,.55);
}
.topbar .close {
  background: transparent;
  border: none;
  width: 32px; height: 32px;
  cursor: pointer;
  font-size: 14px;
  color: rgba(0,0,0,.55);
  border-radius: 8px;
}
.topbar .close:hover { background: rgba(0,0,0,.06); color: var(--ink); }

/* ── Body (steps) ───────────────────────────────────── */
.body {
  flex: 1;
  padding: 18px 36px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.step { display: none; flex: 1; flex-direction: column; }
.step.active { display: flex; }

.pill {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  border: 2px solid var(--ink);
  font-size: 12px;
  font-weight: 600;
  background: var(--c3);
  margin-bottom: 14px;
  box-shadow: 2px 2px 0 var(--ink);
}

h1 {
  font-weight: 700;
  letter-spacing: -1.5px;
  line-height: .98;
  margin-bottom: 16px;
}

p.lead {
  font-size: 15px;
  line-height: 1.55;
  color: rgba(0,0,0,.78);
  margin-bottom: 12px;
}

.muted { font-size: 13px; color: rgba(0,0,0,.55); }

/* ── Welcome step ───────────────────────────────────── */
.welcome {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
}
.welcome .text { flex: 1; }
.welcome h1 { font-size: 44px; }
.welcome .hero {
  flex-shrink: 0;
  width: 200px; height: 200px;
  border-radius: 50%;
  background: var(--c4);
  border: 2.5px solid var(--ink);
  box-shadow: 6px 6px 0 var(--ink);
  display: grid; place-items: center;
  transform: rotate(-4deg);
}

.hi-pink { background: var(--c1); padding: 0 6px; border: 2px solid var(--ink); border-radius: 6px; }
.hi-yellow { background: var(--c5); padding: 0 6px; border: 2px solid var(--ink); border-radius: 6px; }

/* ── Hotkey step ────────────────────────────────────── */
.hotkey-box {
  background: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 18px;
  padding: 22px;
  box-shadow: 4px 4px 0 var(--ink);
  display: grid;
  place-items: center;
  margin: 18px 0;
}
.keys {
  display: flex;
  align-items: center;
  gap: 6px;
}
.key {
  display: inline-block;
  padding: 12px 18px;
  background: var(--bg);
  border: 2.5px solid var(--ink);
  border-radius: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 3px 3px 0 var(--ink);
}
.plus { font-size: 18px; color: rgba(0,0,0,.5); font-weight: 700; }
.tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: var(--c3);
  border: 2px solid var(--ink);
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.4;
  margin-top: auto;
}

/* ── Ready step ─────────────────────────────────────── */
.ready-grid {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex: 1;
}
.ready-grid > * { flex: 1; min-width: 0; }

.try-box {
  background: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 16px;
  padding: 18px;
  box-shadow: 5px 5px 0 var(--c1);
}
.try-box .row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.try-box .row .label { font-size: 13px; font-weight: 600; }
.try-box textarea {
  width: 100%;
  min-height: 130px;
  padding: 12px;
  font-size: 14px;
  font-family: inherit;
  border: 2px dashed var(--ink);
  border-radius: 12px;
  background: var(--bg);
  resize: vertical;
  outline: none;
  color: var(--ink);
}
.try-box .hint {
  margin-top: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgba(0,0,0,.55);
}
.tag {
  display: inline-block;
  padding: 2px 8px;
  background: var(--c3);
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
}

ul.checks { list-style: none; margin: 14px 0 0; }
ul.checks li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  margin-bottom: 8px;
  color: rgba(0,0,0,.85);
}
ul.checks li .dot {
  width: 18px; height: 18px;
  border-radius: 50%;
  background: var(--c4);
  border: 1.5px solid var(--ink);
  display: grid; place-items: center;
  font-size: 10px;
  font-weight: 700;
}

/* ── Footer (progress + nav) ────────────────────────── */
.footer {
  padding: 16px 36px 22px;
  border-top: 1px dashed rgba(0,0,0,.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: rgba(255,255,255,.4);
}

.progress { display: flex; align-items: center; gap: 6px; }
.progress .pip {
  width: 12px; height: 12px;
  border-radius: 999px;
  background: var(--bg);
  border: 2px solid var(--ink);
  transition: width .2s, background .2s;
}
.progress .pip.active { width: 32px; background: var(--c1); }
.progress .pip.passed { background: var(--c1); }
.progress .label {
  margin-left: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgba(0,0,0,.55);
}

.nav { display: flex; gap: 10px; }
.btn {
  background: var(--c1);
  color: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 999px;
  padding: 10px 22px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 3px 3px 0 var(--ink);
}
.btn:hover { transform: translate(-1px,-1px); box-shadow: 4px 4px 0 var(--ink); }
.btn:active { transform: translate(2px,2px); box-shadow: none; }
.btn.finish { background: var(--c4); color: var(--ink); }

.btn-outline {
  background: transparent;
  color: var(--ink);
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: 9px 18px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
.btn-outline:hover { background: var(--paper); }

/* ── Trust list (step 3) ─────────────────────────────── */
.trust-list { list-style: none; padding: 0; margin: 16px 0; display: flex; flex-direction: column; gap: 10px; }
.trust-list li { font-size: 13px; line-height: 1.55; background: var(--paper); border: 2px solid var(--ink); border-radius: 10px; padding: 10px 14px; box-shadow: 2px 2px 0 var(--c5); }
.trust-list li b { color: var(--ink); }
.trust-list code { font-family: 'JetBrains Mono', monospace; background: rgba(0,0,0,.06); padding: 1px 5px; border-radius: 3px; font-size: 11px; }

.step-icon { font-size: 36px; margin-bottom: 8px; }
.step-actions { display: flex; gap: 10px; margin-top: auto; padding-top: 12px; }
.step-actions .btn-prev,
.step-actions .btn-next {
  background: var(--c1);
  color: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 999px;
  padding: 10px 22px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 3px 3px 0 var(--ink);
}
.step-actions .btn-prev {
  background: transparent;
  color: var(--ink);
}
</style>
</head>
<body>
<div class="app">

  <header class="topbar">
    <span class="stamp">free_flow · bienvenue</span>
    <button class="close" id="close-btn" title="fermer">&#10005;</button>
  </header>

  <main class="body">

    <!-- ── Step 1: welcome ─────────────────────────────── -->
    <section class="step active" id="step-1">
      <div class="welcome">
        <div class="text">
          <span class="pill">★ bienvenue à bord</span>
          <h1>Salut !<br><span class="hi-pink">FreeFlow</span> est prêt<br>à <span class="hi-yellow">parler</span>.</h1>
          <p class="lead">
            FreeFlow transforme ta voix en texte directement sur ta machine.
            <b>100 % local. Gratuit. Aucun compte.</b>
          </p>
          <p class="lead">
            Maintiens un raccourci, parle, lâche — ton texte est collé là où tu cliques.
          </p>
          <p class="muted">version 0.1 · MIT · made solo ♡</p>
        </div>
        <div class="hero">
          <svg width="120" height="106" viewBox="0 0 64 56">
            <path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z"
                  fill="#ff5d8f" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/>
            <g fill="#16140f">
              <path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/>
              <path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/>
            </g>
          </svg>
        </div>
      </div>
    </section>

    <!-- ── Step 2: hotkey ──────────────────────────────── -->
    <section class="step" id="step-2">
      <span class="pill" style="background:var(--c5);">étape 2 — ton raccourci</span>
      <h1 style="font-size:32px;">Choisis ta <span class="hi-pink">touche magique</span>.</h1>
      <p class="lead">
        Maintiens cette combinaison pour <b>dicter</b>, lâche pour <b>transcrire</b>.
        On utilise <b>Ctrl + Espace</b> par défaut — facile à atteindre,
        difficile à presser par accident.
      </p>

      <div class="hotkey-box">
        <div class="keys">
          <span class="key">Ctrl</span>
          <span class="plus">+</span>
          <span class="key">Espace</span>
        </div>
        <p class="muted" style="margin-top:12px;">tu pourras le changer plus tard dans Réglages</p>
      </div>

      <div class="tip">
        <span style="font-size:18px;">🎤</span>
        <span>Essaie en parlant maintenant pour tester — Windows va te demander l'accès au micro la première fois, dis oui.</span>
      </div>
    </section>

    <!-- ── Step 3: trust disclosure ────────────────────── -->
    <section class="step" id="step-3" data-step="3">
      <div class="step-icon">🔒</div>
      <h2>Ce que FreeFlow fait à ton PC</h2>
      <p class="lead">Sois au courant — c'est important.</p>
      <ul class="trust-list">
        <li><b>🎤 Tout reste local.</b> Ton audio ne quitte jamais ton PC. La transcription se fait sur ton processeur avec Whisper.</li>
        <li><b>📝 L'historique est stocké en clair</b> dans <code>~/.freeflow/history/</code>. <b>Ne dicte pas de mots de passe</b> ou tu peux les supprimer après.</li>
        <li><b>⌨️ Hook clavier global</b> — FreeFlow voit techniquement chaque touche que tu tapes (mais n'agit que sur Ctrl+Espace).</li>
        <li><b>📋 Ton presse-papier est temporairement écrit</b> pour coller la transcription (~150ms), puis restauré.</li>
        <li><b>🎯 Le texte se colle où tu cliques</b>, pas où tu étais quand tu as parlé. Attention aux fenêtres publiques (Discord, Slack).</li>
      </ul>
      <div class="step-actions">
        <button class="btn-prev" onclick="prevStep()">← Retour</button>
        <button class="btn-next" onclick="nextStep()">J'ai compris →</button>
      </div>
    </section>

    <!-- ── Step 4: first try ───────────────────────────── -->
    <section class="step" id="step-4">
      <span class="pill" style="background:var(--c4);">étape 4 — go</span>
      <h1 style="font-size:32px;">Essaie maintenant.</h1>
      <p class="lead">
        Maintiens <b>Ctrl + Espace</b>, dis quelque chose, lâche.
        Ou utilise ce champ comme bac à sable pour t'entraîner à taper.
      </p>

      <div class="ready-grid">
        <div>
          <ul class="checks">
            <li><span class="dot">✓</span> raccourci enregistré</li>
            <li><span class="dot">✓</span> modèle Whisper téléchargé</li>
            <li><span class="dot">✓</span> micro autorisé</li>
            <li><span class="dot">●</span> en attente de ton premier mot…</li>
          </ul>
          <p class="muted" style="margin-top:14px;">
            Clique sur <b>C'est parti !</b> pour terminer.
            On ne te montrera plus cet écran.
          </p>
        </div>
        <div class="try-box">
          <div class="row">
            <span class="label">🎙 Fais un essai</span>
            <span class="tag">SANDBOX</span>
          </div>
          <textarea placeholder="ton texte apparaîtra ici…"></textarea>
          <div class="hint">en attente — maintiens Ctrl + Espace</div>
        </div>
      </div>
    </section>

  </main>

  <footer class="footer">
    <div class="progress">
      <span class="pip active" data-step="1"></span>
      <span class="pip" data-step="2"></span>
      <span class="pip" data-step="3"></span>
      <span class="pip" data-step="4"></span>
      <span class="label">étape <span id="step-num">1</span> / 4</span>
    </div>
    <div class="nav">
      <button class="btn-outline" id="prev-btn" style="visibility:hidden;">← retour</button>
      <button class="btn" id="next-btn">suivant →</button>
    </div>
  </footer>

</div>

<script>
var current = 1;
var MAX_STEP = 4;
var max = MAX_STEP;

function render() {
  for (var i = 1; i <= max; i++) {
    var s = document.getElementById('step-' + i);
    if (s) s.classList.toggle('active', i === current);
    var p = document.querySelector('.pip[data-step="' + i + '"]');
    if (p) {
      p.classList.toggle('active', i === current);
      p.classList.toggle('passed', i < current);
    }
  }
  document.getElementById('step-num').textContent = current;
  document.getElementById('prev-btn').style.visibility = current === 1 ? 'hidden' : 'visible';
  var next = document.getElementById('next-btn');
  if (current === max) {
    next.textContent = "c'est parti ! ↗";
    next.classList.add('finish');
  } else {
    next.textContent = 'suivant →';
    next.classList.remove('finish');
  }
}

function prevStep() {
  if (current > 1) { current--; render(); }
}
function nextStep() {
  if (current < max) { current++; render(); } else { finish(); }
}

document.getElementById('prev-btn').addEventListener('click', prevStep);
document.getElementById('next-btn').addEventListener('click', nextStep);
document.getElementById('close-btn').addEventListener('click', finish);

function finish() {
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.finish) {
      window.pywebview.api.finish();
      return;
    }
  } catch (e) {}
  window.close();
}
</script>
</body></html>""".replace("__FONT_FACE_CSS__", FONT_CSS)


# ── Window class ────────────────────────────────────────────────────────────


class _OnboardingApi:
    """Bridge so the HTML can mark onboarding done & close the window."""

    def __init__(self):
        self._window = None

    def bind(self, window):
        self._window = window

    def finish(self):
        mark_onboarding_done()
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass


class OnboardingWindow:
    """First-launch welcome flow — 4 steps with prev/next pagination."""

    def __init__(self):
        self._window = None
        self._api = _OnboardingApi()

    def open(self):
        """Show the onboarding window centered on screen."""
        self._window = webview.create_window(
            "Bienvenue — FreeFlow",
            html=ONBOARDING_HTML,
            width=540,
            height=640,
            frameless=False,
            on_top=False,
            background_color="#f4f0e8",
            js_api=self._api,
        )
        self._api.bind(self._window)
        return self._window
