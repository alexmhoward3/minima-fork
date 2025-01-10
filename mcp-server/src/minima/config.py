import os
from typing import Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class QdrantConfig:
    """Configuration for Qdrant vector database"""
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "mnm_storage"
    prefer_grpc: bool = False
    timeout: float = 10.0

@dataclass
class PathConfig:
    """Configuration for file paths and directories"""
    local_files_path: str = os.environ.get("LOCAL_FILES_PATH", "")
    container_path: str = os.environ.get("CONTAINER_PATH", "/usr/src/app/local_files/")
    ignore_file: str = ".minimaignore"
    
    def get_ignore_path(self) -> Path:
        """Get the path to the ignore file"""
        return Path(self.container_path) / self.ignore_file

@dataclass
class ModelConfig:
    """Configuration for ML models"""
    embedding_model_id: str = os.environ.get(
        "EMBEDDING_MODEL_ID", 
        "sentence-transformers/all-mpnet-base-v2"
    )
    embedding_size: int = int(os.environ.get("EMBEDDING_SIZE", "768"))
    reranker_model: Optional[str] = os.environ.get("RERANKER_MODEL")
    device: Optional[str] = os.environ.get("DEVICE", None)

@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    chunk_size: int = int(os.environ.get("CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.environ.get("CHUNK_OVERLAP", "100"))
    chunk_strategy: str = os.environ.get("CHUNK_STRATEGY", "h2")
    max_documents: int = int(os.environ.get("MAX_DOCUMENTS", "1000"))
    batch_size: int = int(os.environ.get("BATCH_SIZE", "10"))

@dataclass
class LogConfig:
    """Configuration for logging"""
    level: str = os.environ.get("LOG_LEVEL", "INFO")
    file: Optional[str] = os.environ.get("LOG_FILE", "app.log")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

@dataclass
class ServerConfig:
    """Main server configuration"""
    name: str = "minima"
    version: str = "0.0.1"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"

@dataclass
class Config:
    """Root configuration class"""
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LogConfig = field(default_factory=LogConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        return cls(
            qdrant=QdrantConfig(
                host=os.environ.get("QDRANT_HOST", "localhost"),
                port=int(os.environ.get("QDRANT_PORT", "6333")),
                collection_name=os.environ.get("QDRANT_COLLECTION", "mnm_storage"),
                prefer_grpc=os.environ.get("QDRANT_PREFER_GRPC", "false").lower() == "true",
                timeout=float(os.environ.get("QDRANT_TIMEOUT", "10.0"))
            ),
            paths=PathConfig(
                local_files_path=os.environ.get("LOCAL_FILES_PATH", ""),
                container_path=os.environ.get("CONTAINER_PATH", "/usr/src/app/local_files/"),
                ignore_file=os.environ.get("IGNORE_FILE", ".minimaignore")
            ),
            models=ModelConfig(
                embedding_model_id=os.environ.get("EMBEDDING_MODEL_ID", "sentence-transformers/all-mpnet-base-v2"),
                embedding_size=int(os.environ.get("EMBEDDING_SIZE", "768")),
                reranker_model=os.environ.get("RERANKER_MODEL"),
                device=os.environ.get("DEVICE")
            ),
            processing=ProcessingConfig(
                chunk_overlap=int(os.environ.get("CHUNK_OVERLAP", "100")),
                chunk_strategy=os.environ.get("CHUNK_STRATEGY", "h2"),
                max_documents=int(os.environ.get("MAX_DOCUMENTS", "1000")),
                batch_size=int(os.environ.get("BATCH_SIZE", "10"))
            ),
            logging=LogConfig(
                level=os.environ.get("LOG_LEVEL", "INFO"),
                file=os.environ.get("LOG_FILE", "app.log"),
                format=os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            ),
            server=ServerConfig(
                name=os.environ.get("SERVER_NAME", "minima"),
                version=os.environ.get("SERVER_VERSION", "0.0.1"),
                host=os.environ.get("SERVER_HOST", "0.0.0.0"),
                port=int(os.environ.get("SERVER_PORT", "8000")),
                workers=int(os.environ.get("SERVER_WORKERS", "1")),
                debug=os.environ.get("DEBUG", "false").lower() == "true"
            )
        )

# Create global config instance
config = Config.from_env()
