"""Cosine similarity matching for InsightFace embeddings."""

from __future__ import annotations

from typing import Optional

import numpy as np

from app.config import get_config
from app.core.exceptions import EmbeddingMismatchError
from app.core.models import MatchResult

DEFAULT_THRESHOLD = 0.40


def l2_normalize(vec: np.ndarray) -> np.ndarray:
    values = np.asarray(vec, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(values))
    if norm <= 0:
        return values
    return values / norm


def cosine_similarity(embedding_a, embedding_b) -> float:
    vector_a = l2_normalize(np.asarray(embedding_a, dtype=np.float32))
    vector_b = l2_normalize(np.asarray(embedding_b, dtype=np.float32))
    if vector_a.shape != vector_b.shape:
        raise EmbeddingMismatchError(
            f"Embedding dimension mismatch: {vector_a.shape[0]} vs {vector_b.shape[0]}"
        )
    return float(np.dot(vector_a, vector_b))


def similarity_to_match_percentage(similarity: float) -> float:
    percentage = ((float(similarity) + 1.0) / 2.0) * 100.0
    return round(max(0.0, min(100.0, percentage)), 2)


def compare_embeddings(
    incoming,
    stored,
    *,
    threshold: Optional[float] = None,
) -> MatchResult:
    """
    Compare two InsightFace embeddings.

    matched=True when cosine similarity >= threshold.
    """
    if threshold is None:
        try:
            threshold = get_config().match_threshold
        except Exception:  # noqa: BLE001
            threshold = DEFAULT_THRESHOLD

    similarity = cosine_similarity(incoming, stored)
    rounded = round(similarity, 6)
    matched = similarity >= float(threshold)
    return MatchResult(
        matched=matched,
        similarity=rounded,
        distance=round(1.0 - similarity, 6),
        match_percentage=similarity_to_match_percentage(rounded),
        threshold=float(threshold),
        metric="cosine_similarity",
        threshold_shortfall=(
            round(float(threshold) - rounded, 6) if not matched else None
        ),
    )
