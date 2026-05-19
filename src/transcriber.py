import re

import numpy as np
from faster_whisper import WhisperModel

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


def clean_text(text: str) -> str:
    text = FILLER_RE.sub("", text)
    text = re.sub(r"\s*,\s*,", ",", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,\.\!\?])", r"\1", text)
    text = re.sub(r"^[\s,\.]+", "", text)
    text = re.sub(r"[\s,]+$", "", text)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."
    return text.strip()


class Transcriber:
    def __init__(self, model_size: str = "base", language: str = "fr"):
        self.language = language
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
            initial_prompt=INITIAL_PROMPT,
            no_speech_threshold=0.6,
            condition_on_previous_text=False,
        )
        raw = " ".join(segment.text for segment in segments).strip()
        return clean_text(raw)

    def warm_up(self) -> None:
        silent = np.zeros(16000, dtype=np.float32)
        self.transcribe(silent)
