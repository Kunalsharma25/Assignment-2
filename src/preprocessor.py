"""
Module for cleaning and chunking review text.
Uses tiktoken for precise tokenization and overlapping chunk generation.
"""
import html
import re
import unicodedata
import logging
import tiktoken
from typing import List

logger = logging.getLogger(__name__)

class Preprocessor:
    """
    Handles cleaning and token-safe segmentation of raw text.
    
    Attributes:
        max_tokens (int): Maximum tokens per chunk.
        overlap_tokens (int): Number of overlapping tokens between chunks.
    """
    def __init__(self, max_tokens: int = 1000, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.has_tiktoken = True
        except Exception as e:
            logger.warning(f"Could not load tiktoken: {e}. Falling back to word approximation.")
            self.has_tiktoken = False

    def clean(self, text: str) -> str:
        """Cleans raw text data."""
        if not text:
            return ""
        
        # 1. HTML unescape
        text = html.unescape(text)
        
        # 2. Strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 3. Normalize Unicode (NFC)
        text = unicodedata.normalize('NFC', text)
        
        # 4. Remove non-printable control characters (except tabs and newlines)
        text = "".join(ch for ch in text if ch.isprintable() or ch in '\t\n\r')
        
        # 5. Collapse multiple whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def count_tokens(self, text: str) -> int:
        """Counts tokens in text."""
        if self.has_tiktoken:
            return len(self.encoding.encode(text))
        else:
            # Fallback: ~4 characters per token or ~0.75 words per token
            return len(text.split())

    def chunk(self, text: str) -> List[str]:
        """Chunks text into token-safe overlapping segments."""
        token_count = self.count_tokens(text)
        if token_count <= self.max_tokens:
            return [text]
        
        # Chunking logic
        if self.has_tiktoken:
            tokens = self.encoding.encode(text)
            chunks = []
            start = 0
            while start < len(tokens):
                end = start + self.max_tokens
                chunk_tokens = tokens[start:end]
                chunks.append(self.encoding.decode(chunk_tokens))
                
                # Move start forward by (max - overlap)
                start += (self.max_tokens - self.overlap_tokens)
                
                # Prevent infinite loops if overlap >= max
                if self.max_tokens <= self.overlap_tokens:
                    break
        else:
            # Simple word-based chunking fallback
            words = text.split()
            chunks = []
            # Assuming ~0.75 words per token, so max words ~ max_tokens * 1.3
            max_words = int(self.max_tokens * 1.3)
            overlap_words = int(self.overlap_tokens * 1.3)
            
            start = 0
            while start < len(words):
                end = start + max_words
                chunks.append(" ".join(words[start:end]))
                start += (max_words - overlap_words)
                if max_words <= overlap_words:
                    break
        
        logger.info(f"Segmented text into {len(chunks)} chunks.")
        return chunks

    def process(self, text: str) -> List[str]:
        """Cleans and chunks the input text."""
        cleaned = self.clean(text)
        if not cleaned:
            logger.warning("Cleaned text is empty.")
            return []
        return self.chunk(cleaned)
