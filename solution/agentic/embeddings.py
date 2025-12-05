# agentic/embeddings.py
"""
Small wrapper for embeddings. Replace embedding_fn with your provider.
For testing this uses a deterministic (but simple) hashing -> vector method.
"""

import hashlib
import numpy as np
from typing import List

EMBED_DIM = 128

def _simple_text_to_vector(text: str, dim: int = EMBED_DIM) -> List[float]:
    # deterministic pseudo-embedding: not good for production
    h = hashlib.md5(text.encode("utf8")).digest()
    vec = np.frombuffer(h* (dim // len(h) + 1), dtype=np.uint8)[:dim].astype(float)
    vec = vec / (np.linalg.norm(vec) + 1e-8)
    return vec.tolist()

def embedding_fn(text: str) -> List[float]:
    return _simple_text_to_vector(text)
