from __future__ import annotations

import numpy as np
import pytest

from app.agents.base import AgentState
from app.agents.embedding import EMBED_DIM, EmbeddingAgent

SR = 22050


def _sine(seconds: float, freq: float, sr: int = SR, amp: float = 0.4) -> np.ndarray:
    t = np.linspace(0, seconds, int(seconds * sr), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _state(y: np.ndarray) -> AgentState:
    return {"job_id": "j1", "cleaned_audio": y, "sample_rate": SR}


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def test_embedding_shape_and_dtype():
    out = EmbeddingAgent()(_state(_sine(2.0, 440.0)))

    assert "errors" not in out or not out["errors"]
    emb = out["embedding"]
    assert emb.shape == (EMBED_DIM,)
    assert emb.dtype == np.float32


def test_embedding_is_l2_normalized():
    out = EmbeddingAgent()(_state(_sine(2.0, 440.0)))
    assert float(np.linalg.norm(out["embedding"])) == pytest.approx(1.0, abs=1e-5)


def test_embedding_is_deterministic():
    y = _sine(2.0, 440.0)
    a = EmbeddingAgent()(_state(y.copy()))["embedding"]
    b = EmbeddingAgent()(_state(y.copy()))["embedding"]
    assert np.allclose(a, b, atol=1e-6)


def test_similar_audio_scores_higher_than_different_audio():
    base = _sine(2.0, 440.0)
    rng = np.random.default_rng(0)
    similar = base + rng.standard_normal(base.shape).astype(np.float32) * 0.01
    different = _sine(2.0, 220.0)

    agent = EmbeddingAgent()
    e_base = agent(_state(base))["embedding"]
    e_similar = agent(_state(similar))["embedding"]
    e_different = agent(_state(different))["embedding"]

    assert _cosine(e_base, e_similar) > _cosine(e_base, e_different)


def test_records_error_when_cleaned_audio_missing():
    out = EmbeddingAgent()({"job_id": "j1", "sample_rate": SR})
    assert out["errors"]
    assert "embedding" in out["errors"][0]
    assert "embedding" not in {k for k in out if k != "errors"} or "embedding" not in out


def test_records_error_when_sample_rate_missing():
    out = EmbeddingAgent()({"job_id": "j1", "cleaned_audio": _sine(1.0, 440.0)})
    assert out["errors"]
    assert "embedding" in out["errors"][0]


def test_records_error_when_audio_is_empty():
    out = EmbeddingAgent()(
        {"job_id": "j1", "cleaned_audio": np.zeros(0, dtype=np.float32), "sample_rate": SR}
    )
    assert out["errors"]
    assert "embedding" in out["errors"][0]
