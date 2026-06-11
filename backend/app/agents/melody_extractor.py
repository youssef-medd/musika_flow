from __future__ import annotations

import librosa
import numpy as np

from app.agents.base import AgentState, BaseAgent

PITCH_FMIN = 65.0    # ~C2 — covers low male humming
PITCH_FMAX = 1047.0  # ~C6 — covers high female humming / whistle

# Krumhansl-Schmuckler key profiles (major/minor) used for tonality estimation.
MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class MelodyExtractorAgent(BaseAgent):
    name = "melody_extractor"

    def __init__(
        self,
        fmin: float = PITCH_FMIN,
        fmax: float = PITCH_FMAX,
    ) -> None:
        self.fmin = fmin
        self.fmax = fmax

    def run(self, state: AgentState) -> AgentState:
        y = state.get("cleaned_audio")
        sr = state.get("sample_rate")
        if y is None:
            raise ValueError("cleaned_audio missing from state")
        if sr is None:
            raise ValueError("sample_rate missing from state")
        if y.size == 0:
            raise ValueError("cleaned_audio is empty")

        f0 = self._extract_pitch(y, sr)
        tempo = self._estimate_tempo(y, sr)
        key = self._estimate_key(y, sr)
        notes = self._pitch_to_notes(f0)

        return self.merge(
            state,
            pitch_hz=f0.astype(np.float32),
            tempo_bpm=tempo,
            key=key,
            notes=notes,
        )

    def _extract_pitch(self, y: np.ndarray, sr: int) -> np.ndarray:
        f0, _, _ = librosa.pyin(y, fmin=self.fmin, fmax=self.fmax, sr=sr)
        return np.nan_to_num(f0, nan=0.0)

    def _estimate_tempo(self, y: np.ndarray, sr: int) -> float:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return float(np.atleast_1d(tempo)[0])

    def _estimate_key(self, y: np.ndarray, sr: int) -> str:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        total = chroma_mean.sum()
        if total <= 0:
            return "unknown"
        chroma_mean = chroma_mean / total

        best_score = -np.inf
        best_key = "unknown"
        for tonic in range(12):
            major_corr = np.corrcoef(np.roll(MAJOR_PROFILE, tonic), chroma_mean)[0, 1]
            minor_corr = np.corrcoef(np.roll(MINOR_PROFILE, tonic), chroma_mean)[0, 1]
            if major_corr > best_score:
                best_score = major_corr
                best_key = f"{PITCH_CLASSES[tonic]} major"
            if minor_corr > best_score:
                best_score = minor_corr
                best_key = f"{PITCH_CLASSES[tonic]} minor"
        return best_key

    def _pitch_to_notes(self, f0: np.ndarray) -> list[str]:
        voiced = f0[f0 > 0]
        if voiced.size == 0:
            return []
        midi_int = np.round(librosa.hz_to_midi(voiced)).astype(int)
        notes: list[str] = []
        last: int | None = None
        for m in midi_int:
            if m != last:
                notes.append(librosa.midi_to_note(int(m)))
                last = m
        return notes
