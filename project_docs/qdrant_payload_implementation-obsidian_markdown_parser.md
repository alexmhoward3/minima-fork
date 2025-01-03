# Qdrant Payload Implementation Details (using Obsidian Markdown Parser)

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
  "modified_at": "ISO timestamp"
}
```

## Metadata Extraction

The following code snippets demonstrate how to extract metadata from Obsidian notes:

### Metadata Extraction

The following code snippets demonstrate how to extract metadata from Obsidian notes using the `Obsidian-Markdown-Parser` library:

```python
from src.Parser import Parser
from src.YamlParser import YamlParser, YAML_METHOD
import os
import datetime
import uuid

def extract_metadata(file_path):
    parser = Parser(os.path.dirname(file_path))
    file = next((f for f in parser.mdFiles if f.path == file_path), None)
    if not file:
        return None

    # Extract file path
    file_path = file.path

    # Generate chunk ID
    chunk_id = str(uuid.uuid4())

    # Extract heading (this requires reading the file content)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        heading = get_heading(content)

    # Extract tags
    tags = file.tags

    # Extract links
    links = file.links

    # Extract timestamps
    created_at = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
    modified_at = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

    return {
        "file_path": file_path,
        "chunk_id": chunk_id,
        "heading": heading,
        "tags": list(tags),
        "links": list(links),
        "created_at": created_at,
        "modified_at": modified_at
    }

def get_heading(text):
    import re
    match = re.search(r"^#+\s+(.*)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None
```

## Document Relationship Tracking

Document relationships will be tracked by storing links in the `links` field of the payload. A graph database or similar structure can be used to efficiently query these relationships.

## Payload-Based Scoring

Payload fields will be used to boost or penalize search results. For example, results from recently modified notes could be boosted. The scoring function will be configurable by the user.

```python
def score_with_payload(vector_similarity, payload):
    score = vector_similarity
    # Example: boost score for recent notes
    modified_at = datetime.datetime.fromisoformat(payload.get("modified_at"))
    age = datetime.datetime.now() - modified_at
    if age < datetime.timedelta(days=7):
        score += 0.2
    return score
```

## Key Functions

- `extract_metadata(file_path, text)`: Extracts all metadata from a given file path and text content.
- `create_payload(file_path, text)`: Creates a Qdrant payload from the extracted metadata.
- `score_with_payload(vector_similarity, payload)`: Scores search results based on vector similarity and payload data.
