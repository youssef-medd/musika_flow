from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.agents.audio_cleaner import AudioCleanerAgent
from app.agents.base import AgentState

SR = 22050


def _write_wav(path: Path, signal: np.ndarray, sr: int = SR) -> Path:
    sf.write(path, signal, sr, subtype="PCM_16")
    return path


def _sine(seconds: float, freq: float = 440.0, sr: int = SR, amp: float = 0.2) -> np.ndarray:
    t = np.linspace(0, seconds, int(seconds * sr), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _silence(seconds: float, sr: int = SR) -> np.ndarray:
    return np.zeros(int(seconds * sr), dtype=np.float32)


def _noise(seconds: float, sr: int = SR, amp: float = 0.05) -> np.ndarray:
    rng = np.random.default_rng(42)
    return (amp * rng.standard_normal(int(seconds * sr))).astype(np.float32)


@pytest.fixture
def noisy_wav(tmp_path: Path) -> Path:
    signal = np.concatenate(
        [
            _silence(1.0),
            _sine(2.0) + _noise(2.0),
            _silence(1.0),
        ]
    )
    return _write_wav(tmp_path / "noisy.wav", signal)


def test_cleaner_returns_cleaned_audio_in_state(noisy_wav: Path):
    agent = AudioCleanerAgent()
    state: AgentState = {"job_id": "j1", "audio_path": str(noisy_wav)}

    out = agent(state)

    assert "errors" not in out or not out["errors"]
    assert "cleaned_audio" in out
    assert out["sample_rate"] == SR
    assert out["cleaned_audio"].dtype == np.float32
    assert out["cleaned_audio"].ndim == 1


def test_cleaner_trims_leading_and_trailing_silence(noisy_wav: Path):
    agent = AudioCleanerAgent(denoise=False)

    out = agent({"job_id": "j1", "audio_path": str(noisy_wav)})

    expected_samples = int(2.0 * SR)
    assert abs(out["cleaned_audio"].shape[0] - expected_samples) < int(0.3 * SR)


def test_cleaner_peak_normalizes_to_target(noisy_wav: Path):
    agent = AudioCleanerAgent(denoise=False, peak_target=0.97)

    out = agent({"job_id": "j1", "audio_path": str(noisy_wav)})

    peak = float(np.max(np.abs(out["cleaned_audio"])))
    assert peak == pytest.approx(0.97, abs=0.01)


def _off_band_energy(y: np.ndarray, sr: int, low: float, high: float) -> float:
    spectrum = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    mask = (freqs < low) | (freqs > high)
    return float(np.sum(spectrum[mask] ** 2))


def test_cleaner_attenuates_off_band_noise(tmp_path: Path):
    sine = _sine(3.0, freq=440.0, amp=0.3)
    noise = _noise(3.0, amp=0.1)
    noisy = sine + noise
    path = _write_wav(tmp_path / "noisy_sine.wav", noisy)

    denoised = AudioCleanerAgent(denoise=True)({"job_id": "j", "audio_path": str(path)})
    raw = AudioCleanerAgent(denoise=False)({"job_id": "j", "audio_path": str(path)})

    off_d = _off_band_energy(denoised["cleaned_audio"], SR, low=350.0, high=550.0)
    off_r = _off_band_energy(raw["cleaned_audio"], SR, low=350.0, high=550.0)
    assert off_d < off_r


def test_cleaner_records_error_when_path_missing():
    agent = AudioCleanerAgent()
    out = agent({"job_id": "j1"})

    assert out["errors"]
    assert "audio_cleaner" in out["errors"][0]
    assert "cleaned_audio" not in out
