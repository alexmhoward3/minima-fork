from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ProcessedDocument:
    """Represents a processed document with its metadata and content"""
    content: str
    metadata: Dict[str, any]
    uuid: str
    embedding: Optional[List[float]] = None
    chunks: List['ProcessedDocument'] = None
    
    @property
    def filename(self) -> str:
        return self.metadata.get('file_path', '').split('/')[-1]
    
    @property
    def created_at(self) -> Optional[datetime]:
        date_str = self.metadata.get('created_at')
        return datetime.fromisoformat(date_str) if date_str else None
    
    @property
    def modified_at(self) -> Optional[datetime]:
        date_str = self.metadata.get('modified_at')
        return datetime.fromisoformat(date_str) if date_str else None
    
    @property
    def tags(self) -> List[str]:
        return self.metadata.get('tags', [])