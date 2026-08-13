import hashlib
import math


def generate_embedding(text: str, dim: int = 384) -> list[float]:
    """Generates a deterministic 384-dimensional normalized vector embedding from text."""
    words = text.lower().split()
    vector = [0.0] * dim

    # Add unigrams
    for _i, word in enumerate(words):
        h = hashlib.sha256(f"uni_{word}".encode()).hexdigest()
        for idx in range(0, min(len(h) - 1, 16), 2):
            dim_idx = int(h[idx : idx + 2], 16) % dim
            vector[dim_idx] += 1.5

    # Add bigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i + 1]}"
        h = hashlib.sha256(f"bi_{bigram}".encode()).hexdigest()
        for idx in range(0, min(len(h) - 1, 16), 2):
            dim_idx = int(h[idx : idx + 2], 16) % dim
            vector[dim_idx] += 2.0

    # L2 Normalization
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    else:
        vector = [1.0 / math.sqrt(dim)] * dim

    return vector


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two vectors."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2, strict=False))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)
