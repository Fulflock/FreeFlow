"""FreeFlow Onboarding window — 4-step welcome flow shown on first launch.

Redesigned (0.1.3) on the FreeFlow design system: warm cream + dot grid,
sticker cards with thick ink borders and hard offset shadows, the brand
palette (pink/blue/yellow/teal/purple). Uses the bundled Space Grotesk +
JetBrains Mono so it renders fully offline.
"""

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
<html lang="fr"><head><meta charset="utf-8">
<title>Bienvenue — FreeFlow</title>
<style>
__FONT_FACE_CSS__

:root{
  --bg:#fef6e4; --ink:#16140f; --paper:#fff;
  --c1:#ff5d8f; --c2:#5d9cff; --c3:#ffd23f; --c4:#5fdba7; --c5:#b794f6;
  --dot:rgba(0,0,0,.07);
  --r-card:20px; --r-pill:999px; --bw:2.5px; --shadow:5px 5px 0 var(--ink);
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{
  font-family:'Space Grotesk','Segoe UI',sans-serif;
  -webkit-font-smoothing:antialiased; color:var(--ink);
  background:radial-gradient(var(--dot) 1.5px,transparent 1.5px) 0 0/22px 22px,var(--bg);
  overflow:hidden; user-select:none;
}
.app{display:flex;flex-direction:column;height:100vh;width:100vw}

/* Top bar */
.topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;flex-shrink:0}
.stamp{display:flex;align-items:center;gap:9px;font-weight:700;font-size:15px;letter-spacing:-.3px}
.stamp svg{width:26px;height:23px;filter:drop-shadow(2px 2px 0 rgba(0,0,0,.12))}
.close{background:transparent;border:none;width:32px;height:32px;border-radius:9px;cursor:pointer;font-size:15px;color:rgba(0,0,0,.5)}
.close:hover{background:rgba(0,0,0,.06);color:var(--ink)}

/* Body / steps */
.body{flex:1;padding:8px 40px;display:flex;flex-direction:column;min-height:0;overflow:hidden}
.step{display:none;flex:1;flex-direction:column;justify-content:center;animation:fade .35s ease both}
.step.active{display:flex}
@keyframes fade{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.tag{display:inline-flex;align-items:center;gap:7px;align-self:flex-start;
  padding:6px 14px;border-radius:var(--r-pill);border:2px solid var(--ink);
  font-size:12.5px;font-weight:600;background:var(--c4);box-shadow:2px 2px 0 var(--ink);margin-bottom:18px}
h1{font-size:40px;line-height:1;letter-spacing:-1.6px;font-weight:700}
h1 .hl{color:var(--c1)}
p.lead{font-size:16px;line-height:1.55;color:rgba(22,20,15,.8);margin-top:16px;max-width:42ch}
.muted{font-size:13px;color:rgba(22,20,15,.55)}

/* Step 1 — welcome hero */
.hero{display:flex;align-items:center;gap:28px}
.hero .txt{flex:1}
.hero .orb{flex-shrink:0;width:150px;height:150px;border-radius:50%;background:var(--c3);
  border:var(--bw) solid var(--ink);box-shadow:var(--shadow);display:grid;place-items:center;transform:rotate(-5deg)}
.hero .orb svg{width:84px;height:74px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
.chip{font-size:12.5px;font-weight:600;padding:6px 12px;border:2px solid var(--ink);border-radius:var(--r-pill);background:var(--paper)}
.chip.b{background:var(--c2);color:#fff} .chip.p{background:var(--c1);color:#fff} .chip.y{background:var(--c3)}

/* Step 2 — hotkey */
.keycombo{display:flex;align-items:center;gap:10px;margin:22px 0}
.key{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;padding:14px 20px;
  background:var(--paper);border:var(--bw) solid var(--ink);border-radius:14px;box-shadow:var(--shadow)}
.plus{font-size:20px;font-weight:700;color:rgba(0,0,0,.45)}
.flow{display:flex;gap:10px;margin-top:8px}
.flow .f{flex:1;background:var(--paper);border:2px solid var(--ink);border-radius:14px;padding:14px;text-align:center}
.flow .f .n{font-size:22px} .flow .f .l{font-size:13px;font-weight:600;margin-top:4px}
.flow .f .s{font-size:11px;color:rgba(0,0,0,.55);margin-top:2px}

/* Step 3 — trust */
.trust{list-style:none;display:flex;flex-direction:column;gap:10px;margin-top:6px}
.trust li{display:flex;gap:12px;align-items:flex-start;font-size:14px;line-height:1.5;
  background:var(--paper);border:2px solid var(--ink);border-radius:13px;padding:12px 14px;box-shadow:2px 2px 0 var(--ink)}
.trust .ic{flex-shrink:0;width:30px;height:30px;border-radius:9px;border:2px solid var(--ink);display:grid;place-items:center;font-size:15px}
.trust li:nth-child(1) .ic{background:var(--c4)} .trust li:nth-child(2) .ic{background:var(--c3)}
.trust li:nth-child(3) .ic{background:var(--c2)} .trust li:nth-child(4) .ic{background:var(--c1)}
.trust b{font-weight:600}
.trust code{font-family:'JetBrains Mono',monospace;font-size:12px;background:var(--bg);border:1px solid var(--ink);border-radius:4px;padding:1px 5px}

/* Step 4 — ready */
.ready{display:flex;align-items:center;gap:26px}
.ready .txt{flex:1}
.checks{list-style:none;display:flex;flex-direction:column;gap:9px;margin-top:8px}
.checks li{display:flex;align-items:center;gap:10px;font-size:14.5px}
.checks .dot{width:22px;height:22px;border-radius:50%;background:var(--c4);border:2px solid var(--ink);display:grid;place-items:center;font-size:12px;font-weight:700}
.ready .big{flex-shrink:0;width:140px;height:140px;border-radius:28px;background:var(--c1);border:var(--bw) solid var(--ink);box-shadow:var(--shadow);display:grid;place-items:center;transform:rotate(4deg)}
.ready .big svg{width:80px;height:70px}

/* Footer */
.footer{display:flex;align-items:center;justify-content:space-between;padding:18px 40px 24px;flex-shrink:0;border-top:2px dashed rgba(0,0,0,.18)}
.pips{display:flex;align-items:center;gap:7px}
.pip{width:11px;height:11px;border-radius:50%;background:var(--paper);border:2px solid var(--ink);transition:width .2s,background .2s}
.pip.active{width:30px;background:var(--c1)} .pip.passed{background:var(--c1)}
.pips .lbl{margin-left:8px;font-family:'JetBrains Mono',monospace;font-size:11px;color:rgba(0,0,0,.5)}
.nav{display:flex;gap:10px}
.btn{font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:15px;padding:11px 22px;
  border:var(--bw) solid var(--ink);border-radius:var(--r-pill);background:var(--c1);color:#fff;cursor:pointer;
  box-shadow:3px 3px 0 var(--ink);transition:transform .12s,box-shadow .12s}
.btn:hover{transform:translate(-2px,-2px);box-shadow:5px 5px 0 var(--ink)}
.btn:active{transform:translate(2px,2px);box-shadow:0 0 0 var(--ink)}
.btn.ghost{background:transparent;color:var(--ink);box-shadow:none}
.btn.ghost:hover{background:var(--paper);transform:none;box-shadow:2px 2px 0 var(--ink)}
.btn.finish{background:var(--c4);color:var(--ink)}
</style>
</head>
<body>
<div class="app">

  <header class="topbar">
    <span class="stamp">
      <svg viewBox="0 0 64 56"><path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z" fill="#ff5d8f" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/><g fill="#16140f"><path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/><path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/></g></svg>
      FreeFlow
    </span>
    <button class="close" id="close-btn" title="passer">&#10005;</button>
  </header>

  <main class="body">

    <!-- Step 1 — Welcome -->
    <section class="step active" id="step-1">
      <div class="hero">
        <div class="txt">
          <span class="tag">★ bienvenue à bord</span>
          <h1>Salut !<br>Ta voix devient<br><span class="hl">du texte</span>.</h1>
          <p class="lead">FreeFlow transcrit ce que tu dis, partout sur Windows. Maintiens une touche, parle, lâche — c'est écrit.</p>
          <div class="chips">
            <span class="chip p">100% local</span>
            <span class="chip y">gratuit</span>
            <span class="chip b">sans compte</span>
          </div>
        </div>
        <div class="orb">
          <svg viewBox="0 0 64 56"><path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z" fill="#ff5d8f" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/><g fill="#16140f"><path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/><path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/></g></svg>
        </div>
      </div>
    </section>

    <!-- Step 2 — How it works -->
    <section class="step" id="step-2">
      <span class="tag" style="background:var(--c3)">étape 1 — la touche magique</span>
      <h1 style="font-size:32px">Maintiens. Parle. <span class="hl">Lâche.</span></h1>
      <div class="keycombo">
        <span class="key">Ctrl</span><span class="plus">+</span><span class="key">Espace</span>
      </div>
      <p class="lead" style="margin-top:0">Tu maintiens la combinaison pour dicter, tu lâches pour transcrire. Le texte se colle là où est ton curseur.</p>
      <div class="flow">
        <div class="f"><div class="n">🎙️</div><div class="l">Maintiens</div><div class="s">Ctrl + Espace</div></div>
        <div class="f"><div class="n">🗣️</div><div class="l">Parle</div><div class="s">dis ta phrase</div></div>
        <div class="f"><div class="n">✨</div><div class="l">Lâche</div><div class="s">c'est collé</div></div>
      </div>
      <p class="muted" style="margin-top:14px">Tu pourras changer la touche dans les Réglages.</p>
    </section>

    <!-- Step 3 — Trust / disclosure -->
    <section class="step" id="step-3">
      <span class="tag" style="background:var(--c2);color:#fff">étape 2 — en toute transparence</span>
      <h1 style="font-size:30px">Ce que FreeFlow fait <span class="hl">(et ne fait pas)</span>.</h1>
      <ul class="trust">
        <li><span class="ic">🔒</span><span><b>Tout reste sur ton PC.</b> Ton audio ne part jamais sur internet — la transcription tourne sur ton processeur.</span></li>
        <li><span class="ic">📝</span><span><b>L'historique est stocké en clair</b> dans <code>~/.freeflow</code>. Ne dicte pas de mots de passe (ou supprime-les après).</span></li>
        <li><span class="ic">⌨️</span><span><b>Écoute du clavier</b> pour détecter Ctrl + Espace — mais FreeFlow n'agit que sur cette combo.</span></li>
        <li><span class="ic">📋</span><span><b>Le presse-papier</b> est utilisé une fraction de seconde pour coller, puis restauré.</span></li>
      </ul>
    </section>

    <!-- Step 4 — Ready -->
    <section class="step" id="step-4">
      <div class="ready">
        <div class="txt">
          <span class="tag" style="background:var(--c4)">étape 3 — c'est parti</span>
          <h1 style="font-size:34px">Tout est <span class="hl">prêt</span>.</h1>
          <ul class="checks">
            <li><span class="dot">✓</span> Raccourci activé</li>
            <li><span class="dot">✓</span> Moteur de transcription chargé</li>
            <li><span class="dot">✓</span> 100% hors-ligne &amp; privé</li>
          </ul>
          <p class="muted" style="margin-top:14px">Clique sur <b>C'est parti</b>, ouvre n'importe quel champ de texte et essaie !</p>
        </div>
        <div class="big">
          <svg viewBox="0 0 64 56"><path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z" fill="#fff" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/><g fill="#16140f"><path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/><path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/></g></svg>
        </div>
      </div>
    </section>

  </main>

  <footer class="footer">
    <div class="pips">
      <span class="pip active" data-step="1"></span>
      <span class="pip" data-step="2"></span>
      <span class="pip" data-step="3"></span>
      <span class="pip" data-step="4"></span>
      <span class="lbl">étape <span id="step-num">1</span>/4</span>
    </div>
    <div class="nav">
      <button class="btn ghost" id="prev-btn" style="visibility:hidden">← retour</button>
      <button class="btn" id="next-btn">suivant →</button>
    </div>
  </footer>

</div>

<script>
var current=1, MAX=4;
function render(){
  for(var i=1;i<=MAX;i++){
    var s=document.getElementById('step-'+i); if(s)s.classList.toggle('active',i===current);
    var p=document.querySelector('.pip[data-step="'+i+'"]');
    if(p){p.classList.toggle('active',i===current);p.classList.toggle('passed',i<current);}
  }
  document.getElementById('step-num').textContent=current;
  document.getElementById('prev-btn').style.visibility=current===1?'hidden':'visible';
  var n=document.getElementById('next-btn');
  if(current===MAX){n.textContent="c'est parti ! ✨";n.classList.add('finish');}
  else{n.textContent='suivant →';n.classList.remove('finish');}
}
function prev(){if(current>1){current--;render();}}
function next(){if(current<MAX){current++;render();}else{finish();}}
document.getElementById('prev-btn').addEventListener('click',prev);
document.getElementById('next-btn').addEventListener('click',next);
document.getElementById('close-btn').addEventListener('click',finish);
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight')next();else if(e.key==='ArrowLeft')prev();});
function finish(){
  try{ if(window.pywebview&&window.pywebview.api&&window.pywebview.api.finish){window.pywebview.api.finish();return;} }catch(e){}
  window.close();
}
render();
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
            width=620,
            height=620,
            frameless=False,
            on_top=False,
            background_color="#fef6e4",
            js_api=self._api,
        )
        self._api.bind(self._window)
        return self._window
