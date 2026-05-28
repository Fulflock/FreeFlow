"""FreeFlow Settings window — sticker-pack themed pywebview window."""

import webview

from src.fonts import FONT_CSS


SETTINGS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Réglages — FreeFlow</title>
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
  background: var(--bg);
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: var(--ink);
  overflow: hidden;
}

.app {
  display: flex;
  height: 100vh;
  width: 100vw;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: rgba(0,0,0,.03);
  border-right: 1px solid rgba(0,0,0,.08);
  padding: 18px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px 14px;
  margin-bottom: 6px;
  border-bottom: 1px dashed rgba(0,0,0,.15);
}
.brand-dot {
  width: 22px; height: 22px;
  border-radius: 6px;
  background: var(--c1);
  border: 2px solid var(--ink);
  display: grid; place-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 700;
  color: var(--ink);
}
.brand-name {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -.3px;
}

.side-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 2px solid transparent;
  user-select: none;
}
.side-item:hover {
  background: rgba(0,0,0,.04);
}
.side-item.active {
  background: var(--paper);
  border: 2px solid var(--ink);
  box-shadow: 2px 2px 0 var(--ink);
  font-weight: 600;
}
.side-item .ico {
  font-size: 14px;
  width: 16px;
  text-align: center;
}
.side-item.muted {
  color: rgba(0,0,0,.5);
  margin-top: auto;
}

/* ── Main pane ───────────────────────────────────────────────────── */
.main {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 14px; right: 18px;
  width: 30px; height: 30px;
  border-radius: 50%;
  background: var(--paper);
  border: 2px solid var(--ink);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  display: grid; place-items: center;
  box-shadow: 2px 2px 0 var(--ink);
  z-index: 10;
  color: var(--ink);
}
.close-btn:hover { background: var(--c1); color: var(--paper); }
.close-btn:active { transform: translate(2px, 2px); box-shadow: none; }

.section { display: none; }
.section.active { display: block; }

.section h2 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -.8px;
  margin-bottom: 4px;
}
.section .subtitle {
  font-size: 13px;
  color: rgba(0,0,0,.6);
  margin-bottom: 22px;
}
.section .subtitle code {
  background: var(--c3);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

/* ── Setting row (sticker) ───────────────────────────────────────── */
.row {
  background: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 14px;
  padding: 14px 18px;
  box-shadow: 3px 3px 0 var(--ink);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
}
.row-label { min-width: 0; }
.row-label .lbl { font-size: 14px; font-weight: 600; }
.row-label .hint { font-size: 12px; color: rgba(0,0,0,.55); margin-top: 2px; }
.row-control { flex-shrink: 0; }

/* ── Controls ────────────────────────────────────────────────────── */
.kbd {
  display: inline-block;
  padding: 4px 10px;
  background: var(--bg);
  border: 2px solid var(--ink);
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 2px 2px 0 var(--ink);
}
.plus { color: rgba(0,0,0,.4); margin: 0 3px; font-weight: 700; }

.btn-sm {
  background: var(--paper);
  border: 2px solid var(--ink);
  border-radius: 999px;
  padding: 5px 12px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  color: var(--ink);
}
.btn-sm:hover { background: var(--c5); }
.btn-sm:active { transform: translate(1px,1px); }

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

/* Select pill */
.select {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg);
  border: 2px solid var(--ink);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  user-select: none;
}
.select .caret { color: rgba(0,0,0,.5); font-size: 10px; }

/* Toggle */
.toggle {
  width: 46px; height: 26px;
  border-radius: 999px;
  background: var(--bg);
  border: 2px solid var(--ink);
  position: relative;
  cursor: pointer;
  box-shadow: 2px 2px 0 var(--ink);
  transition: background .15s;
}
.toggle.on { background: var(--c4); }
.toggle .knob {
  position: absolute;
  top: 1px; left: 1px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: var(--paper);
  border: 1.5px solid var(--ink);
  transition: left .15s;
}
.toggle.on .knob { left: 21px; }

/* Model picker */
.models {
  display: flex; gap: 6px; flex-wrap: wrap;
  justify-content: flex-end;
}
.model {
  padding: 6px 10px;
  background: var(--bg);
  border: 2px solid var(--ink);
  border-radius: 8px;
  font-size: 12px;
  text-align: center;
  cursor: pointer;
  min-width: 92px;
}
.model.active {
  background: var(--c4);
  box-shadow: 2px 2px 0 var(--ink);
}
.model .name { font-weight: 600; }
.model .meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: rgba(0,0,0,.6);
  margin-top: 2px;
}

/* Slider */
.slider {
  width: 180px;
  position: relative;
  height: 28px;
}
.slider .track {
  position: absolute;
  left: 0; right: 0; top: 50%;
  transform: translateY(-50%);
  height: 6px; border-radius: 3px;
  background: var(--bg);
  border: 1.5px solid var(--ink);
}
.slider .fill {
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  height: 6px; border-radius: 3px;
  width: 75%;
  background: var(--c3);
  border: 1.5px solid var(--ink);
}
.slider .knob {
  position: absolute;
  left: calc(75% - 10px);
  top: 50%;
  transform: translateY(-50%);
  width: 20px; height: 20px;
  border-radius: 50%;
  background: var(--paper);
  border: 2px solid var(--ink);
  box-shadow: 1px 1px 0 var(--ink);
  cursor: grab;
}

/* About box */
.about-card {
  background: var(--paper);
  border: 2.5px solid var(--ink);
  border-radius: 14px;
  padding: 22px;
  box-shadow: 4px 4px 0 var(--c1);
  text-align: center;
}
.about-logo {
  width: 78px; height: 78px;
  border-radius: 22px;
  background: var(--c4);
  border: 2.5px solid var(--ink);
  box-shadow: 3px 3px 0 var(--ink);
  margin: 0 auto 14px;
  display: grid; place-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 28px;
  letter-spacing: -2px;
}
.about-card h3 {
  font-size: 20px;
  margin-bottom: 4px;
  letter-spacing: -.5px;
}
.about-card .ver {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: rgba(0,0,0,.6);
  margin-bottom: 14px;
}
.about-card p {
  font-size: 13px;
  color: rgba(0,0,0,.7);
  line-height: 1.5;
  max-width: 380px;
  margin: 0 auto 14px;
}

/* Footer actions */
.footer-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-top: 18px;
  margin-top: 22px;
  border-top: 1px dashed rgba(0,0,0,.15);
}
.footer-hint {
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: rgba(0,0,0,.5);
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,.18); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,.3); }
</style>
</head>
<body>
<div class="app">

  <aside class="sidebar">
    <div class="brand">
      <div class="brand-dot">ff</div>
      <div class="brand-name">FreeFlow</div>
    </div>
    <div class="side-item active" data-target="general">
      <span class="ico">&#9881;</span> Général
    </div>
    <div class="side-item" data-target="audio">
      <span class="ico">&#127908;</span> Audio
    </div>
    <div class="side-item" data-target="shortcuts">
      <span class="ico">&#8984;</span> Raccourcis
    </div>
    <div class="side-item" data-target="model">
      <span class="ico">&#129504;</span> Modèle
    </div>
    <div class="side-item muted" data-target="about">
      <span class="ico">&#9432;</span> À propos
    </div>
  </aside>

  <main class="main">
    <button class="close-btn" id="close-btn" title="fermer">&#10005;</button>

    <!-- ── Général ── -->
    <section class="section active" id="sec-general">
      <h2>Général</h2>
      <p class="subtitle">tout reste local, dans <code>~/.freeflow/config.json</code></p>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Lancer au démarrage de Windows</div>
          <div class="hint">apparaît dans la barre des tâches au boot</div>
        </div>
        <div class="row-control">
          <div class="toggle on" data-toggle><span class="knob"></span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Ponctuation automatique</div>
          <div class="hint">ajoute virgules, points et majuscules</div>
        </div>
        <div class="row-control">
          <div class="toggle on" data-toggle><span class="knob"></span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Langue principale</div>
          <div class="hint">laisse sur auto si tu mixes les langues</div>
        </div>
        <div class="row-control">
          <div class="select">&#127467;&#127479; français <span class="caret">&#9662;</span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Opacité de l'overlay</div>
          <div class="hint">niveau 75 %</div>
        </div>
        <div class="row-control">
          <div class="slider">
            <div class="track"></div>
            <div class="fill"></div>
            <div class="knob"></div>
          </div>
        </div>
      </div>

      <div class="footer-actions">
        <button class="btn">&#10003; Sauvegarder</button>
        <button class="btn-outline">Annuler</button>
        <span class="footer-hint">modifs auto-appliquées · CTRL+S</span>
      </div>
    </section>

    <!-- ── Audio ── -->
    <section class="section" id="sec-audio">
      <h2>Audio</h2>
      <p class="subtitle">configure ton micro et la qualité de capture</p>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Périphérique d'entrée</div>
          <div class="hint">le micro utilisé pour la dictée</div>
        </div>
        <div class="row-control">
          <div class="select">Micro par défaut <span class="caret">&#9662;</span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Gain micro</div>
          <div class="hint">niveau 75 %</div>
        </div>
        <div class="row-control">
          <div class="slider">
            <div class="track"></div>
            <div class="fill"></div>
            <div class="knob"></div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Réduction de bruit</div>
          <div class="hint">filtre le souffle constant en arrière-plan</div>
        </div>
        <div class="row-control">
          <div class="toggle on" data-toggle><span class="knob"></span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Coupure automatique des silences</div>
          <div class="hint">arrête la capture après 2 s de silence</div>
        </div>
        <div class="row-control">
          <div class="toggle" data-toggle><span class="knob"></span></div>
        </div>
      </div>
    </section>

    <!-- ── Raccourcis ── -->
    <section class="section" id="sec-shortcuts">
      <h2>Raccourcis</h2>
      <p class="subtitle">maintiens la combo pour dicter, lâche pour transcrire</p>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Raccourci principal</div>
          <div class="hint">la touche magique pour dicter</div>
        </div>
        <div class="row-control">
          <span class="kbd">Ctrl</span><span class="plus">+</span><span class="kbd">Espace</span>
          <button class="btn-sm" style="margin-left:8px;">changer</button>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Coller automatiquement</div>
          <div class="hint">si non, clique dans le champ pour coller</div>
        </div>
        <div class="row-control">
          <div class="toggle" data-toggle><span class="knob"></span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Annuler la transcription</div>
          <div class="hint">touche pour annuler en cours de dictée</div>
        </div>
        <div class="row-control">
          <span class="kbd">Esc</span>
          <button class="btn-sm" style="margin-left:8px;">changer</button>
        </div>
      </div>
    </section>

    <!-- ── Modèle ── -->
    <section class="section" id="sec-model">
      <h2>Modèle</h2>
      <p class="subtitle">plus gros = plus précis mais plus lent</p>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Modèle de transcription</div>
          <div class="hint">choisis le compromis vitesse / précision</div>
        </div>
        <div class="row-control">
          <div class="models">
            <div class="model">
              <div class="name">tiny</div>
              <div class="meta">75 mo · &#9733;&#9733;</div>
            </div>
            <div class="model active">
              <div class="name">small</div>
              <div class="meta">466 mo · &#9733;&#9733;&#9733;</div>
            </div>
            <div class="model">
              <div class="name">medium</div>
              <div class="meta">780 mo · &#9733;&#9733;&#9733;&#9733;</div>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Calcul sur GPU si dispo</div>
          <div class="hint">accélère la transcription quand possible</div>
        </div>
        <div class="row-control">
          <div class="toggle on" data-toggle><span class="knob"></span></div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Stocker les modèles dans</div>
          <div class="hint">dossier local — sans connexion après téléchargement</div>
        </div>
        <div class="row-control">
          <div class="select">~/.freeflow/models <span class="caret">&#9662;</span></div>
        </div>
      </div>
    </section>

    <!-- ── À propos ── -->
    <section class="section" id="sec-about">
      <h2>À propos</h2>
      <p class="subtitle">FreeFlow est libre, local et sans compte.</p>

      <div class="about-card">
        <div class="about-logo">ff</div>
        <h3>FreeFlow</h3>
        <div class="ver">version 0.1 · MIT</div>
        <p>
          Une dictée vocale 100 % locale pour Windows.
          Aucune donnée n'est envoyée sur Internet — ton micro
          ne quitte jamais ta machine.
        </p>
        <button class="btn-sm">github.com/freeflow</button>
      </div>
    </section>

  </main>
</div>

<script>
// Sidebar navigation
var items = document.querySelectorAll('.side-item');
var sections = document.querySelectorAll('.section');
items.forEach(function(it){
  it.addEventListener('click', function(){
    var target = it.getAttribute('data-target');
    if (!target) return;
    items.forEach(function(x){ x.classList.remove('active'); });
    it.classList.add('active');
    sections.forEach(function(s){ s.classList.remove('active'); });
    var sec = document.getElementById('sec-' + target);
    if (sec) sec.classList.add('active');
  });
});

// Toggle controls
document.querySelectorAll('[data-toggle]').forEach(function(t){
  t.addEventListener('click', function(){
    t.classList.toggle('on');
  });
});

// Close button — uses pywebview bridge if available
document.getElementById('close-btn').addEventListener('click', function(){
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.close) {
      window.pywebview.api.close();
      return;
    }
  } catch (e) {}
  window.close();
});
</script>
</body></html>""".replace("__FONT_FACE_CSS__", FONT_CSS)


class _SettingsApi:
    """Small bridge so the HTML close button can dismiss the window."""

    def __init__(self):
        self._window = None

    def bind(self, window):
        self._window = window

    def close(self):
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass


class SettingsWindow:
    """Standalone settings window — local, no persistence (visual scaffold)."""

    def __init__(self):
        self._window = None
        self._api = _SettingsApi()

    def open(self):
        """Create and show the settings window."""
        self._window = webview.create_window(
            "Réglages — FreeFlow",
            html=SETTINGS_HTML,
            width=820,
            height=560,
            frameless=False,
            on_top=False,
            background_color="#f4f0e8",
            js_api=self._api,
        )
        self._api.bind(self._window)
        return self._window
