from __future__ import annotations

import librosa
import numpy as np

from app.agents.base import AgentState, BaseAgent

EMBED_DIM = 512
N_MELS = 128
N_MFCC = 40
PROJECTION_SEED = 20260714


class EmbeddingAgent(BaseAgent):
    """Deterministic audio embedding.

    Mel + MFCC time-pooled stats projected to a 512-dim L2-normalized vector.
    Stand-in for CLAP until the model is wired; keeps the pipeline runnable
    without pulling multi-GB weights.
    """

    name = "embedding"

    def __init__(
        self,
        embed_dim: int = EMBED_DIM,
        n_mels: int = N_MELS,
        n_mfcc: int = N_MFCC,
        projection_seed: int = PROJECTION_SEED,
    ) -> None:
        self.embed_dim = embed_dim
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self._rng = np.random.default_rng(projection_seed)
        self._projection: np.ndarray | None = None

    def run(self, state: AgentState) -> AgentState:
        y = state.get("cleaned_audio")
        sr = state.get("sample_rate")
        if y is None:
            raise ValueError("cleaned_audio missing from state")
        if sr is None:
            raise ValueError("sample_rate missing from state")
        if y.size == 0:
            raise ValueError("cleaned_audio is empty")

        features = self._pooled_features(y, sr)
        projection = self._get_projection(features.shape[0])
        embedding = features @ projection
        embedding = self._l2_normalize(embedding).astype(np.float32)

        return self.merge(state, embedding=embedding)

    def _pooled_features(self, y: np.ndarray, sr: int) -> np.ndarray:
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels)
        log_mel = librosa.power_to_db(mel, ref=np.max)
        mfcc = librosa.feature.mfcc(S=log_mel, sr=sr, n_mfcc=self.n_mfcc)

        return np.concatenate(
            [
                log_mel.mean(axis=1),
                log_mel.std(axis=1),
                mfcc.mean(axis=1),
                mfcc.std(axis=1),
            ]
        ).astype(np.float32)

    def _get_projection(self, in_dim: int) -> np.ndarray:
        if self._projection is None or self._projection.shape[0] != in_dim:
            proj = self._rng.standard_normal((in_dim, self.embed_dim)).astype(np.float32)
            proj /= np.sqrt(in_dim)
            self._projection = proj
        return self._projection

    @staticmethod
    def _l2_normalize(v: np.ndarray) -> np.ndarray:
        norm = float(np.linalg.norm(v))
        if norm == 0.0:
            return v
        return v / norm
