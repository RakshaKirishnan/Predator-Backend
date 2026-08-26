"""Shared domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class DetectedFace:
    bbox: list[float]
    score: float
    embedding: list[float]
    landmarks: Optional[list[list[float]]] = None

    @property
    def embedding_dim(self) -> int:
        return len(self.embedding)

    def to_dict(self, *, include_embedding: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "bbox": list(self.bbox),
            "score": self.score,
            "landmarks": self.landmarks,
            "embedding_dim": self.embedding_dim,
        }
        if include_embedding:
            data["embedding"] = list(self.embedding)
        return data


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    similarity: float
    distance: float
    match_percentage: float
    threshold: float
    metric: str = "cosine_similarity"
    threshold_shortfall: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "similarity": self.similarity,
            "distance": self.distance,
            "match_percentage": self.match_percentage,
            "threshold": self.threshold,
            "metric": self.metric,
            "threshold_shortfall": self.threshold_shortfall,
        }
