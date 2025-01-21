from typing import List, Dict
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    text: str
    metadata: Dict
    start_char: int
    end_char: int

class ChunkingStrategy:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, metadata: Dict) -> List[Chunk]:
        raise NotImplementedError

    def _character_chunk(self, text: str, metadata: Dict, start_pos: int, min_size: int = None) -> List[Chunk]:
        """Base character-based chunking logic with optional minimum chunk size."""
        chunks = []
        current_pos = 0
        chunk_size = self.chunk_size if min_size is None else max(self.chunk_size, min_size)
        
        while current_pos < len(text):
            chunk_end = min(current_pos + chunk_size, len(text))
            
            # Adjust chunk boundary to not break within a line
            if chunk_end < len(text):
                # Try to find a line break first
                line_break = text.rfind('\n', current_pos, chunk_end)
                if line_break != -1:
                    # Make sure we have enough content
                    if line_break - current_pos >= (min_size or 0):
                        chunk_end = line_break
                    else:
                        # Keep looking for the next line break
                        next_break = text.find('\n', line_break + 1)
                        if next_break != -1:
                            chunk_end = next_break
                else:
                    # If no line break, try word boundary
                    space = text.rfind(' ', current_pos, chunk_end)
                    if space != -1:
                        chunk_end = space
            
            # Create the chunk
            chunk_text = text[current_pos:chunk_end].strip()
            if chunk_text:  # Only create chunk if there's content
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata=metadata,
                    start_char=start_pos + current_pos,
                    end_char=start_pos + chunk_end
                ))
            
            # Move position
            current_pos = chunk_end
            if current_pos < len(text):
                current_pos = max(current_pos - self.chunk_overlap, 0)
                
        return chunks

class H2ChunkingStrategy(ChunkingStrategy):
    def split_text(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text based on H2 headers while maintaining minimum context size."""
        h2_pattern = re.compile(r'^(## .*?)(?=\n## |\Z)', re.MULTILINE | re.DOTALL)
        matches = list(h2_pattern.finditer(text))
        
        logger.info(f"Found {len(matches)} h2 sections")
        chunks = []
        current_pos = 0
        
        # Handle content before first H2 if it exists
        if matches and matches[0].start() > 0:
            pre_h2_content = text[:matches[0].start()].strip()
            if pre_h2_content:
                logger.info("Processing pre-h2 content")
                chunks.extend(self._character_chunk(pre_h2_content, metadata, 0))
                current_pos = matches[0].start()
        
        # Process each H2 section
        min_section_size = 800  # Minimum characters to keep after each H2
        
        for match in matches:
            section_text = match.group(0)
            if not section_text.strip():
                continue
                
            logger.info(f"Processing h2 section starting with: {section_text[:50]}...")
            
            # Ensure we keep enough context
            section_chunks = self._character_chunk(
                section_text,
                metadata,
                match.start(),
                min_size=min_section_size
            )
            
            chunks.extend(section_chunks)
            current_pos = match.end()
        
        # Handle any remaining content
        if current_pos < len(text):
            remaining_text = text[current_pos:].strip()
            if remaining_text:
                chunks.extend(self._character_chunk(remaining_text, metadata, current_pos))
        
        if not chunks:  # Fallback to character chunking if no H2 sections found
            logger.info("No H2 sections found, falling back to character chunking")
            return self._character_chunk(text, metadata, 0)
        
        return chunks

class CharacterChunkingStrategy(ChunkingStrategy):
    def split_text(self, text: str, metadata: Dict) -> List[Chunk]:
        """Standard character-based chunking."""
        logger.info("Using character chunking strategy")
        chunks = self._character_chunk(text, metadata, 0)
        logger.info(f"Created {len(chunks)} character-based chunks")
        return chunks