from __future__ import annotations

import librosa
import noisereduce as nr
import numpy as np

from app.agents.base import AgentState, BaseAgent

TARGET_SAMPLE_RATE = 22050
TRIM_TOP_DB = 30
PEAK_TARGET = 0.97


class AudioCleanerAgent(BaseAgent):
    name = "audio_cleaner"

    def __init__(
        self,
        sample_rate: int = TARGET_SAMPLE_RATE,
        trim_top_db: int = TRIM_TOP_DB,
        peak_target: float = PEAK_TARGET,
        denoise: bool = True,
    ) -> None:
        self.sample_rate = sample_rate
        self.trim_top_db = trim_top_db
        self.peak_target = peak_target
        self.denoise = denoise

    def run(self, state: AgentState) -> AgentState:
        audio_path = state.get("audio_path")
        if not audio_path:
            raise ValueError("audio_path missing from state")

        y, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)

        if y.size == 0:
            raise ValueError("loaded audio is empty")

        y = self._trim_silence(y)
        y = self._denoise(y, sr) if self.denoise else y
        y = self._normalize(y)

        return self.merge(
            state,
            cleaned_audio=y.astype(np.float32),
            sample_rate=sr,
        )

    def _trim_silence(self, y: np.ndarray) -> np.ndarray:
        trimmed, _ = librosa.effects.trim(y, top_db=self.trim_top_db)
        return trimmed if trimmed.size > 0 else y

    def _denoise(self, y: np.ndarray, sr: int) -> np.ndarray:
        return nr.reduce_noise(y=y, sr=sr, stationary=False, prop_decrease=0.85)

    def _normalize(self, y: np.ndarray) -> np.ndarray:
        peak = float(np.max(np.abs(y)))
        if peak == 0.0:
            return y
        return (y / peak) * self.peak_target
