import logging
from typing import List, Optional, Set
from langchain.schema import Document
from langchain_community.document_loaders import ObsidianLoader
from pathlib import Path
import os
import yaml

logger = logging.getLogger(__name__)

class SingleFileObsidianLoader(ObsidianLoader):
    """Loader that handles a single Obsidian file while maintaining tag and frontmatter parsing."""
    
    def __init__(
        self,
        file_path: str,
        vault_path: str,
        encoding: str = None,
        collect_metadata: bool = True
    ):
        """Initialize with both file path and vault path."""
        super().__init__(
            str(vault_path),
            encoding=encoding,
            collect_metadata=collect_metadata
        )
        self.target_file = str(Path(file_path))
        self.vault_path = str(Path(vault_path))
        self.encoding = encoding or 'utf-8'
        logger.info(f"Initialized SingleFileObsidianLoader for {self.target_file} in vault {self.vault_path}")

    def load(self) -> List[Document]:
        """Load and process the single specified file."""
        try:
            target_path = Path(self.target_file).resolve()
            
            # Read the file
            with open(self.target_file, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Create initial document
            doc = Document(
                page_content=content,
                metadata={
                    'source': str(target_path),
                    'file_path': str(target_path),
                    'relative_path': str(Path(self.target_file).relative_to(self.vault_path))
                }
            )
            
            # Use ObsidianLoader's metadata and tag processing
            documents = self._process_document(doc)
            
            if documents:
                logger.info(f"Successfully loaded and processed {self.target_file}")
                logger.info(f"Tags found: {documents[0].metadata.get('tags', [])}")
                return documents
            else:
                logger.warning(f"No content loaded from {self.target_file}")
                return []

        except Exception as e:
            logger.error(f"Error loading {self.target_file}: {str(e)}")
            return []

    def _process_document(self, doc: Document) -> List[Document]:
        """Process a single document using ObsidianLoader's functionality."""
        try:
            # Extract metadata using parent class method
            metadata = self.collect_metadata(doc.page_content)
            
            # Get tags using parent class method
            tags = self.collect_tags(doc.page_content)
            if tags:
                if metadata.get('tags'):
                    # Merge with any tags from frontmatter
                    if isinstance(metadata['tags'], list):
                        tags.extend(metadata['tags'])
                    elif isinstance(metadata['tags'], str):
                        tags.extend(tag.strip() for tag in metadata['tags'].split(','))
                metadata['tags'] = sorted(list(set(tags)))
            
            # Update document metadata
            doc.metadata.update(metadata)
            
            return [doc]
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return [doc]