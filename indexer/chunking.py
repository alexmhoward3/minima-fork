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

    def _character_chunk(self, text: str, metadata: Dict, start_pos: int) -> List[Chunk]:
        # Base character-based chunking logic
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            chunk_end = min(current_pos + self.chunk_size, len(text))
            
            # Adjust chunk boundary to not break within a line
            if chunk_end < len(text):
                chunk_end = text.rfind('\n', current_pos, chunk_end)
                if chunk_end == -1:
                    chunk_end = text.rfind(' ', current_pos, chunk_end)
                if chunk_end == -1:
                    chunk_end = min(current_pos + self.chunk_size, len(text))
            
            chunks.append(Chunk(
                text=text[current_pos:chunk_end],
                metadata=metadata,
                start_char=start_pos + current_pos,
                end_char=start_pos + chunk_end
            ))
            
            current_pos = chunk_end
            if current_pos < len(text):
                current_pos = max(current_pos - self.chunk_overlap, 0)
                
        return chunks

class H2ChunkingStrategy(ChunkingStrategy):
    def split_text(self, text: str, metadata: Dict) -> List[Chunk]:
        # Split into h2 sections first
        h2_pattern = re.compile(r'^## ', re.MULTILINE)
        sections = h2_pattern.split(text)
        
        logger.info(f"Split text into {len(sections)} h2 sections")
        if len(sections) > 1:
            logger.info(f"First few characters of sections: {[s[:50] + '...' for s in sections[:2]]}")

        
        chunks = []
        current_pos = 0
        
        logger.info(f"Starting H2 chunking for text length {len(text)}")

        # Handle pre-h2 content if it exists
        if sections[0].strip():
            logger.info("Processing pre-h2 content")
            chunks.extend(self._character_chunk(sections[0], metadata, current_pos))
            current_pos += len(sections[0])

        # Process each h2 section
        for section in sections[1:]:
            if not section.strip():
                logger.info("Skipping empty section")
                continue
                
            logger.info(f"Processing h2 section starting with: {section[:50]}...")
                
            # Add back the '## ' prefix
            section_text = f"## {section}"
            section_chunks = self._character_chunk(section_text, metadata, current_pos)
            chunks.extend(section_chunks)
            current_pos += len(section_text)

        return chunks



class CharacterChunkingStrategy(ChunkingStrategy):
    def split_text(self, text: str, metadata: Dict) -> List[Chunk]:
        # Existing character-based chunking implementation
        logger.info("Using character chunking strategy")
        chunks = self._character_chunk(text, metadata, 0)
        logger.info(f"Created {len(chunks)} character-based chunks")
        return chunks