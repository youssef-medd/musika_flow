from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypedDict

import numpy as np


class AgentState(TypedDict, total=False):
    job_id: str
    audio_path: str
    sample_rate: int
    cleaned_audio: np.ndarray
    pitch_hz: np.ndarray
    tempo_bpm: float
    key: str
    notes: list[str]
    errors: list[str]


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        ...

    def _record_error(self, state: AgentState, exc: Exception) -> AgentState:
        errors = list(state.get("errors", []))
        errors.append(f"{self.name}: {exc}")
        return {**state, "errors": errors}

    def __call__(self, state: AgentState) -> AgentState:
        try:
            return self.run(state)
        except Exception as exc:  # noqa: BLE001
            return self._record_error(state, exc)

    @staticmethod
    def merge(state: AgentState, **updates: Any) -> AgentState:
        return {**state, **updates}
