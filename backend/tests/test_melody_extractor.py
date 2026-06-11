from __future__ import annotations

import numpy as np
import pytest

from app.agents.base import AgentState
from app.agents.melody_extractor import (
    PITCH_CLASSES,
    MelodyExtractorAgent,
)

SR = 22050


def _sine(seconds: float, freq: float, sr: int = SR, amp: float = 0.4) -> np.ndarray:
    t = np.linspace(0, seconds, int(seconds * sr), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


@pytest.fixture
def a4_state() -> AgentState:
    return {
        "job_id": "j1",
        "cleaned_audio": _sine(3.0, 440.0),
        "sample_rate": SR,
    }


def test_melody_extractor_writes_all_fields(a4_state: AgentState):
    out = MelodyExtractorAgent()(a4_state)

    assert "errors" not in out or not out["errors"]
    for field in ("pitch_hz", "tempo_bpm", "key", "notes"):
        assert field in out, f"missing {field}"


def test_pitch_tracks_input_frequency_a4(a4_state: AgentState):
    out = MelodyExtractorAgent()(a4_state)

    voiced = out["pitch_hz"][out["pitch_hz"] > 0]
    assert voiced.size > 0, "no voiced frames detected"
    median_hz = float(np.median(voiced))
    assert median_hz == pytest.approx(440.0, rel=0.03)


def test_tempo_is_positive_float(a4_state: AgentState):
    out = MelodyExtractorAgent()(a4_state)
    assert isinstance(out["tempo_bpm"], float)
    assert out["tempo_bpm"] >= 0.0


def test_key_is_valid_string(a4_state: AgentState):
    out = MelodyExtractorAgent()(a4_state)
    key = out["key"]
    assert isinstance(key, str)
    assert key == "unknown" or any(
        key == f"{pc} {mode}" for pc in PITCH_CLASSES for mode in ("major", "minor")
    )


def test_notes_contain_a_pitch_class_for_a4(a4_state: AgentState):
    out = MelodyExtractorAgent()(a4_state)
    notes = out["notes"]
    assert isinstance(notes, list)
    assert notes, "expected at least one detected note"
    pitch_classes = {n.rstrip("0123456789-") for n in notes}
    assert "A" in pitch_classes


def test_records_error_when_cleaned_audio_missing():
    out = MelodyExtractorAgent()({"job_id": "j1", "sample_rate": SR})
    assert out["errors"]
    assert "melody_extractor" in out["errors"][0]
    assert "pitch_hz" not in out


def test_records_error_when_sample_rate_missing():
    out = MelodyExtractorAgent()({"job_id": "j1", "cleaned_audio": _sine(1.0, 440.0)})
    assert out["errors"]
    assert "melody_extractor" in out["errors"][0]


def test_records_error_when_audio_is_empty():
    out = MelodyExtractorAgent()(
        {"job_id": "j1", "cleaned_audio": np.zeros(0, dtype=np.float32), "sample_rate": SR}
    )
    assert out["errors"]
    assert "melody_extractor" in out["errors"][0]
