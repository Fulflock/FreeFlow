"""FreeFlow Settings window — sticker-pack themed pywebview window.

Real, persisted settings (0.1.1+). Controls that have a working backend are
wired to ~/.freeflow/config.json via the Python bridge below; controls that
don't yet have a backend are clearly marked "bientôt" so nothing is fake.

Wired (persisted): launch_at_startup, auto_punctuation, language, model_size,
overlay_opacity, hotkey_combo. Some apply live (language, punctuation), the
rest on next launch — the UI says so.
"""

import webview

from src.fonts import FONT_CSS
from src.config import load_config, save_config


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

.app { display: flex; height: 100vh; width: 100vw; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
.sidebar {
  width: 220px; flex-shrink: 0;
  background: rgba(0,0,0,.03);
  border-right: 1px solid rgba(0,0,0,.08);
  padding: 18px 12px;
  display: flex; flex-direction: column; gap: 4px;
}
.brand {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 10px 14px; margin-bottom: 6px;
  border-bottom: 1px dashed rgba(0,0,0,.15);
}
.brand-dot {
  width: 22px; height: 22px; border-radius: 6px;
  background: var(--c1); border: 2px solid var(--ink);
  display: grid; place-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 700; color: var(--ink);
}
.brand-name { font-size: 14px; font-weight: 600; letter-spacing: -.3px; }

.side-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: 8px;
  font-size: 13px; font-weight: 500; cursor: pointer;
  border: 2px solid transparent; user-select: none;
}
.side-item:hover { background: rgba(0,0,0,.04); }
.side-item.active {
  background: var(--paper); border: 2px solid var(--ink);
  box-shadow: 2px 2px 0 var(--ink); font-weight: 600;
}
.side-item .ico { font-size: 14px; width: 16px; text-align: center; }
.side-item.muted { color: rgba(0,0,0,.5); margin-top: auto; }

/* ── Main pane ───────────────────────────────────────────────────── */
.main { flex: 1; overflow-y: auto; padding: 24px 28px; position: relative; }

.close-btn {
  position: absolute; top: 14px; right: 18px;
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--paper); border: 2px solid var(--ink);
  cursor: pointer; font-size: 13px; font-weight: 600;
  display: grid; place-items: center;
  box-shadow: 2px 2px 0 var(--ink); z-index: 10; color: var(--ink);
}
.close-btn:hover { background: var(--c1); color: var(--paper); }
.close-btn:active { transform: translate(2px, 2px); box-shadow: none; }

.section { display: none; }
.section.active { display: block; }
.section h2 { font-size: 26px; font-weight: 700; letter-spacing: -.8px; margin-bottom: 4px; }
.section .subtitle { font-size: 13px; color: rgba(0,0,0,.6); margin-bottom: 22px; }
.section .subtitle code {
  background: var(--c3); padding: 1px 6px; border-radius: 4px;
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
}

/* ── Setting row (sticker) ───────────────────────────────────────── */
.row {
  background: var(--paper); border: 2.5px solid var(--ink);
  border-radius: 14px; padding: 14px 18px;
  box-shadow: 3px 3px 0 var(--ink);
  display: flex; justify-content: space-between; align-items: center;
  gap: 16px; margin-bottom: 14px;
}
.row.soon { opacity: .55; }
.row-label { min-width: 0; }
.row-label .lbl { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.row-label .hint { font-size: 12px; color: rgba(0,0,0,.55); margin-top: 2px; }
.row-control { flex-shrink: 0; }

.soon-tag {
  font-family: 'JetBrains Mono', monospace; font-size: 9px;
  background: var(--c5); border: 1.5px solid var(--ink);
  border-radius: 999px; padding: 1px 7px; font-weight: 600;
}
.restart-tag {
  font-family: 'JetBrains Mono', monospace; font-size: 9px;
  background: var(--c3); border: 1.5px solid var(--ink);
  border-radius: 999px; padding: 1px 7px; font-weight: 600;
}

/* ── Controls ────────────────────────────────────────────────────── */
.kbd {
  display: inline-block; padding: 4px 10px;
  background: var(--bg); border: 2px solid var(--ink);
  border-radius: 8px; font-family: 'JetBrains Mono', monospace;
  font-size: 12px; font-weight: 600; box-shadow: 2px 2px 0 var(--ink);
}
.plus { color: rgba(0,0,0,.4); margin: 0 3px; font-weight: 700; }

.btn-sm {
  background: var(--paper); border: 2px solid var(--ink);
  border-radius: 999px; padding: 5px 12px; font-family: inherit;
  font-size: 12px; font-weight: 500; cursor: pointer; color: var(--ink);
}
.btn-sm:hover { background: var(--c5); }
.btn-sm:active { transform: translate(1px,1px); }
.btn-sm:disabled { opacity: .5; cursor: not-allowed; }

/* Native select styled as a pill */
select.pick {
  appearance: none; -webkit-appearance: none;
  padding: 6px 30px 6px 12px;
  background: var(--bg);
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%2316140f'/></svg>");
  background-repeat: no-repeat; background-position: right 10px center;
  border: 2px solid var(--ink); border-radius: 8px;
  font-family: inherit; font-size: 13px; font-weight: 500;
  cursor: pointer; color: var(--ink); box-shadow: 2px 2px 0 var(--ink);
}

/* Toggle */
.toggle {
  width: 46px; height: 26px; border-radius: 999px;
  background: var(--bg); border: 2px solid var(--ink);
  position: relative; cursor: pointer;
  box-shadow: 2px 2px 0 var(--ink); transition: background .15s;
}
.toggle.on { background: var(--c4); }
.toggle.disabled { cursor: not-allowed; }
.toggle .knob {
  position: absolute; top: 1px; left: 1px;
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--paper); border: 1.5px solid var(--ink);
  transition: left .15s;
}
.toggle.on .knob { left: 21px; }

/* Model picker */
.models { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.model {
  padding: 6px 10px; background: var(--bg);
  border: 2px solid var(--ink); border-radius: 8px;
  font-size: 12px; text-align: center; cursor: pointer; min-width: 84px;
}
.model.active { background: var(--c4); box-shadow: 2px 2px 0 var(--ink); }
.model .name { font-weight: 600; }
.model .meta { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: rgba(0,0,0,.6); margin-top: 2px; }

/* Range slider (opacity) */
input[type=range].range {
  -webkit-appearance: none; appearance: none;
  width: 180px; height: 6px; border-radius: 3px;
  background: var(--bg); border: 1.5px solid var(--ink); outline: none;
}
input[type=range].range::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--paper); border: 2px solid var(--ink);
  box-shadow: 1px 1px 0 var(--ink); cursor: grab;
}
.range-val { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: rgba(0,0,0,.6); margin-left: 8px; }

/* List management (dictionary + snippets) */
.list-add { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.list-add.snippet-add .input-text:first-child { flex: 0 0 38%; }
.input-text {
  flex: 1; min-width: 120px;
  padding: 9px 12px;
  background: var(--bg); border: 2px solid var(--ink); border-radius: 8px;
  font-family: inherit; font-size: 13px; color: var(--ink);
  outline: none;
}
.input-text:focus { box-shadow: 2px 2px 0 var(--ink); }
.add-btn { padding: 9px 16px; font-size: 13px; flex-shrink: 0; }
.item-list { display: flex; flex-direction: column; gap: 8px; }
.item-row {
  display: flex; align-items: center; gap: 12px;
  background: var(--bg); border: 2px solid var(--ink); border-radius: 10px;
  padding: 8px 8px 8px 14px;
}
.item-row .item-main { flex: 1; min-width: 0; }
.item-row .item-trigger { font-weight: 600; font-size: 13px; }
.item-row .item-arrow { color: rgba(0,0,0,.4); margin: 0 6px; }
.item-row .item-exp {
  font-size: 12px; color: rgba(0,0,0,.6);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.item-row .item-word { font-weight: 600; font-size: 13px; }
.del-btn {
  flex-shrink: 0; width: 28px; height: 28px; border-radius: 8px;
  background: var(--paper); border: 2px solid var(--ink); cursor: pointer;
  font-size: 13px; color: var(--ink); display: grid; place-items: center;
}
.del-btn:hover { background: var(--c1); color: var(--paper); }
.empty-hint { font-size: 12px; color: rgba(0,0,0,.45); font-style: italic; padding: 6px 2px; }
.empty-hint.hide { display: none; }

/* About box */
.about-card {
  background: var(--paper); border: 2.5px solid var(--ink);
  border-radius: 14px; padding: 22px; box-shadow: 4px 4px 0 var(--c1);
  text-align: center;
}
.about-logo {
  width: 78px; height: 78px; border-radius: 22px;
  background: var(--c4); border: 2.5px solid var(--ink);
  box-shadow: 3px 3px 0 var(--ink); margin: 0 auto 14px;
  display: grid; place-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700; font-size: 28px; letter-spacing: -2px;
}
.about-card h3 { font-size: 20px; margin-bottom: 4px; letter-spacing: -.5px; }
.about-card .ver { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: rgba(0,0,0,.6); margin-bottom: 14px; }
.about-card p { font-size: 13px; color: rgba(0,0,0,.7); line-height: 1.5; max-width: 380px; margin: 0 auto 14px; }

/* Saved toast */
.toast {
  position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
  background: var(--c4); border: 2px solid var(--ink); border-radius: 999px;
  padding: 8px 18px; font-size: 13px; font-weight: 600;
  box-shadow: 3px 3px 0 var(--ink); opacity: 0; pointer-events: none;
  transition: opacity .2s, transform .2s; z-index: 50;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(-4px); }

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
    <div class="side-item active" data-target="general"><span class="ico">&#9881;</span> Général</div>
    <div class="side-item" data-target="shortcuts"><span class="ico">&#8984;</span> Raccourcis</div>
    <div class="side-item" data-target="dictionary"><span class="ico">&#128214;</span> Dictionnaire</div>
    <div class="side-item" data-target="snippets"><span class="ico">&#9889;</span> Snippets</div>
    <div class="side-item" data-target="model"><span class="ico">&#129504;</span> Modèle</div>
    <div class="side-item" data-target="audio"><span class="ico">&#127908;</span> Audio</div>
    <div class="side-item muted" data-target="about"><span class="ico">&#9432;</span> À propos</div>
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
          <div class="hint">FreeFlow apparaît dans la barre des tâches au boot</div>
        </div>
        <div class="row-control"><div class="toggle" id="tg-startup" data-key="launch_at_startup"><span class="knob"></span></div></div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Ponctuation automatique</div>
          <div class="hint">ajoute les majuscules et le point final</div>
        </div>
        <div class="row-control"><div class="toggle" id="tg-punct" data-key="auto_punctuation"><span class="knob"></span></div></div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Langue principale</div>
          <div class="hint">la langue dans laquelle tu dictes</div>
        </div>
        <div class="row-control">
          <select class="pick" id="sel-language">
            <option value="auto">🌍 Auto-détection</option>
            <option value="fr">🇫🇷 Français</option>
            <option value="en">🇬🇧 English</option>
            <option value="es">🇪🇸 Español</option>
            <option value="de">🇩🇪 Deutsch</option>
            <option value="it">🇮🇹 Italiano</option>
            <option value="pt">🇵🇹 Português</option>
            <option value="nl">🇳🇱 Nederlands</option>
          </select>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Opacité de l'overlay <span class="restart-tag">au redémarrage</span></div>
          <div class="hint">la barre flottante pendant la dictée</div>
        </div>
        <div class="row-control">
          <input type="range" class="range" id="rng-opacity" min="50" max="100" step="5">
          <span class="range-val" id="opacity-val">85%</span>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Vérifier les mises à jour</div>
          <div class="hint">propose la nouvelle version 1×/jour (via GitHub)</div>
        </div>
        <div class="row-control"><div class="toggle" id="tg-update" data-key="update_check_enabled"><span class="knob"></span></div></div>
      </div>
    </section>

    <!-- ── Raccourcis ── -->
    <section class="section" id="sec-shortcuts">
      <h2>Raccourcis</h2>
      <p class="subtitle">maintiens la combo pour dicter, lâche pour transcrire</p>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Raccourci principal <span class="restart-tag">au redémarrage</span></div>
          <div class="hint" id="hotkey-hint">la touche magique pour dicter</div>
        </div>
        <div class="row-control">
          <span id="hotkey-display"></span>
          <button class="btn-sm" id="btn-hotkey" style="margin-left:8px;">changer</button>
        </div>
      </div>

      <div class="row soon">
        <div class="row-label">
          <div class="lbl">Coller automatiquement <span class="soon-tag">bientôt</span></div>
          <div class="hint">pour l'instant : clique où tu veux coller</div>
        </div>
        <div class="row-control"><div class="toggle disabled"><span class="knob"></span></div></div>
      </div>
    </section>

    <!-- ── Dictionnaire ── -->
    <section class="section" id="sec-dictionary">
      <h2>Dictionnaire</h2>
      <p class="subtitle">apprends à FreeFlow tes noms, marques et mots techniques</p>

      <div class="row" style="flex-direction:column; align-items:stretch;">
        <div class="row-label" style="margin-bottom:12px;">
          <div class="lbl">Mots à mieux reconnaître</div>
          <div class="hint">prénoms, noms de marque, jargon — un par ajout</div>
        </div>
        <div class="list-add">
          <input type="text" class="input-text" id="dict-input" placeholder="ex: WebPrestige, Benjamin, FreeFlow…" maxlength="60">
          <button class="btn add-btn" id="dict-add">+ Ajouter</button>
        </div>
        <div class="item-list" id="dict-list"></div>
        <div class="empty-hint" id="dict-empty">Aucun mot pour l'instant. Ajoute les noms que FreeFlow écrit de travers.</div>
      </div>
    </section>

    <!-- ── Snippets ── -->
    <section class="section" id="sec-snippets">
      <h2>Snippets</h2>
      <p class="subtitle">dis un mot-clé → FreeFlow colle un texte tout prêt</p>

      <div class="row" style="flex-direction:column; align-items:stretch;">
        <div class="row-label" style="margin-bottom:12px;">
          <div class="lbl">Tes raccourcis vocaux</div>
          <div class="hint">ex: dis « mon mail » → colle ton adresse complète</div>
        </div>
        <div class="list-add snippet-add">
          <input type="text" class="input-text" id="snip-trigger" placeholder="quand je dis…  (ex: mon mail)" maxlength="60">
          <input type="text" class="input-text" id="snip-expansion" placeholder="colle ça…  (ex: benjamin@…)" maxlength="500">
          <button class="btn add-btn" id="snip-add">+ Ajouter</button>
        </div>
        <div class="item-list" id="snip-list"></div>
        <div class="empty-hint" id="snip-empty">Aucun snippet. Crée ton premier raccourci vocal.</div>
      </div>
    </section>

    <!-- ── Modèle ── -->
    <section class="section" id="sec-model">
      <h2>Modèle</h2>
      <p class="subtitle">plus gros = plus précis mais plus lent · <span class="restart-tag">au redémarrage</span></p>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Modèle de transcription</div>
          <div class="hint">choisis le compromis vitesse / précision</div>
        </div>
        <div class="row-control">
          <div class="models" id="model-picker">
            <div class="model" data-model="tiny"><div class="name">tiny</div><div class="meta">75 mo · &#9733;&#9733;</div></div>
            <div class="model" data-model="base"><div class="name">base</div><div class="meta">142 mo · &#9733;&#9733;&#9733;</div></div>
            <div class="model" data-model="small"><div class="name">small</div><div class="meta">466 mo · &#9733;&#9733;&#9733;&#9733;</div></div>
            <div class="model" data-model="medium"><div class="name">medium</div><div class="meta">1.5 go · &#9733;&#9733;&#9733;&#9733;&#9733;</div></div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="row-label">
          <div class="lbl">Calcul</div>
          <div class="hint">FreeFlow tourne sur ton processeur (CPU int8)</div>
        </div>
        <div class="row-control"><span class="kbd">CPU · int8</span></div>
      </div>
    </section>

    <!-- ── Audio ── -->
    <section class="section" id="sec-audio">
      <h2>Audio</h2>
      <p class="subtitle">le réglage fin du micro arrive bientôt</p>

      <div class="row soon">
        <div class="row-label">
          <div class="lbl">Périphérique d'entrée <span class="soon-tag">bientôt</span></div>
          <div class="hint">pour l'instant : ton micro Windows par défaut</div>
        </div>
        <div class="row-control"><span class="kbd">micro par défaut</span></div>
      </div>

      <div class="row soon">
        <div class="row-label">
          <div class="lbl">Réduction de bruit <span class="soon-tag">bientôt</span></div>
          <div class="hint">filtre le souffle constant en arrière-plan</div>
        </div>
        <div class="row-control"><div class="toggle disabled"><span class="knob"></span></div></div>
      </div>
    </section>

    <!-- ── À propos ── -->
    <section class="section" id="sec-about">
      <h2>À propos</h2>
      <p class="subtitle">FreeFlow est libre, local et sans compte.</p>
      <div class="about-card">
        <div class="about-logo">ff</div>
        <h3>FreeFlow</h3>
        <div class="ver">version 0.1.1 · MIT</div>
        <p>Une dictée vocale 100 % locale pour Windows. Aucune donnée n'est envoyée sur Internet — ton micro ne quitte jamais ta machine.</p>
        <button class="btn-sm">github.com/Fulflock/FreeFlow</button>
      </div>
    </section>

  </main>
</div>

<div class="toast" id="toast">✓ enregistré</div>

<script>
var CFG = {};
var capturing = false;

function api(){ return (window.pywebview && window.pywebview.api) || null; }

function toast(msg){
  var t = document.getElementById('toast');
  t.textContent = msg || '✓ enregistré';
  t.classList.add('show');
  setTimeout(function(){ t.classList.remove('show'); }, 1400);
}

function save(updates, msg){
  var a = api();
  if (!a){ return; }
  a.save(updates).then(function(newCfg){
    if (newCfg) CFG = newCfg;
    toast(msg || '✓ enregistré');
  });
}

// ── Hotkey rendering ───────────────────────────────────────────────
function prettyKey(k){
  var map = { ctrl:'Ctrl', alt:'Alt', shift:'Maj', space:'Espace', cmd:'Win', win:'Win' };
  if (map[k]) return map[k];
  return k.length === 1 ? k.toUpperCase() : k.charAt(0).toUpperCase()+k.slice(1);
}
function renderHotkey(combo){
  combo = combo && combo.length ? combo : ['ctrl','space'];
  var el = document.getElementById('hotkey-display');
  el.innerHTML = combo.map(function(k,i){
    return (i>0 ? '<span class="plus">+</span>' : '') + '<span class="kbd">'+prettyKey(k)+'</span>';
  }).join('');
}

// ── Lists: custom dictionary + snippets ────────────────────────────
function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

function renderDict(){
  var words = (CFG.custom_words || []);
  var list = document.getElementById('dict-list');
  var empty = document.getElementById('dict-empty');
  empty.classList.toggle('hide', words.length > 0);
  list.innerHTML = words.map(function(w, i){
    return '<div class="item-row"><div class="item-main"><span class="item-word">'
      + esc(w) + '</span></div><button class="del-btn" data-dict="' + i + '" title="supprimer">&#10005;</button></div>';
  }).join('');
}
function renderSnippets(){
  var snips = (CFG.snippets || []);
  var list = document.getElementById('snip-list');
  var empty = document.getElementById('snip-empty');
  empty.classList.toggle('hide', snips.length > 0);
  list.innerHTML = snips.map(function(s, i){
    return '<div class="item-row"><div class="item-main"><span class="item-trigger">'
      + esc(s.trigger) + '</span><span class="item-arrow">&#8594;</span><span class="item-exp">'
      + esc(s.expansion) + '</span></div><button class="del-btn" data-snip="' + i + '" title="supprimer">&#10005;</button></div>';
  }).join('');
}

// ── Apply config to controls ───────────────────────────────────────
function applyToUI(cfg){
  CFG = cfg || {};
  if (!CFG.custom_words) CFG.custom_words = [];
  if (!CFG.snippets) CFG.snippets = [];
  setToggle('tg-startup', !!CFG.launch_at_startup);
  setToggle('tg-punct', CFG.auto_punctuation !== false);
  setToggle('tg-update', CFG.update_check_enabled !== false);
  var sel = document.getElementById('sel-language');
  if (sel) sel.value = CFG.language || 'fr';
  var op = Math.round((CFG.overlay_opacity != null ? CFG.overlay_opacity : 0.85) * 100);
  var rng = document.getElementById('rng-opacity');
  if (rng){ rng.value = op; document.getElementById('opacity-val').textContent = op + '%'; }
  document.querySelectorAll('#model-picker .model').forEach(function(m){
    m.classList.toggle('active', m.getAttribute('data-model') === (CFG.model_size || 'base'));
  });
  renderHotkey(CFG.hotkey_combo);
  renderDict();
  renderSnippets();
}
function setToggle(id, on){
  var t = document.getElementById(id);
  if (t) t.classList.toggle('on', !!on);
}

// ── Wire controls ──────────────────────────────────────────────────
function wire(){
  // Sidebar nav
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

  // Functional toggles
  ['tg-startup','tg-punct','tg-update'].forEach(function(id){
    var t = document.getElementById(id);
    if (!t) return;
    t.addEventListener('click', function(){
      t.classList.toggle('on');
      var key = t.getAttribute('data-key');
      var upd = {}; upd[key] = t.classList.contains('on');
      var msg = '✓ enregistré';
      if (key === 'launch_at_startup') msg = t.classList.contains('on') ? '✓ lancera au démarrage' : '✓ ne se lancera plus au démarrage';
      save(upd, msg);
    });
  });

  // Language
  var sel = document.getElementById('sel-language');
  if (sel) sel.addEventListener('change', function(){ save({ language: sel.value }, '✓ langue : ' + sel.options[sel.selectedIndex].text); });

  // Opacity
  var rng = document.getElementById('rng-opacity');
  if (rng){
    rng.addEventListener('input', function(){ document.getElementById('opacity-val').textContent = rng.value + '%'; });
    rng.addEventListener('change', function(){ save({ overlay_opacity: parseInt(rng.value,10)/100 }, '✓ opacité — au redémarrage'); });
  }

  // Model picker
  document.querySelectorAll('#model-picker .model').forEach(function(m){
    m.addEventListener('click', function(){
      document.querySelectorAll('#model-picker .model').forEach(function(x){ x.classList.remove('active'); });
      m.classList.add('active');
      save({ model_size: m.getAttribute('data-model') }, '✓ modèle ' + m.getAttribute('data-model') + ' — au redémarrage');
    });
  });

  // Hotkey capture
  var btn = document.getElementById('btn-hotkey');
  var hint = document.getElementById('hotkey-hint');
  btn.addEventListener('click', function(){
    if (capturing) return;
    capturing = true;
    btn.textContent = 'appuie…';
    hint.textContent = 'appuie sur ta combinaison (avec Ctrl ou Alt)';
    document.getElementById('hotkey-display').innerHTML = '<span class="kbd">…</span>';
  });
  document.addEventListener('keydown', function(ev){
    if (!capturing) return;
    ev.preventDefault();
    var key = ev.key;
    // Ignore lone modifier presses — wait for the real key.
    if (['Control','Alt','Shift','Meta','OS'].indexOf(key) !== -1) return;
    var mods = [];
    if (ev.ctrlKey) mods.push('ctrl');
    if (ev.altKey) mods.push('alt');
    if (ev.shiftKey) mods.push('shift');
    var main;
    if (ev.code === 'Space') main = 'space';
    else if (/^F\\d{1,2}$/.test(key)) main = key.toLowerCase();
    else if (key.length === 1) main = key.toLowerCase();
    else main = key.toLowerCase();
    var isFunc = /^f\\d{1,2}$/.test(main);
    if (mods.length === 0 && !isFunc){
      hint.textContent = '⚠ ajoute Ctrl ou Alt (sinon tu bloques une touche normale)';
      return;
    }
    var combo = mods.concat([main]);
    capturing = false;
    btn.textContent = 'changer';
    hint.textContent = 'enregistré — actif au prochain démarrage';
    renderHotkey(combo);
    save({ hotkey_combo: combo }, '✓ raccourci — au redémarrage');
  });

  // Dictionary: add
  function addWord(){
    var inp = document.getElementById('dict-input');
    var w = (inp.value || '').trim();
    if (!w) return;
    if (CFG.custom_words.indexOf(w) === -1){
      CFG.custom_words.push(w);
      renderDict();
      save({ custom_words: CFG.custom_words }, '✓ « ' + w +' » ajouté');
    }
    inp.value = '';
    inp.focus();
  }
  document.getElementById('dict-add').addEventListener('click', addWord);
  document.getElementById('dict-input').addEventListener('keydown', function(ev){
    if (ev.key === 'Enter'){ ev.preventDefault(); addWord(); }
  });

  // Snippets: add
  function addSnippet(){
    var t = document.getElementById('snip-trigger');
    var e = document.getElementById('snip-expansion');
    var trig = (t.value || '').trim();
    var exp = (e.value || '').trim();
    if (!trig || !exp) return;
    CFG.snippets.push({ trigger: trig, expansion: exp });
    renderSnippets();
    save({ snippets: CFG.snippets }, '✓ snippet « ' + trig + ' » ajouté');
    t.value = ''; e.value = ''; t.focus();
  }
  document.getElementById('snip-add').addEventListener('click', addSnippet);
  document.getElementById('snip-expansion').addEventListener('keydown', function(ev){
    if (ev.key === 'Enter'){ ev.preventDefault(); addSnippet(); }
  });

  // Delete from either list (event delegation)
  document.addEventListener('click', function(ev){
    var btn = ev.target.closest ? ev.target.closest('.del-btn') : null;
    if (!btn) return;
    if (btn.hasAttribute('data-dict')){
      var i = parseInt(btn.getAttribute('data-dict'), 10);
      CFG.custom_words.splice(i, 1);
      renderDict();
      save({ custom_words: CFG.custom_words }, '✓ supprimé');
    } else if (btn.hasAttribute('data-snip')){
      var j = parseInt(btn.getAttribute('data-snip'), 10);
      CFG.snippets.splice(j, 1);
      renderSnippets();
      save({ snippets: CFG.snippets }, '✓ supprimé');
    }
  });

  // Close
  document.getElementById('close-btn').addEventListener('click', function(){
    var a = api();
    if (a && a.close){ a.close(); return; }
    window.close();
  });
}

function boot(){
  wire();
  var a = api();
  if (a && a.get_config){
    a.get_config().then(function(cfg){ applyToUI(cfg); });
  } else {
    applyToUI({});
  }
}

if (window.pywebview && window.pywebview.api) boot();
else window.addEventListener('pywebviewready', boot);
</script>
</body></html>""".replace("__FONT_FACE_CSS__", FONT_CSS)


class _SettingsApi:
    """Bridge: load current config, persist changes, close the window."""

    def __init__(self, config=None, on_apply=None):
        self._window = None
        self._config = config or {}
        self._on_apply = on_apply or (lambda cfg: None)

    def bind(self, window):
        self._window = window

    def get_config(self):
        # Return the freshest merged view so the UI reflects prior saves too.
        try:
            return load_config()
        except Exception:
            return dict(self._config)

    def save(self, updates):
        """Persist whitelisted keys, then ask the host to apply live ones."""
        try:
            new_cfg = save_config(updates or {})
        except Exception:
            return self.get_config()
        try:
            self._on_apply(new_cfg)
        except Exception:
            pass
        self._config = new_cfg
        return new_cfg

    def close(self):
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass


class SettingsWindow:
    """Standalone settings window — real, persisted to ~/.freeflow/config.json."""

    def __init__(self, config=None, on_apply=None):
        self._window = None
        self._api = _SettingsApi(config=config, on_apply=on_apply)

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
