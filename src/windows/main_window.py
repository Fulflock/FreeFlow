"""FreeFlow Main Window — history + 30-day word-count chart, one page.

Default surface opened when the user double-clicks the desktop shortcut or
left-clicks the tray icon. Sticker-pack pink/cream aesthetic; fully offline
(no CDN, no Chart.js — SVG bars are hand-rolled).
"""

import threading
from datetime import datetime, date, timedelta

import webview

from src.history import DictationHistory
from src.fonts import FONT_CSS


# ── In-memory stats computer ───────────────────────────────────────────────
# Mirrors DictationHistory aggregation methods, but operates on a pre-loaded
# `entries` list to avoid the 6+ filesystem rescans per dashboard render.


class _StatsComputer:
    """Compute aggregates in memory from a single get_all() snapshot.

    Each method mirrors the corresponding DictationHistory method exactly
    (same algorithms / formats) — but without re-reading the JSON files.
    """

    def __init__(self, entries):
        self._entries = entries or []

    def extended(self) -> dict:
        all_e = self._entries
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        week_words = 0
        week_count = 0
        for e in all_e:
            try:
                d = datetime.fromisoformat(e.get("timestamp", "")).date()
            except Exception:
                continue
            if d >= week_start:
                week_words += len((e.get("text") or "").split())
                week_count += 1

        total_words = sum(len((e.get("text") or "").split()) for e in all_e)
        minutes_saved = round(total_words / 40)

        return {
            "total_dictations": len(all_e),
            "total_words": total_words,
            "week_words": week_words,
            "week_dictations": week_count,
            "minutes_saved": minutes_saved,
        }

    def wpm(self) -> dict:
        total_words = 0
        total_minutes = 0.0
        for entry in self._entries:
            dur = float(entry.get("duration_seconds") or 0)
            if dur <= 0.5:
                continue
            words = len((entry.get("text") or "").split())
            if words <= 0:
                continue
            total_words += words
            total_minutes += dur / 60.0

        if total_minutes <= 0 or total_words <= 0:
            return {"avg_wpm": 0.0, "total_minutes_saved": 0}

        avg_wpm = total_words / total_minutes
        if avg_wpm <= 0:
            return {"avg_wpm": 0.0, "total_minutes_saved": 0}

        minutes_saved = total_words * (1.0 / 40.0 - 1.0 / avg_wpm)
        return {
            "avg_wpm": round(avg_wpm, 1),
            "total_minutes_saved": max(0, int(round(minutes_saved))),
        }

    def streak(self) -> dict:
        days_with_activity = set()
        for entry in self._entries:
            day_key = (entry.get("timestamp") or "")[:10]
            if day_key:
                days_with_activity.add(day_key)

        if not days_with_activity:
            return {"current": 0, "longest": 0}

        today = date.today()
        current = 0
        d = today
        while d.isoformat() in days_with_activity:
            current += 1
            d = d - timedelta(days=1)

        sorted_days = sorted(
            datetime.fromisoformat(s).date() for s in days_with_activity
        )
        longest = 1
        run = 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                run += 1
                longest = max(longest, run)
            else:
                run = 1
        longest = max(longest, current)

        return {"current": current, "longest": longest}

    def word_count_per_day(self, days: int = 30) -> list:
        today = date.today()
        buckets = {}
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            buckets[d.isoformat()] = {"date": d.isoformat(), "words": 0, "count": 0}

        for entry in self._entries:
            day_key = (entry.get("timestamp") or "")[:10]
            if day_key in buckets:
                words = len((entry.get("text") or "").split())
                buckets[day_key]["words"] += words
                buckets[day_key]["count"] += 1

        return list(buckets.values())

    def yearly_heatmap(self, end_date=None) -> list:
        end = end_date or date.today()
        buckets = {}
        for i in range(364, -1, -1):
            d = end - timedelta(days=i)
            buckets[d.isoformat()] = {"date": d.isoformat(), "count": 0, "words": 0}

        for entry in self._entries:
            day_key = (entry.get("timestamp") or "")[:10]
            if day_key in buckets:
                words = len((entry.get("text") or "").split())
                buckets[day_key]["count"] += 1
                buckets[day_key]["words"] += words

        return list(buckets.values())

    def hourly_distribution(self) -> list:
        bins = [0] * 24
        for entry in self._entries:
            ts = entry.get("timestamp") or ""
            try:
                h = datetime.fromisoformat(ts).hour
                bins[h] += 1
            except Exception:
                continue
        return bins

    def app_breakdown(self, top_n: int = 5) -> list:
        def _classify(raw):
            low = raw.lower()
            if "freeflow" in low or "free flow" in low or "wispr" in low:
                return None
            if not raw or low == "unknown":
                return "— autres —"
            if (len(raw) >= 3 and raw[1:3] == ":\\") or raw.startswith("/"):
                return "Système"
            if raw[:1] in {"※", "​", "﻿"}:
                return "— autres —"
            return raw

        bucket = {}
        for entry in self._entries:
            raw = (entry.get("app") or "").strip()
            key = _classify(raw)
            if key is None:
                continue
            b = bucket.setdefault(key, {"app": key, "count": 0, "words": 0})
            b["count"] += 1
            b["words"] += len((entry.get("text") or "").split())

        ordered = sorted(bucket.values(), key=lambda x: x["count"], reverse=True)
        return ordered[:top_n]

    def best_dictation_this_week(self):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        best = None
        best_words = -1
        best_dur = -1.0
        for entry in self._entries:
            try:
                d = datetime.fromisoformat(entry.get("timestamp", "")).date()
            except Exception:
                continue
            if d < week_start:
                continue
            words = len((entry.get("text") or "").split())
            dur = float(entry.get("duration_seconds") or 0)
            if words > best_words or (words == best_words and dur > best_dur):
                best_words = words
                best_dur = dur
                best = entry

        if not best:
            return None
        return {
            "id": best.get("id"),
            "timestamp": best.get("timestamp"),
            "text": best.get("text") or "",
            "words": best_words,
            "app": best.get("app") or "",
            "duration": float(best.get("duration_seconds") or 0),
        }


# ── Python ↔ JS bridge ─────────────────────────────────────────────────────


class _MainApi:
    """Exposed as window.pywebview.api in the WebView."""

    def __init__(self):
        self._window = None
        self._history = DictationHistory()

    def bind(self, window):
        self._window = window

    def get_history(self):
        try:
            entries = self._history.get_all() or []
            entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
            return entries
        except Exception:
            return []

    def get_stats(self, days=30):
        try:
            # Single I/O read — all aggregations below run in-memory.
            entries = self._history.get_all() or []
            sc = _StatsComputer(entries)

            summary = sc.extended()
            wpm = sc.wpm()
            streak = sc.streak()
            avg_wpm = float(wpm.get("avg_wpm") or 0)
            multiplier = round(avg_wpm / 40.0, 1) if avg_wpm > 0 else 0
            summary.update({
                "avg_wpm": avg_wpm,
                "wpm_multiplier": multiplier,
                "current_streak": int(streak.get("current") or 0),
                "longest_streak": int(streak.get("longest") or 0),
            })

            hourly = sc.hourly_distribution()
            apps = sc.app_breakdown()
            best = sc.best_dictation_this_week()

            peak_hour = 0
            peak_val = -1
            for i, v in enumerate(hourly):
                if v > peak_val:
                    peak_val = v
                    peak_hour = i
            top_app_count = apps[0]["count"] if apps else 0
            voiceprint_seed = {
                "total_dictations": int(summary.get("total_dictations") or 0),
                "total_words": int(summary.get("total_words") or 0),
                "streak": int(streak.get("current") or 0),
                "peak_hour": peak_hour,
                "top_app_count": int(top_app_count),
            }

            return {
                "summary": summary,
                "per_day": sc.word_count_per_day(days),
                "yearly_heatmap": sc.yearly_heatmap(),
                "hourly_dist": hourly,
                "app_breakdown": apps,
                "best_week": best,
                "voiceprint_seed": voiceprint_seed,
            }
        except Exception:
            return {
                "summary": {}, "per_day": [], "yearly_heatmap": [],
                "hourly_dist": [0] * 24, "app_breakdown": [],
                "best_week": None, "voiceprint_seed": {},
            }

    def copy_to_clipboard(self, text):
        try:
            import pyperclip
            pyperclip.copy(text or "")
            return True
        except Exception:
            return False

    def paste_again(self, text):
        try:
            from src.injector import paste_at_cursor
            threading.Thread(
                target=lambda: paste_at_cursor(text or ""),
                daemon=True,
            ).start()
            return True
        except Exception:
            return False

    def delete_entry(self, entry_id):
        try:
            return bool(self._history.delete_entry(entry_id))
        except Exception:
            return False


_HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>FreeFlow</title>
<style>
__FONT_FACE_CSS__
:root{--c1:#ff5d8f;--c3:#a8e6cf;--c4:#c4e86b;--c5:#ffd166;--ink:#16140f;--paper:#fffdf7;--bg:#f4f0e8;}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;background:radial-gradient(rgba(0,0,0,.05) 1px,transparent 1px) 0 0/22px 22px,var(--bg);font-family:'Space Grotesk','Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;color:var(--ink);}
body{display:flex;flex-direction:column;overflow-x:hidden;}
.scroll{flex:1;overflow-y:auto;}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;padding:22px 28px 12px;gap:18px;flex-shrink:0;}
.brand-row{display:flex;align-items:center;gap:12px;}
.logo-dot{width:38px;height:34px;flex-shrink:0;filter:drop-shadow(0 3px 6px rgba(255,93,143,.4));}
.title{font-size:26px;font-weight:700;letter-spacing:-.8px;}
.subtitle{font-size:12px;color:rgba(0,0,0,.55);margin-top:2px;font-family:'JetBrains Mono',monospace;}
.wpm-pill{display:inline-flex;align-items:center;gap:6px;margin-top:6px;font-family:'JetBrains Mono',monospace;font-size:11px;background:var(--paper);border:1.5px solid var(--ink);border-radius:999px;padding:3px 10px;box-shadow:2px 2px 0 var(--c5);}
.wpm-pill.hide{display:none;}
.voiceprint{width:56px;height:56px;flex-shrink:0;cursor:pointer;filter:drop-shadow(0 2px 4px rgba(255,93,143,.3));}
.stats-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:0 28px 14px;}
.stat-card{position:relative;background:var(--paper);border:2.5px solid var(--ink);border-radius:14px;padding:12px 14px;box-shadow:3px 3px 0 var(--ink);display:flex;flex-direction:column;gap:2px;overflow:hidden;}
.stat-card.c1{box-shadow:3px 3px 0 var(--c1);}
.stat-card.c3{box-shadow:3px 3px 0 var(--c3);}
.stat-card.c4{box-shadow:3px 3px 0 var(--c4);}
.stat-card.c5{box-shadow:3px 3px 0 var(--c5);}
.stat-num{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;letter-spacing:-.5px;position:relative;z-index:2;}
.stat-label{font-size:11px;color:rgba(0,0,0,.6);text-transform:lowercase;position:relative;z-index:2;}
.spark{position:absolute;left:0;right:0;bottom:0;height:32px;opacity:.45;z-index:1;}
.streak-dots{display:flex;gap:3px;margin-top:6px;position:relative;z-index:2;}
.streak-dots span{width:6px;height:6px;border-radius:50%;background:var(--bg);border:1px solid var(--ink);}
.streak-dots span.on{background:var(--c5);}
.chart-card{margin:0 28px 18px;background:var(--paper);border:2.5px solid var(--ink);border-radius:14px;padding:14px 16px 8px;box-shadow:4px 4px 0 var(--ink);}
.chart-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;}
.chart-title{font-size:13px;font-weight:600;}
.chart-meta{font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(0,0,0,.5);}
.chart-wrap{width:100%;}
.chart-wrap svg{display:block;width:100%;height:140px;}
.chart-axis{display:flex;justify-content:space-between;margin-top:4px;font-family:'JetBrains Mono',monospace;font-size:9px;color:rgba(0,0,0,.4);}
.heatmap-card{margin:0 28px 18px;background:var(--paper);border:2.5px solid var(--ink);border-radius:14px;padding:14px 16px;box-shadow:4px 4px 0 var(--ink);}
.heatmap-wrap{width:100%;overflow-x:auto;}
.heatmap-wrap svg{display:block;height:auto;}
.legend{display:flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:9px;color:rgba(0,0,0,.5);justify-content:flex-end;margin-top:6px;}
.legend-sq{width:10px;height:10px;border:1px solid var(--ink);border-radius:2px;}
.dual-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:0 28px 18px;}
.dual-card{background:var(--paper);border:2.5px solid var(--ink);border-radius:14px;padding:14px 16px;box-shadow:4px 4px 0 var(--ink);}
.dual-card svg{display:block;width:100%;height:200px;}
.dual-card .donut-legend{margin-top:8px;display:flex;flex-direction:column;gap:4px;}
.dual-card .donut-legend .lg-row{display:flex;align-items:center;gap:8px;font-size:11px;}
.dual-card .donut-legend .lg-dot{width:10px;height:10px;border-radius:50%;border:1.5px solid var(--ink);flex-shrink:0;}
.dual-card .donut-legend .lg-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.dual-card .donut-legend .lg-pct{font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(0,0,0,.55);}
.best-card{margin:0 28px 18px;background:var(--paper);border:2.5px solid var(--ink);border-left:5px solid var(--c1);border-radius:14px;padding:14px 18px;box-shadow:4px 4px 0 var(--c1);}
.best-card.hide{display:none;}
.best-head{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.best-head .trophy{font-size:18px;}
.best-head .title-row{flex:1;}
.best-head h4{font-size:14px;font-weight:600;letter-spacing:-.3px;}
.best-head .meta-line{font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(0,0,0,.55);}
.best-card .text{font-size:13px;line-height:1.5;color:rgba(0,0,0,.85);margin:8px 0 10px;white-space:pre-wrap;word-break:break-word;}
.best-card .row-actions{display:flex;gap:6px;}
.search-row{margin:0 28px 12px;background:var(--paper);border:2.5px solid var(--ink);border-radius:14px;box-shadow:3px 3px 0 var(--ink);padding:10px 14px;display:flex;align-items:center;gap:12px;}
.search-row .icon{font-size:14px;color:rgba(0,0,0,.5);}
.search-row input{flex:1;border:none;outline:none;background:transparent;font:inherit;font-size:14px;padding:4px 0;color:var(--ink);}
.search-row input::placeholder{color:rgba(0,0,0,.4);}
.chips{display:flex;gap:6px;padding-left:10px;border-left:1px solid rgba(0,0,0,.12);}
.chip{font-size:11px;font-weight:500;padding:4px 10px;border-radius:999px;border:1.5px solid var(--ink);background:var(--bg);cursor:pointer;user-select:none;}
.chip.active{background:var(--c1);color:var(--ink);}
.list{padding:4px 28px 22px;display:flex;flex-direction:column;gap:10px;}
.entry{background:var(--paper);border:2.5px solid var(--ink);border-radius:14px;padding:14px 16px;box-shadow:3px 3px 0 var(--ink);}
.entry .head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:10px;}
.entry .meta{display:flex;align-items:center;gap:8px;}
.entry .stamp{font-family:'JetBrains Mono',monospace;font-size:11px;color:rgba(0,0,0,.6);}
.entry .app-name{font-size:12px;font-weight:600;background:var(--c3);border:1.5px solid var(--ink);border-radius:6px;padding:1px 8px;}
.badge{font-family:'JetBrains Mono',monospace;font-size:10px;background:var(--bg);border:1.5px solid var(--ink);border-radius:999px;padding:1px 8px;}
.entry .text{font-size:14px;line-height:1.45;color:rgba(0,0,0,.88);margin-bottom:10px;white-space:pre-wrap;word-break:break-word;}
.row-actions{display:flex;gap:6px;}
.badge.saved{background:var(--c4);border:1.5px solid var(--ink);color:var(--ink);font-weight:700;font-family:'JetBrains Mono',monospace;box-shadow:1.5px 1.5px 0 var(--ink);padding:2px 8px;}
.best-saved{display:inline-flex;align-items:center;gap:6px;margin-top:6px;font-family:'JetBrains Mono',monospace;font-size:12px;background:var(--c4);border:1.5px solid var(--ink);border-radius:999px;padding:3px 12px;box-shadow:2px 2px 0 var(--ink);font-weight:600;}
.btn-sm{background:var(--paper);border:2px solid var(--ink);border-radius:999px;padding:4px 12px;font-family:inherit;font-size:12px;font-weight:500;cursor:pointer;color:var(--ink);}
.btn-sm:hover{background:var(--c5);}
.btn-sm:active{transform:translate(1px,1px);}
.btn-sm.primary{background:var(--c4);}
.btn-sm.danger:hover{background:var(--c1);color:var(--paper);}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;text-align:center;color:rgba(0,0,0,.7);}
.empty svg.bubble{width:110px;height:96px;margin-bottom:16px;}
.empty h3{font-size:22px;letter-spacing:-.5px;margin-bottom:6px;}
.empty p{font-size:14px;color:rgba(0,0,0,.6);max-width:360px;line-height:1.5;}
.empty .hint{margin-top:16px;font-family:'JetBrains Mono',monospace;font-size:12px;padding:6px 12px;background:var(--paper);border:2px solid var(--ink);border-radius:999px;box-shadow:2px 2px 0 var(--ink);}
::-webkit-scrollbar{width:8px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(0,0,0,.18);border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.3);}
#confetti{position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:9999;}
.confetti-piece{position:absolute;width:8px;height:14px;top:-20px;border-radius:2px;animation:confetti-fall 2s ease-in forwards;}
@keyframes confetti-fall{0%{transform:translateY(0) rotate(0deg);opacity:1;}100%{transform:translateY(120vh) rotate(720deg);opacity:0;}}
.toast{position:fixed;top:14px;left:50%;transform:translateX(-50%);background:var(--paper);border:2.5px solid var(--ink);border-radius:999px;padding:8px 16px;font-size:13px;font-weight:600;box-shadow:3px 3px 0 var(--c1);z-index:10000;animation:toast-in .25s ease-out;}
@keyframes toast-in{from{opacity:0;transform:translate(-50%,-12px);}to{opacity:1;transform:translate(-50%,0);}}
@media (max-width: 760px){.stats-strip{grid-template-columns:repeat(2,1fr);}.dual-row{grid-template-columns:1fr;}}
</style></head><body>
<div class="topbar">
  <div class="brand-row">
    <svg class="logo-dot" viewBox="0 0 64 56">
      <path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z" fill="#ff5d8f" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/>
      <g fill="#16140f"><path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/><path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/></g>
    </svg>
    <div><div class="title">FreeFlow</div><div class="subtitle">~/.freeflow · stocke en local</div><div class="wpm-pill hide" id="wpm-pill"></div></div>
  </div>
  <svg class="voiceprint" id="voiceprint" viewBox="0 0 56 56" title="Ton voiceprint"></svg>
</div>
<div class="scroll">
<div class="stats-strip" id="stats-strip"></div>
<div class="heatmap-card">
  <div class="chart-head"><div class="chart-title">Année de dictée</div><div class="chart-meta" id="heatmap-meta">—</div></div>
  <div class="heatmap-wrap" id="heatmap-wrap"><svg></svg></div>
  <div class="legend">moins <span class="legend-sq" style="background:var(--bg);opacity:.5;"></span><span class="legend-sq" style="background:#ff5d8f;opacity:.25;"></span><span class="legend-sq" style="background:#ff5d8f;opacity:.5;"></span><span class="legend-sq" style="background:#ff5d8f;opacity:.75;"></span><span class="legend-sq" style="background:#ff5d8f;"></span> plus</div>
</div>
<div class="chart-card">
  <div class="chart-head"><div class="chart-title">Mots dictes — 30 derniers jours</div><div class="chart-meta" id="chart-meta">—</div></div>
  <div class="chart-wrap" id="chart-wrap"><svg></svg></div>
  <div class="chart-axis" id="chart-axis"></div>
</div>
<div class="dual-row">
  <div class="dual-card">
    <div class="chart-head"><div class="chart-title">Tes heures de dictée</div><div class="chart-meta" id="clock-meta">—</div></div>
    <div id="clock-wrap"><svg viewBox="0 0 200 200"></svg></div>
  </div>
  <div class="dual-card">
    <div class="chart-head"><div class="chart-title">Où tu dictes le plus</div><div class="chart-meta" id="donut-meta">—</div></div>
    <div id="donut-wrap"><svg viewBox="0 0 200 200"></svg></div>
    <div class="donut-legend" id="donut-legend"></div>
  </div>
</div>
<div class="best-card hide" id="best-card">
  <div class="best-head">
    <span class="trophy">🏆</span>
    <div class="title-row"><h4>La pépite de la semaine</h4><div class="meta-line" id="best-meta">—</div></div>
  </div>
  <div class="text" id="best-text">—</div>
  <div class="row-actions"><button class="btn-sm primary" id="best-copy">⏎ Copier</button><button class="btn-sm" id="best-paste">↺ Renvoyer</button></div>
</div>
<div class="search-row" id="search-row" style="display:none;">
  <span class="icon">&#128269;</span>
  <input id="search" placeholder="cherche dans tes dictees..." />
  <div class="chips"><span class="chip active" data-filter="all">Tout</span><span class="chip" data-filter="today">Aujourd'hui</span><span class="chip" data-filter="week">Cette semaine</span></div>
</div>
<div class="list" id="list"></div>
</div>
<div id="confetti"></div>
<script>
var ENTRIES=[],CURRENT_FILTER='all',CURRENT_QUERY='',CACHED_STATS=null,BEST_ENTRY=null,COLORS=['#ff5d8f','#a8e6cf','#c4e86b','#ffd166'];
function esc(s){return (s||'').replace(/[&<>"']/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];});}
function humanizeStamp(iso){if(!iso)return '';var d=new Date(iso);if(isNaN(d))return iso;var today=new Date();today.setHours(0,0,0,0);var dt=new Date(d);dt.setHours(0,0,0,0);var diff=(today-dt)/86400000;var hh=String(d.getHours()).padStart(2,'0');var mm=String(d.getMinutes()).padStart(2,'0');if(diff===0)return "aujourd'hui &middot; "+hh+':'+mm;if(diff===1)return 'hier &middot; '+hh+':'+mm;return d.toLocaleDateString('fr-FR')+' &middot; '+hh+':'+mm;}
function isToday(iso){if(!iso)return false;var d=new Date(iso);var t=new Date();return d.getFullYear()===t.getFullYear()&&d.getMonth()===t.getMonth()&&d.getDate()===t.getDate();}
function isThisWeek(iso){if(!iso)return false;var d=new Date(iso);var t=new Date();var monday=new Date(t);monday.setDate(t.getDate()-((t.getDay()+6)%7));monday.setHours(0,0,0,0);return d>=monday;}
function easeOutCubic(t){return 1-Math.pow(1-t,3);}
function animateCount(el,target,suffix,dur){target=target||0;dur=dur||800;var start=performance.now();function step(now){var t=Math.min(1,(now-start)/dur);var v=Math.round(easeOutCubic(t)*target);el.textContent=v+(suffix||'');if(t<1)requestAnimationFrame(step);}requestAnimationFrame(step);}
function sparklinePath(values,W,H){if(!values||!values.length)return '';var max=1;for(var i=0;i<values.length;i++){if(values[i]>max)max=values[i];}var step=W/Math.max(1,values.length-1);var pts=values.map(function(v,i){return [i*step,H-(v/max)*(H-2)-1];});var d='M '+pts[0][0].toFixed(1)+' '+pts[0][1].toFixed(1);for(var i=1;i<pts.length;i++){d+=' L '+pts[i][0].toFixed(1)+' '+pts[i][1].toFixed(1);}return d;}
function renderChart(perDay){var svg=document.querySelector('#chart-wrap svg');var W=svg.parentNode.clientWidth||800;var H=140;svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('width',W);svg.setAttribute('height',H);var max=1;for(var i=0;i<perDay.length;i++){if(perDay[i].words>max)max=perDay[i].words;}var gap=3;var barW=Math.max(4,(W-gap*(perDay.length-1))/perDay.length);var ink='#16140f',pink='#ff5d8f',bg='#f4f0e8';var parts=[];parts.push('<line x1="0" y1="'+(H-1)+'" x2="'+W+'" y2="'+(H-1)+'" stroke="'+ink+'" stroke-width="1.5" stroke-dasharray="3,3" opacity=".3"/>');for(var i=0;i<perDay.length;i++){var d=perDay[i];var x=i*(barW+gap);var h=max>0?(d.words/max)*(H-14):0;var y=H-h-1;var fill=d.words===0?bg:pink;var op=d.words===0?0.6:1;parts.push('<rect x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" width="'+barW.toFixed(1)+'" height="'+Math.max(2,h).toFixed(1)+'" rx="2" ry="2" fill="'+fill+'" stroke="'+ink+'" stroke-width="1.5" opacity="'+op+'"><title>'+d.date+' — '+d.words+' mots ('+d.count+' dictees)</title></rect>');}svg.innerHTML=parts.join('');var axis=document.getElementById('chart-axis');axis.innerHTML='';var marks=[0,Math.floor(perDay.length*0.25),Math.floor(perDay.length*0.5),Math.floor(perDay.length*0.75),perDay.length-1];marks.forEach(function(idx){var d=perDay[idx];if(!d)return;var lbl=d.date.slice(5);var sp=document.createElement('span');sp.textContent=lbl;axis.appendChild(sp);});document.getElementById('chart-meta').textContent='max '+max+' mots / jour';}
function renderStats(s,per_day,heatmap){var strip=document.getElementById('stats-strip');var weekSpark=(per_day||[]).slice(-7).map(function(d){return d.words||0;});var monthlyBuckets={};(heatmap||[]).forEach(function(d){var k=d.date.slice(0,7);monthlyBuckets[k]=(monthlyBuckets[k]||0)+(d.count||0);});var monthsArr=Object.keys(monthlyBuckets).sort().slice(-12).map(function(k){return monthlyBuckets[k];});var streakCur=s.current_streak||0;var streakLong=s.longest_streak||0;var dotsHtml='';for(var i=13;i>=0;i--){var on=i<streakCur;dotsHtml+='<span class="'+(on?'on':'')+'"></span>';}var sp1=sparklinePath(weekSpark,140,28);var sp2=sparklinePath(monthsArr.length?monthsArr:[0,0,0],140,28);strip.innerHTML='<div class="stat-card c1"><div class="stat-num" data-val="'+(s.week_words||0)+'">0</div><div class="stat-label">mots cette semaine</div><svg class="spark" viewBox="0 0 140 32" preserveAspectRatio="none"><path d="'+sp1+'" stroke="#ff5d8f" stroke-width="2" fill="none" stroke-linecap="round"/></svg></div><div class="stat-card c3"><div class="stat-num" data-val="'+(s.total_dictations||0)+'">0</div><div class="stat-label">dictees au total</div><svg class="spark" viewBox="0 0 140 32" preserveAspectRatio="none"><path d="'+sp2+'" stroke="#a8e6cf" stroke-width="2" fill="none" stroke-linecap="round"/></svg></div><div class="stat-card c4"><div class="stat-num" data-val="'+(s.minutes_saved||0)+'" data-suffix=" min">0</div><div class="stat-label">temps gagne</div></div><div class="stat-card c5"><div class="stat-num" data-val="'+streakCur+'" data-suffix=" j '+(streakCur>=2?'🔥':'')+'">0</div><div class="stat-label">streak (max '+streakLong+')</div><div class="streak-dots">'+dotsHtml+'</div></div>';strip.querySelectorAll('.stat-num').forEach(function(el){animateCount(el,parseInt(el.getAttribute('data-val'),10),el.getAttribute('data-suffix')||'',800);});}
function renderHeatmap(data){var svg=document.querySelector('#heatmap-wrap svg');var cell=11,gap=2,topPad=16,leftPad=24;var cols=53;var W=leftPad+cols*(cell+gap);var H=topPad+7*(cell+gap);svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('width',W);svg.setAttribute('height',H);var parts=[];var totalCount=0,activeDays=0;var firstDay=data.length?new Date(data[0].date):new Date();var firstWeekday=firstDay.getDay();var monthLabels={};for(var i=0;i<data.length;i++){var d=data[i];var dayIdx=firstWeekday+i;var col=Math.floor(dayIdx/7);var row=dayIdx%7;var x=leftPad+col*(cell+gap);var y=topPad+row*(cell+gap);var w=d.words||0;var c=d.count||0;totalCount+=c;if(c>0)activeDays++;var fill='#f4f0e8',op=.5;if(w>=1&&w<=2){fill='#ff5d8f';op=.25;}else if(w>=3&&w<=10){fill='#ff5d8f';op=.5;}else if(w>=11&&w<=30){fill='#ff5d8f';op=.75;}else if(w>30){fill='#ff5d8f';op=1;}parts.push('<rect x="'+x+'" y="'+y+'" width="'+cell+'" height="'+cell+'" rx="2" ry="2" fill="'+fill+'" opacity="'+op+'" stroke="#16140f" stroke-width=".8"><title>'+d.date+' — '+w+' mots ('+c+' dictees)</title></rect>');var monthKey=d.date.slice(0,7);if(!monthLabels[monthKey]){monthLabels[monthKey]={col:col,name:d.date.slice(5,7)};}}var monthNames=['','jan','fev','mar','avr','mai','juin','juil','aout','sept','oct','nov','dec'];Object.keys(monthLabels).forEach(function(k){var ml=monthLabels[k];var mn=monthNames[parseInt(ml.name,10)];parts.push('<text x="'+(leftPad+ml.col*(cell+gap))+'" y="11" font-family="JetBrains Mono,monospace" font-size="9" fill="rgba(0,0,0,.4)">'+mn+'</text>');});var dayLabels=['','L','','M','','V',''];for(var r=0;r<7;r++){if(dayLabels[r]){parts.push('<text x="2" y="'+(topPad+r*(cell+gap)+9)+'" font-family="JetBrains Mono,monospace" font-size="8" fill="rgba(0,0,0,.4)">'+dayLabels[r]+'</text>');}}svg.innerHTML=parts.join('');document.getElementById('heatmap-meta').textContent=activeDays+' jours actifs · '+totalCount+' dictees';}
function renderClock(hourly){var svg=document.querySelector('#clock-wrap svg');var cx=100,cy=100,rIn=28,rOut=88;var max=1;for(var i=0;i<hourly.length;i++){if(hourly[i]>max)max=hourly[i];}var peakH=0,peakV=-1;for(var i=0;i<24;i++){if(hourly[i]>peakV){peakV=hourly[i];peakH=i;}}var parts=[];parts.push('<circle cx="'+cx+'" cy="'+cy+'" r="'+(rOut+2)+'" fill="none" stroke="#16140f" stroke-width="1" opacity=".2" stroke-dasharray="2,3"/>');for(var i=0;i<24;i++){var ang=(i/24)*2*Math.PI-Math.PI/2;var v=hourly[i]||0;var len=max>0?(v/max)*(rOut-rIn):0;var x1=cx+Math.cos(ang)*rIn;var y1=cy+Math.sin(ang)*rIn;var x2=cx+Math.cos(ang)*(rIn+Math.max(2,len));var y2=cy+Math.sin(ang)*(rIn+Math.max(2,len));var col=v===0?'#f4f0e8':'#ff5d8f';var op=v===0?.5:.95;parts.push('<line x1="'+x1.toFixed(1)+'" y1="'+y1.toFixed(1)+'" x2="'+x2.toFixed(1)+'" y2="'+y2.toFixed(1)+'" stroke="'+col+'" stroke-width="6" stroke-linecap="round" opacity="'+op+'"><title>'+i+'h — '+v+' dictees</title></line>');}var labels=[[0,'0h'],[6,'6h'],[12,'12h'],[18,'18h']];labels.forEach(function(p){var i=p[0],txt=p[1];var ang=(i/24)*2*Math.PI-Math.PI/2;var lx=cx+Math.cos(ang)*(rOut+10);var ly=cy+Math.sin(ang)*(rOut+10)+3;parts.push('<text x="'+lx.toFixed(1)+'" y="'+ly.toFixed(1)+'" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="rgba(0,0,0,.55)">'+txt+'</text>');});parts.push('<circle cx="'+cx+'" cy="'+cy+'" r="'+rIn+'" fill="#fffdf7" stroke="#16140f" stroke-width="2"/>');var peakTxt=peakV>0?'Pic à '+peakH+'h':'pas encore';parts.push('<text x="'+cx+'" y="'+(cy-2)+'" text-anchor="middle" font-family="Space Grotesk,sans-serif" font-size="11" font-weight="700" fill="#16140f">'+peakTxt+'</text>');if(peakV>0){parts.push('<text x="'+cx+'" y="'+(cy+11)+'" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8" fill="rgba(0,0,0,.5)">'+peakV+' dictees</text>');}svg.innerHTML=parts.join('');document.getElementById('clock-meta').textContent='24h';}
function renderDonut(apps,totalDict){var svg=document.querySelector('#donut-wrap svg');var leg=document.getElementById('donut-legend');var cx=100,cy=100,rOut=80,rIn=50;if(!apps||!apps.length){var ph='';for(var i=0;i<6;i++){var a1=i*Math.PI/3,a2=(i+1)*Math.PI/3;var p1x=cx+Math.cos(a1)*rOut,p1y=cy+Math.sin(a1)*rOut;var p2x=cx+Math.cos(a2)*rOut,p2y=cy+Math.sin(a2)*rOut;var p3x=cx+Math.cos(a2)*rIn,p3y=cy+Math.sin(a2)*rIn;var p4x=cx+Math.cos(a1)*rIn,p4y=cy+Math.sin(a1)*rIn;ph+='<path d="M '+p1x.toFixed(1)+' '+p1y.toFixed(1)+' A '+rOut+' '+rOut+' 0 0 1 '+p2x.toFixed(1)+' '+p2y.toFixed(1)+' L '+p3x.toFixed(1)+' '+p3y.toFixed(1)+' A '+rIn+' '+rIn+' 0 0 0 '+p4x.toFixed(1)+' '+p4y.toFixed(1)+' Z" fill="#f4f0e8" stroke="#16140f" stroke-width="1.5" opacity=".5"/>';}svg.innerHTML=ph+'<text x="'+cx+'" y="'+(cy-2)+'" text-anchor="middle" font-family="Space Grotesk,sans-serif" font-size="11" font-weight="700" fill="#16140f">— pas encore —</text><text x="'+cx+'" y="'+(cy+12)+'" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8" fill="rgba(0,0,0,.5)">tracking d\'app bientôt</text>';leg.innerHTML='<div class="lg-row" style="color:rgba(0,0,0,.55);font-style:italic;">Active le tracking d\'app — bientôt</div>';document.getElementById('donut-meta').textContent='';return;}var total=0;apps.forEach(function(a){total+=a.count||0;});if(total===0){total=1;}var ang=-Math.PI/2;var parts=[];apps.forEach(function(a,i){var frac=(a.count||0)/total;var a2=ang+frac*2*Math.PI;var col=COLORS[i%COLORS.length];var p1x=cx+Math.cos(ang)*rOut,p1y=cy+Math.sin(ang)*rOut;var p2x=cx+Math.cos(a2)*rOut,p2y=cy+Math.sin(a2)*rOut;var p3x=cx+Math.cos(a2)*rIn,p3y=cy+Math.sin(a2)*rIn;var p4x=cx+Math.cos(ang)*rIn,p4y=cy+Math.sin(ang)*rIn;var large=frac>0.5?1:0;parts.push('<path d="M '+p1x.toFixed(1)+' '+p1y.toFixed(1)+' A '+rOut+' '+rOut+' 0 '+large+' 1 '+p2x.toFixed(1)+' '+p2y.toFixed(1)+' L '+p3x.toFixed(1)+' '+p3y.toFixed(1)+' A '+rIn+' '+rIn+' 0 '+large+' 0 '+p4x.toFixed(1)+' '+p4y.toFixed(1)+' Z" fill="'+col+'" stroke="#16140f" stroke-width="2"><title>'+esc(a.app)+' — '+a.count+' dictees</title></path>');ang=a2;});parts.push('<circle cx="'+cx+'" cy="'+cy+'" r="'+(rIn-1)+'" fill="#fffdf7" stroke="#16140f" stroke-width="2"/>');parts.push('<text x="'+cx+'" y="'+(cy-4)+'" text-anchor="middle" font-family="Space Grotesk,sans-serif" font-size="20" font-weight="700" fill="#16140f">'+(totalDict||total)+'</text>');parts.push('<text x="'+cx+'" y="'+(cy+12)+'" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="rgba(0,0,0,.55)">dans '+apps.length+' apps</text>');svg.innerHTML=parts.join('');var legHtml=apps.map(function(a,i){var pct=Math.round((a.count||0)*100/total);var col=COLORS[i%COLORS.length];return '<div class="lg-row"><span class="lg-dot" style="background:'+col+';"></span><span class="lg-name" title="'+esc(a.app)+'">'+esc(a.app.slice(0,32))+'</span><span class="lg-pct">'+pct+'%</span></div>';}).join('');leg.innerHTML=legHtml;document.getElementById('donut-meta').textContent=total+' dictees';}
function formatSaved(words,durSec){var typingSec=(words||0)/40*60;var saved=Math.max(0,typingSec-(durSec||0));if(saved<60)return Math.round(saved)+'s gagnees';var m=Math.floor(saved/60);var s=Math.round(saved%60);return s>0?m+'m '+s+'s gagnees':m+' min gagnees';}
function renderBest(best){var card=document.getElementById('best-card');if(!best){card.classList.add('hide');return;}BEST_ENTRY=best;card.classList.remove('hide');var txt=(best.text||'').slice(0,240);if((best.text||'').length>240)txt+='...';document.getElementById('best-meta').innerHTML=esc(best.app||'')+' &middot; '+humanizeStamp(best.timestamp)+' &middot; '+best.words+' mots &middot; '+Math.round(best.duration||0)+'s &middot; <span style="color:var(--ink);font-weight:600">&#9201; '+formatSaved(best.words,best.duration)+'</span>';document.getElementById('best-text').textContent=txt;}
function renderWpm(s){var pill=document.getElementById('wpm-pill');var wpm=s.avg_wpm||0;var mult=s.wpm_multiplier||0;if(!wpm||wpm<=0){pill.classList.add('hide');return;}pill.classList.remove('hide');pill.innerHTML='🎙️ Tu parles à '+Math.round(wpm)+' wpm — '+mult+'× plus vite que de taper';}
function hash32(s){s=String(s);var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=(h*16777619)>>>0;}return h>>>0;}
function rand01(seed){return ((seed*9301+49297)%233280)/233280;}
function renderVoiceprint(seed){var svg=document.getElementById('voiceprint');seed=seed||{};var key=(seed.total_dictations||0)+'-'+(seed.total_words||0)+'-'+(seed.streak||0)+'-'+(seed.peak_hour||0)+'-'+(seed.top_app_count||0);var h=hash32(key);var sides=6+(h%3);var cx=28,cy=28,baseR=20;var pts=[];for(var i=0;i<sides;i++){var ang=(i/sides)*2*Math.PI-Math.PI/2;var jitter=rand01(h+i*131);var r=baseR*(0.75+jitter*0.5);pts.push([cx+Math.cos(ang)*r,cy+Math.sin(ang)*r]);}var d='M '+pts[0][0].toFixed(1)+' '+pts[0][1].toFixed(1);for(var i=1;i<pts.length;i++){var prev=pts[i-1],cur=pts[i];var midx=(prev[0]+cur[0])/2,midy=(prev[1]+cur[1])/2;d+=' Q '+prev[0].toFixed(1)+' '+prev[1].toFixed(1)+' '+midx.toFixed(1)+' '+midy.toFixed(1);}d+=' Z';var act=Math.min(1,(seed.total_dictations||0)/100);var op=0.35+act*0.5;var innerR=baseR*0.45;svg.innerHTML='<circle cx="28" cy="28" r="26" fill="none" stroke="#16140f" stroke-width="1.5" opacity=".4"/><path d="'+d+'" fill="#ff5d8f" opacity="'+op+'" stroke="#16140f" stroke-width="1.5" stroke-linejoin="round"/><circle cx="28" cy="28" r="'+innerR+'" fill="none" stroke="#16140f" stroke-width="1" opacity=".6"/>';svg.setAttribute('aria-label','Ton voiceprint - basé sur tes habitudes');}
function checkMilestones(s){if(!s)return;try{var ls=window.localStorage;var lastFlags=JSON.parse(ls.getItem('ff_milestones')||'{}');var newFlags={};var toasts=[];var streak=s.current_streak||0;if(streak>=7){newFlags.streak7=true;if(!lastFlags.streak7)toasts.push('🔥 7 jours de streak !');}else{newFlags.streak7=false;}var total=s.total_dictations||0;var hundreds=Math.floor(total/100);newFlags.hundreds=hundreds;if(hundreds>(lastFlags.hundreds||0)&&total>=100)toasts.push('🎉 '+hundreds*100+' dictées atteintes !');var words=s.total_words||0;[1000,5000,10000].forEach(function(thr){var k='w'+thr;newFlags[k]=words>=thr;if(words>=thr&&!lastFlags[k])toasts.push('✨ '+thr+' mots dictés !');});ls.setItem('ff_milestones',JSON.stringify(newFlags));if(toasts.length){setTimeout(function(){toasts.forEach(function(msg,i){setTimeout(function(){launchConfetti();showToast(msg);},i*1400);});},400);}}catch(e){}}
function launchConfetti(){var container=document.getElementById('confetti');var colors=['#ff5d8f','#ffd166','#a8e6cf','#c4e86b'];for(var i=0;i<30;i++){var p=document.createElement('div');p.className='confetti-piece';p.style.left=(Math.random()*100)+'%';p.style.background=colors[i%colors.length];p.style.animationDelay=(Math.random()*0.4)+'s';p.style.transform='rotate('+(Math.random()*360)+'deg)';container.appendChild(p);}setTimeout(function(){container.innerHTML='';},2500);}
function showToast(msg){var t=document.createElement('div');t.className='toast';t.textContent=msg;document.body.appendChild(t);setTimeout(function(){t.style.transition='opacity .3s';t.style.opacity='0';setTimeout(function(){t.remove();},300);},2200);}
function renderList(){var listEl=document.getElementById('list');var searchEl=document.getElementById('search-row');if(!ENTRIES.length){searchEl.style.display='none';listEl.innerHTML='<div class="empty"><svg class="bubble" viewBox="0 0 64 56"><path d="M10 6H54A6 6 0 0160 12V36A6 6 0 0154 42H30L20 52L22 42H10A6 6 0 014 36V12A6 6 0 0110 6Z" fill="#ff5d8f" stroke="#16140f" stroke-width="2.5" stroke-linejoin="round"/><g fill="#16140f"><path d="M19 33V16H29V20H23V23.5H28V27.5H23V33Z"/><path d="M33 33V16H43V20H37V23.5H42V27.5H37V33Z"/></g></svg><h3>Encore aucune dictee</h3><p>Maintiens <b>Ctrl + Espace</b>, parle, lache.<br>Ton premier essai apparaitra ici, stocke en local.</p><div class="hint">Ctrl + Espace</div></div>';return;}searchEl.style.display='flex';var filtered=ENTRIES.filter(function(e){if(CURRENT_FILTER==='today'&&!isToday(e.timestamp))return false;if(CURRENT_FILTER==='week'&&!isThisWeek(e.timestamp))return false;if(CURRENT_QUERY){var t=(e.text||'').toLowerCase();if(t.indexOf(CURRENT_QUERY)===-1)return false;}return true;});if(!filtered.length){listEl.innerHTML='<div class="empty"><h3>Rien ne correspond</h3><p>Essaie un autre filtre ou une autre recherche.</p></div>';return;}var html=filtered.map(function(e){var words=(e.text||'').trim().split(/\s+/).filter(Boolean).length;var dur=e.duration_seconds||0;var app=(e.app||'—').slice(0,28);var safeText=esc(e.text||'');var safeApp=esc(app);var idAttr=esc(e.id||'');return '<div class="entry" data-id="'+idAttr+'"><div class="head"><div class="meta"><span class="app-name">'+safeApp+'</span><span class="stamp">'+humanizeStamp(e.timestamp)+'</span></div><div class="meta"><span class="badge">'+words+' mots</span><span class="badge">'+Math.round(dur)+'s</span><span class="badge saved">&#9201; '+formatSaved(words,dur)+'</span></div></div><div class="text">'+safeText+'</div><div class="row-actions"><button class="btn-sm primary" data-act="copy">&#9114; Copier</button><button class="btn-sm" data-act="paste">&#8634; Renvoyer</button><button class="btn-sm danger" data-act="del">&#128465; Supprimer</button></div></div>';}).join('');listEl.innerHTML=html;}
document.addEventListener('click',function(ev){var btn=ev.target.closest('button[data-act]');if(!btn)return;var card=btn.closest('.entry');if(!card)return;var id=card.getAttribute('data-id');var entry=ENTRIES.find(function(e){return e.id===id;});if(!entry)return;var act=btn.getAttribute('data-act');var api=window.pywebview&&window.pywebview.api;if(!api)return;if(act==='copy'){api.copy_to_clipboard(entry.text||'');btn.textContent='✓ copie';setTimeout(function(){btn.innerHTML='&#9114; Copier';},1200);}else if(act==='paste'){api.paste_again(entry.text||'');btn.textContent='✓ envoye';setTimeout(function(){btn.innerHTML='&#8634; Renvoyer';},1200);}else if(act==='del'){api.delete_entry(id).then(function(ok){if(ok){ENTRIES=ENTRIES.filter(function(e){return e.id!==id;});renderList();reload(true);}});}});
document.addEventListener('click',function(ev){var t=ev.target;if(t.id==='best-copy'&&BEST_ENTRY){var api=window.pywebview&&window.pywebview.api;if(api)api.copy_to_clipboard(BEST_ENTRY.text||'');t.textContent='✓ copie';setTimeout(function(){t.innerHTML='⏎ Copier';},1200);}else if(t.id==='best-paste'&&BEST_ENTRY){var api=window.pywebview&&window.pywebview.api;if(api)api.paste_again(BEST_ENTRY.text||'');t.textContent='✓ envoye';setTimeout(function(){t.innerHTML='↺ Renvoyer';},1200);}});
document.getElementById('search').addEventListener('input',function(ev){CURRENT_QUERY=(ev.target.value||'').toLowerCase();renderList();});
document.querySelectorAll('.chip').forEach(function(chip){chip.addEventListener('click',function(){document.querySelectorAll('.chip').forEach(function(c){c.classList.remove('active');});chip.classList.add('active');CURRENT_FILTER=chip.getAttribute('data-filter');renderList();});});
document.getElementById('voiceprint').addEventListener('click',function(){var api=window.pywebview&&window.pywebview.api;if(api){var svg=document.getElementById('voiceprint').outerHTML;api.copy_to_clipboard(svg);showToast('voiceprint copié');}});
function reload(skipList){var api=window.pywebview&&window.pywebview.api;if(!api){setTimeout(reload,200);return;}Promise.all([api.get_history(),api.get_stats(30)]).then(function(res){ENTRIES=res[0]||[];var stats=res[1]||{};CACHED_STATS=stats;var s=stats.summary||{};renderStats(s,stats.per_day,stats.yearly_heatmap);renderChart(stats.per_day||[]);renderHeatmap(stats.yearly_heatmap||[]);renderClock(stats.hourly_dist||[]);var totalDict=s.total_dictations||0;renderDonut(stats.app_breakdown||[],totalDict);renderBest(stats.best_week);renderWpm(s);renderVoiceprint(stats.voiceprint_seed);if(!skipList){renderList();checkMilestones(s);}});}
window.addEventListener('pywebviewready',function(){reload(false);});
setTimeout(function(){if(!ENTRIES.length)reload(false);},600);
window.addEventListener('resize',function(){if(!CACHED_STATS)return;renderChart(CACHED_STATS.per_day||[]);renderHeatmap(CACHED_STATS.yearly_heatmap||[]);});
</script></body></html>
""".replace("__FONT_FACE_CSS__", FONT_CSS)


class MainWindow:
    """Main FreeFlow window — history + 30-day word-count chart on one page."""

    def __init__(self):
        self._window = None
        self._api = _MainApi()

    def open(self):
        self._window = webview.create_window(
            "FreeFlow",
            html=_HTML,
            width=900,
            height=720,
            min_size=(720, 560),
            frameless=False,
            on_top=False,
            background_color="#f4f0e8",
            js_api=self._api,
        )
        self._api.bind(self._window)
        return self._window
