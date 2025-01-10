import os
import torch
from dataclasses import dataclass
from typing import Dict, Type
from pathlib import Path
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    ObsidianLoader,
)

@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    
    # File handling
    EXTENSIONS_TO_LOADERS: Dict[str, Type] = None
    LOCAL_FILES_PATH: str = os.environ.get("LOCAL_FILES_PATH")
    CONTAINER_PATH: str = os.environ.get("CONTAINER_PATH")
    
    # Model settings
    EMBEDDING_MODEL_ID: str = os.environ.get("EMBEDDING_MODEL_ID", "sentence-transformers/all-mpnet-base-v2")
    EMBEDDING_SIZE: int = int(os.environ.get("EMBEDDING_SIZE", "768"))
    RERANKER_MODEL: str = os.environ.get("RERANKER_MODEL")
    
    # Processing settings
    CHUNK_SIZE: int = int(os.environ.get("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.environ.get("CHUNK_OVERLAP", "100"))
    
    # Device configuration
    DEVICE: torch.device = torch.device(
        "mps" if torch.backends.mps.is_available() else
        "cuda" if torch.cuda.is_available() else
        "cpu"
    )
    
    def __post_init__(self):
        if self.EXTENSIONS_TO_LOADERS is None:
            self.EXTENSIONS_TO_LOADERS = {
                ".pdf": PyMuPDFLoader,
                ".xls": UnstructuredExcelLoader,
                ".docx": Docx2txtLoader,
                ".txt": TextLoader,
                ".md": ObsidianLoader,
                ".csv": CSVLoader,
            }
