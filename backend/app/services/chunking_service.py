"""Independent chunking service for document text.

Requirements:
- Split extracted content into manageable chunks.
- Use sentence or paragraph boundaries where possible.
- Configurable chunk size and overlap (approximate token counts).
- Preserve page references across chunk boundaries.
- Avoid empty chunks and maintain document ordering.
- Avoid splitting sentences unnecessarily.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List
from app.services.pdf_processor import PageText


@dataclass
class Segment:
    """Atomic text segment (sentence/paragraph unit) with page reference."""

    text: str
    page_number: int
    token_count: int


@dataclass
class ChunkResult:
    """Resulting chunk after segmentation and sliding window aggregation."""

    chunk_index: int
    content: str
    page_start: int
    page_end: int
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChunkingService:
    """Service for chunking text using sentence/paragraph boundaries with overlap."""

    def __init__(self, target_chunk_tokens: int = 700, overlap_tokens: int = 100) -> None:
        self.target_chunk_tokens = max(50, target_chunk_tokens)
        self.overlap_tokens = min(max(0, overlap_tokens), self.target_chunk_tokens // 2)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text.

        Standard heuristic for English/multilingual text: ~1 token per 4 characters
        or ~1.3 tokens per whitespace-delimited word. Using max(1, len(text) // 4) for
        fast, deterministic, dependency-free calculation.
        """
        if not text.strip():
            return 0
        words = text.split()
        if not words:
            return 0
        # Blend of word count and character ratio for high accuracy
        by_chars = len(text) / 4.0
        by_words = len(words) * 1.3
        return max(1, int(round((by_chars + by_words) / 2.0)))

    @classmethod
    def split_into_sentences(cls, text: str) -> List[str]:
        """Split text into sentences while respecting common punctuation and abbreviations."""
        if not text.strip():
            return []

        # Split on paragraph boundaries first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences: List[str] = []

        # Regex splitting on period/exclamation/question mark followed by space or newline
        sentence_end_pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])")

        for para in paragraphs:
            # Check if paragraph has sentence endings
            raw_sents = sentence_end_pattern.split(para)
            for s in raw_sents:
                clean_s = s.strip()
                if clean_s:
                    sentences.append(clean_s)

        return sentences

    def chunk_pages(self, pages: List[PageText]) -> List[ChunkResult]:
        """Chunk a list of PageText objects while preserving page boundaries and ordering."""
        # 1. Break down all pages into atomic segments tagged with their page number
        segments: List[Segment] = []
        for page in pages:
            if not page.text.strip():
                continue
            sentences = self.split_into_sentences(page.text)
            for sent in sentences:
                tokens = self.estimate_tokens(sent)
                segments.append(
                    Segment(
                        text=sent,
                        page_number=page.page_number,
                        token_count=tokens,
                    )
                )

        if not segments:
            return []

        # 2. Window segments into chunks based on target token count and overlap
        chunks: List[ChunkResult] = []
        seg_idx = 0
        total_segs = len(segments)
        chunk_idx = 0

        while seg_idx < total_segs:
            curr_chunk_segs: List[Segment] = []
            curr_tokens = 0
            start_page = segments[seg_idx].page_number

            # Accumulate segments until target chunk token limit is reached
            step_idx = seg_idx
            while step_idx < total_segs:
                seg = segments[step_idx]
                # If chunk already has content and adding this sentence exceeds target by > 20%, break
                if curr_chunk_segs and (curr_tokens + seg.token_count > self.target_chunk_tokens * 1.2):
                    break

                curr_chunk_segs.append(seg)
                curr_tokens += seg.token_count
                step_idx += 1

                # If we've reached or exceeded target tokens, stop chunk
                if curr_tokens >= self.target_chunk_tokens:
                    break

            if not curr_chunk_segs:
                # Edge case: single gigantic sentence exceeding limit
                curr_chunk_segs.append(segments[seg_idx])
                curr_tokens = segments[seg_idx].token_count
                step_idx = seg_idx + 1

            # Construct chunk text and metadata
            chunk_text = " ".join(s.text for s in curr_chunk_segs)
            end_page = curr_chunk_segs[-1].page_number

            chunks.append(
                ChunkResult(
                    chunk_index=chunk_idx,
                    content=chunk_text,
                    page_start=start_page,
                    page_end=end_page,
                    token_count=curr_tokens,
                    metadata={
                        "character_count": len(chunk_text),
                        "sentence_count": len(curr_chunk_segs),
                        "pages": list(range(start_page, end_page + 1)),
                    },
                )
            )
            chunk_idx += 1

            if step_idx >= total_segs:
                break

            # Calculate overlap: backtrack segments from step_idx until overlap token target is satisfied
            overlap_accum = 0
            overlap_count = 0
            for back_i in range(len(curr_chunk_segs) - 1, -1, -1):
                seg_to_keep = curr_chunk_segs[back_i]
                if overlap_accum + seg_to_keep.token_count <= self.overlap_tokens or overlap_count == 0:
                    overlap_accum += seg_to_keep.token_count
                    overlap_count += 1
                else:
                    break

            # Advance seg_idx forward, subtracting overlap segments
            # Ensure strict forward progress
            next_seg_idx = step_idx - overlap_count
            if next_seg_idx <= seg_idx:
                next_seg_idx = seg_idx + 1
            seg_idx = next_seg_idx

        return chunks
