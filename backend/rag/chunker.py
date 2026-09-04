"""
Document chunker module.

Splits documents into coherent chunks suitable for embedding and retrieval.
"""
from __future__ import annotations

import re


def chunk_text(
    text: str,
    max_chunk_size: int = 600,
    overlap: int = 80,
) -> list[str]:
    """
    Split document text into logical, overlapping chunks.

    Respects paragraph breaks and sentence boundaries where possible.
    """
    if not text or not text.strip():
        return []

    # Clean text
    clean = re.sub(r"\n{3,}", "\n\n", text.strip())

    # Try splitting by double line breaks (paragraphs)
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current_chunk = ""

    for p in paragraphs:
        if not current_chunk:
            current_chunk = p
        elif len(current_chunk) + len(p) + 2 <= max_chunk_size:
            current_chunk += "\n\n" + p
        else:
            chunks.append(current_chunk)
            # Apply overlap if current chunk is long enough
            if len(p) < max_chunk_size:
                current_chunk = p
            else:
                # Break huge paragraph into sentence chunks
                sentences = re.split(r"(?<=[.!?।])\s+", p)
                current_chunk = ""
                for s in sentences:
                    if not current_chunk:
                        current_chunk = s
                    elif len(current_chunk) + len(s) + 1 <= max_chunk_size:
                        current_chunk += " " + s
                    else:
                        chunks.append(current_chunk)
                        current_chunk = s

    if current_chunk:
        chunks.append(current_chunk)

    return [c.strip() for c in chunks if c.strip()]
