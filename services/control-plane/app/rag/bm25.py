import math
from collections import Counter

from app.rag.chunker import DocumentChunk


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.chunks: list[DocumentChunk] = []
        self.doc_freqs: Counter[str] = Counter()
        self.doc_lengths: list[int] = []
        self.avg_doc_len: float = 0.0

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            words = chunk.content.lower().split()
            self.chunks.append(chunk)
            self.doc_lengths.append(len(words))

            unique_words = set(words)
            for w in unique_words:
                self.doc_freqs[w] += 1

        if self.doc_lengths:
            self.avg_doc_len = sum(self.doc_lengths) / len(self.doc_lengths)

    def search(self, query: str, top_k: int = 10) -> list[tuple[DocumentChunk, float]]:
        query_words = query.lower().split()
        if not self.chunks or not query_words:
            return []

        N = len(self.chunks)
        scores: list[float] = [0.0] * N

        for q_word in query_words:
            n_q = self.doc_freqs.get(q_word, 0)
            if n_q == 0:
                continue

            # IDF calculation
            idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)

            for i, chunk in enumerate(self.chunks):
                doc_words = chunk.content.lower().split()
                f_q = doc_words.count(q_word)
                if f_q == 0:
                    continue

                doc_len = self.doc_lengths[i]
                num = f_q * (self.k1 + 1.0)
                den = f_q + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf * (num / den)

        # Sort by BM25 score descending
        ranked = sorted(zip(self.chunks, scores, strict=False), key=lambda x: x[1], reverse=True)
        return [(chunk, score) for chunk, score in ranked[:top_k] if score > 0.0]
