"""
Text Chunking Utility for Content Indexing

Provides intelligent text chunking functionality using tiktoken for accurate
token counting. Preserves sentence boundaries and implements configurable
overlap between chunks for better context retention.

Usage:
    from backend.utils.text_chunking import chunk_text, count_tokens

    chunks = chunk_text("Long text content here...", max_tokens=500, overlap=50)
    token_count = count_tokens("Some text")
"""

import logging
import re
from typing import List, Dict, Any

try:
    import tiktoken
except ImportError:
    raise ImportError(
        "tiktoken is required for text chunking. Install it with: pip install tiktoken"
    )

from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class TextChunker:
    """
    Text chunking utility with token-aware splitting.

    Uses tiktoken for accurate token counting compatible with OpenAI models.
    Preserves sentence boundaries and implements configurable overlap.
    """

    def __init__(
        self,
        max_tokens: int = None,
        overlap_tokens: int = None,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the text chunker.

        Args:
            max_tokens: Maximum tokens per chunk (defaults to settings.INDEXING_CHUNK_SIZE)
            overlap_tokens: Overlap between chunks (defaults to settings.INDEXING_CHUNK_OVERLAP)
            encoding_name: Tokenizer encoding to use (cl100k_base for GPT-4/3.5)
        """
        self.max_tokens = max_tokens or settings.INDEXING_CHUNK_SIZE
        self.overlap_tokens = overlap_tokens or settings.INDEXING_CHUNK_OVERLAP

        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.error(f"Failed to load tiktoken encoding '{encoding_name}': {e}")
            raise ValueError(f"Invalid encoding name: {encoding_name}")

        logger.info(
            f"TextChunker initialized (max_tokens={self.max_tokens}, "
            f"overlap={self.overlap_tokens}, encoding={encoding_name})"
        )

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: Input text to count tokens

        Returns:
            Number of tokens in the text
        """
        if not text:
            return 0

        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: estimate ~4 chars per token
            return len(text) // 4

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving sentence boundaries.

        Args:
            text: Input text to split

        Returns:
            List of sentences
        """
        # Pattern matches sentence endings (., !, ?) followed by whitespace or end of string
        # Handles common abbreviations (Dr., Mr., Mrs., etc.)
        sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+'

        sentences = re.split(sentence_pattern, text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into token-sized pieces with overlap.

        Preserves sentence boundaries when possible. Each chunk includes
        metadata about its position and token count.

        Args:
            text: Text content to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of chunk dictionaries with text, tokens, and metadata
        """
        if not text or not text.strip():
            return []

        # Clean and normalize text
        text = text.strip()

        # If text fits in one chunk, return it as-is
        total_tokens = self.count_tokens(text)
        if total_tokens <= self.max_tokens:
            return [{
                "text": text,
                "tokens": total_tokens,
                "chunk_index": 0,
                "total_chunks": 1,
                "metadata": metadata or {}
            }]

        # Split into sentences
        sentences = self.split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If a single sentence exceeds max_tokens, split it by words
            if sentence_tokens > self.max_tokens:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append({
                        "text": " ".join(current_chunk),
                        "tokens": current_tokens,
                        "chunk_index": chunk_index,
                        "metadata": metadata or {}
                    })
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence by words
                word_chunks = self._chunk_long_sentence(sentence, metadata)
                for word_chunk in word_chunks:
                    word_chunk["chunk_index"] = chunk_index
                    chunks.append(word_chunk)
                    chunk_index += 1
                continue

            # Check if adding this sentence would exceed max_tokens
            if current_tokens + sentence_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunks.append({
                    "text": " ".join(current_chunk),
                    "tokens": current_tokens,
                    "chunk_index": chunk_index,
                    "metadata": metadata or {}
                })
                chunk_index += 1

                # Start new chunk with overlap
                if self.overlap_tokens > 0 and len(current_chunk) > 1:
                    overlap_text = " ".join(current_chunk)
                    overlap_tokens = self.count_tokens(overlap_text)

                    # Keep removing sentences from the start until within overlap limit
                    while overlap_tokens > self.overlap_tokens and len(current_chunk) > 1:
                        current_chunk.pop(0)
                        overlap_text = " ".join(current_chunk)
                        overlap_tokens = self.count_tokens(overlap_text)

                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "tokens": current_tokens,
                "chunk_index": chunk_index,
                "metadata": metadata or {}
            })

        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks

        logger.info(f"Chunked text into {total_chunks} chunks (total tokens: {total_tokens})")
        return chunks

    def _chunk_long_sentence(
        self,
        sentence: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a long sentence by words when it exceeds max_tokens.

        Args:
            sentence: Long sentence to chunk
            metadata: Optional metadata

        Returns:
            List of chunks from the long sentence
        """
        words = sentence.split()
        chunks = []
        current_words = []
        current_tokens = 0

        for word in words:
            word_tokens = self.count_tokens(word + " ")

            if current_tokens + word_tokens > self.max_tokens and current_words:
                # Save current chunk
                chunks.append({
                    "text": " ".join(current_words),
                    "tokens": current_tokens,
                    "metadata": metadata or {}
                })
                current_words = []
                current_tokens = 0

            current_words.append(word)
            current_tokens += word_tokens

        # Add last chunk
        if current_words:
            chunks.append({
                "text": " ".join(current_words),
                "tokens": current_tokens,
                "metadata": metadata or {}
            })

        return chunks


# Global singleton instance
_chunker_instance = None


def get_text_chunker() -> TextChunker:
    """
    Get or create the global TextChunker instance.

    Returns:
        TextChunker instance
    """
    global _chunker_instance

    if _chunker_instance is None:
        _chunker_instance = TextChunker()

    return _chunker_instance


def chunk_text(
    text: str,
    max_tokens: int = None,
    overlap: int = None,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to chunk text.

    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (optional, uses default if not provided)
        overlap: Overlap between chunks (optional, uses default if not provided)
        metadata: Optional metadata to include with chunks

    Returns:
        List of text chunks with metadata

    Example:
        >>> chunks = chunk_text("Long article text...", max_tokens=500, overlap=50)
        >>> for chunk in chunks:
        ...     print(f"Chunk {chunk['chunk_index']}: {chunk['tokens']} tokens")
    """
    if max_tokens or overlap:
        chunker = TextChunker(max_tokens=max_tokens, overlap_tokens=overlap)
    else:
        chunker = get_text_chunker()

    return chunker.chunk_text(text, metadata)


def count_tokens(text: str) -> int:
    """
    Convenience function to count tokens in text.

    Args:
        text: Text to count tokens for

    Returns:
        Number of tokens

    Example:
        >>> count = count_tokens("Hello, world!")
        >>> print(f"Token count: {count}")
    """
    chunker = get_text_chunker()
    return chunker.count_tokens(text)
