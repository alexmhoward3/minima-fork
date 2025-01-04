# Qdrant Payload Implementation Details (using LangChain ObsidianLoader)

## Overview

This implementation uses the LangChain ObsidianLoader, which is specifically designed to handle Obsidian's markdown format, including wikilinks, frontmatter, and tags.

## Integration with Indexer

The indexer's Config class is modified to use ObsidianLoader for .md files:

```python
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    PyMuPDFLoader,
    ObsidianLoader,  # Add ObsidianLoader
)

@dataclass
class Config:
    EXTENSIONS_TO_LOADERS = {
        ".pdf": PyMuPDFLoader,
        ".xls": UnstructuredExcelLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".md": ObsidianLoader,  # Use ObsidianLoader for markdown files
        ".csv": CSVLoader,
    }
```

## Proposed Payload Schema

The Qdrant payload will be a JSON object with the following structure:

```json
{
  "file_path": "path/to/obsidian/note.md",
  "chunk_id": "unique_id_for_chunk",
  "heading": "Section Heading",
  "tags": ["tag1", "tag2"],
  "links": ["path/to/linked/note1.md", "path/to/linked/note2.md"],
  "created_at": "ISO timestamp",
  "modified_at": "ISO timestamp",
  "frontmatter": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

## Metadata Extraction

The LangChain ObsidianLoader automatically handles metadata extraction. Here's how it works with our system:

```python
from datetime import datetime
import uuid
from langchain_community.document_loaders import ObsidianLoader
from typing import Dict, Any, List

def extract_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from an Obsidian note using LangChain's ObsidianLoader
    """
    # Initialize loader with metadata collection enabled
    loader = ObsidianLoader(
        path=file_path,
        encoding="utf-8",
        collect_metadata=True
    )
    
    # Load document
    docs = loader.load()
    if not docs:
        return None
        
    doc = docs[0]  # Get first document
    metadata = doc.metadata
    
    # Add additional metadata
    metadata.update({
        "chunk_id": str(uuid.uuid4()),
        "created_at": datetime.fromtimestamp(
            os.path.getctime(file_path)
        ).isoformat(),
        "modified_at": datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).isoformat(),
    })
    
    return metadata
```

## Document Relationship Tracking

The ObsidianLoader automatically extracts wikilinks and other relationships. These are available in the metadata:

```python
def get_document_relationships(metadata: Dict[str, Any]) -> List[str]:
    """
    Extract document relationships from metadata
    """
    relationships = []
    
    # Get wikilinks
    if "links" in metadata:
        relationships.extend(metadata["links"])
        
    # Get note references
    if "note_references" in metadata:
        relationships.extend(metadata["note_references"])
        
    # Get embeds
    if "embeds" in metadata:
        relationships.extend(metadata["embeds"])
        
    return list(set(relationships))  # Remove duplicates
```

## Payload-Based Scoring

The scoring system can take advantage of the rich metadata provided by ObsidianLoader:

```python
from datetime import datetime, timedelta
from typing import Dict, Any

def score_with_payload(
    vector_similarity: float,
    payload: Dict[str, Any]
) -> float:
    """
    Score search results based on vector similarity and metadata
    """
    score = vector_similarity
    
    # Boost based on recency
    modified_at = datetime.fromisoformat(payload.get("modified_at"))
    age = datetime.now() - modified_at
    if age < timedelta(days=7):
        score += 0.2
        
    # Boost based on tag matches (example)
    query_tags = set(["important", "todo"])  # Example tags
    doc_tags = set(payload.get("tags", []))
    matching_tags = query_tags.intersection(doc_tags)
    score += len(matching_tags) * 0.1
        
    # Boost based on front matter properties
    frontmatter = payload.get("frontmatter", {})
    if frontmatter.get("priority") == "high":
        score += 0.3
        
    return score
```

## Benefits Over Previous Implementation

1. **Native Obsidian Support**: LangChain's ObsidianLoader is specifically designed for Obsidian's markdown format.
2. **Automatic Feature Detection**: Handles wikilinks, tags, and frontmatter without custom parsing.
3. **Maintained Integration**: Regular updates through the LangChain community.
4. **Robust Parsing**: Better handling of Obsidian's extended markdown syntax.

## Key Functions

- `extract_metadata(file_path)`: Uses ObsidianLoader to extract all metadata.
- `get_document_relationships(metadata)`: Extracts relationship information from metadata.
- `score_with_payload(vector_similarity, payload)`: Scores search results based on vector similarity and payload data.

## Future Enhancements

1. Add support for Obsidian callouts
2. Implement graph-based search using document relationships
3. Add custom scoring based on frontmatter properties
4. Support for dataview metadata