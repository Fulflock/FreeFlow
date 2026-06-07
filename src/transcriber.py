import os
import re
import sys

import numpy as np
from faster_whisper import WhisperModel


def _resolve_model(model_size: str) -> str:
    """Return a local bundled-model directory if we shipped one, else the bare
    model name (which makes faster-whisper download it from HuggingFace).

    We bundle the default model under models/<size>/ so the FIRST dictation
    works instantly, fully offline — no 150 MB download on first run. If the
    user switches to a model we didn't bundle, this falls back to download.
    """
    bases = []
    mei = getattr(sys, "_MEIPASS", None)
    if mei:
        bases.append(mei)  # PyInstaller bundle dir (onedir → _internal)
    if getattr(sys, "frozen", False):
        bases.append(os.path.dirname(sys.executable))  # the app folder
    else:
        bases.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    for base in bases:
        cand = os.path.join(base, "models", model_size)
        if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "model.bin")):
            return cand
    return model_size

INITIAL_PROMPT = (
    "Bonjour, voici une dictée en français avec une ponctuation correcte, "
    "des phrases complètes et bien structurées."
)

FILLER_PATTERNS = [
    r"\beuh+\b",
    r"\bheu+\b",
    r"\bhmm+\b",
    r"\bumm+\b",
    r"\bahh*\b",
    r"\bohh*\b",
    r"\bbah\b",
    r"\bben\b",
    r"\bvoilà\b(?=[\s,\.]*$)",
    r"\bdu coup\b",
    r"\ben fait\b(?=\s*[,\.euh])",
    r"\bgenre\b(?=\s*[,\.])",
    r"\bquoi\b(?=\s*[,\.]*\s*$)",
    r"\bt'sais\b",
    r"\btu sais\b(?=\s*[,\.])",
    r"\btu vois\b(?=\s*[,\.])",
    r"\bcomment dire\b",
    r"\bje veux dire\b(?=\s*[,\.])",
]

FILLER_RE = re.compile("|".join(FILLER_PATTERNS), re.IGNORECASE)


def _normalize_for_match(s: str) -> str:
    """Lowercase + strip everything but letters/digits, so snippet triggers
    match regardless of spacing, casing, or the auto-added trailing period.
    'Mon mail.' and 'mon  mail' both → 'monmail'."""
    return re.sub(r"[^\w]", "", (s or "").lower())


def apply_snippets(text: str, snippets: list) -> str:
    """If the whole dictation matches a snippet trigger, return its expansion.

    Whole-utterance match (predictable): you say just the cue phrase and it
    expands. e.g. trigger 'mon mail' → 'benjamin31.mathias@gmail.com'.
    """
    if not text or not snippets:
        return text
    norm = _normalize_for_match(text)
    for s in snippets:
        try:
            trigger = _normalize_for_match(s.get("trigger", ""))
            expansion = s.get("expansion", "")
        except AttributeError:
            continue
        if trigger and trigger == norm:
            return expansion or text
    return text


def clean_text(text: str, add_punctuation: bool = True) -> str:
    text = FILLER_RE.sub("", text)
    text = re.sub(r"\s*,\s*,", ",", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,\.\!\?])", r"\1", text)
    text = re.sub(r"^[\s,\.]+", "", text)
    text = re.sub(r"[\s,]+$", "", text)
    # The "Ponctuation automatique" toggle controls capitalization + trailing
    # period only. Filler removal above always runs (it's not "punctuation").
    if add_punctuation:
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        if text and text[-1] not in ".!?":
            text += "."
    return text.strip()


class Transcriber:
    def __init__(self, model_size: str = "base", language: str = "fr",
                 auto_punctuation: bool = True, custom_words: list = None):
        # `language`, `auto_punctuation` and `custom_words` are read fresh on
        # every transcribe, so the Settings window can change them live without
        # reloading the model.
        self.language = language
        self.auto_punctuation = auto_punctuation
        self.custom_words = list(custom_words or [])
        # Prefer the bundled model dir (instant, offline); fall back to a
        # HuggingFace download by name if that size wasn't shipped.
        self.model = WhisperModel(
            _resolve_model(model_size), device="cpu", compute_type="int8"
        )

    def _hotwords(self):
        """Build the hotwords hint from the custom dictionary, or None."""
        words = [w.strip() for w in (self.custom_words or []) if w and w.strip()]
        return ", ".join(words) if words else None

    def transcribe(self, audio: np.ndarray) -> str:
        # language "auto" (or empty) → None makes Whisper auto-detect.
        lang = self.language
        if lang in (None, "", "auto"):
            lang = None
        segments, _ = self.model.transcribe(
            audio,
            language=lang,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
            initial_prompt=INITIAL_PROMPT,
            hotwords=self._hotwords(),
            no_speech_threshold=0.6,
            condition_on_previous_text=False,
        )
        raw = " ".join(segment.text for segment in segments).strip()
        return clean_text(raw, add_punctuation=self.auto_punctuation)

    def warm_up(self) -> None:
        silent = np.zeros(16000, dtype=np.float32)
        self.transcribe(silent)
