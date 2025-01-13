# System Patterns

## How the system is built
The system is built with a Python backend for indexing and a frontend for searching. The indexing system incorporates advanced reranking capabilities using the BAAI/bge-m3 model and Obsidian-specific features for enhanced document relationships.

## Key technical decisions
- Enhanced Qdrant utilization:
  - Vector embeddings with cosine similarity
  - Payload storage for Obsidian features
  - Custom scoring for relationship weighting
- Adaptive hardware acceleration (MPS -> CUDA -> CPU fallback)
- Document chunking strategy (500 size/200 overlap) with Obsidian syntax preservation
- BAAI/bge-m3 integration for semantic reranking
- HuggingFace embeddings pipeline for vector generation
- Obsidian parser for extracting structured features
- Improved metadata handling for relevance scoring
- Deduplication of search results

## Architecture patterns
- Microservices architecture for scalability
- Enhanced vector search pipeline:
  - Semantic similarity scoring
  - Payload-based filtering and boosting
  - Feature-weighted result ranking
- Adaptive compute resource utilization
- Chunked document processing with metadata preservation
  - Obsidian feature integration:
  - Internal links stored in payload (requires regex parsing)
  - Tags as filterable attributes
  - YAML frontmatter as structured payload
  - Backlinks tracked in payload metadata (deferred for future implementation)
- Document analysis pipeline:
  - The `deep_search` tool provides advanced semantic search with temporal filtering and analysis capabilities.
  - It allows filtering by date range and tags.
  - It supports different analysis modes:
    - `summary`: Summarize matching documents
    - `timeline`: Show documents in chronological order
    - `topics`: Group documents by tags/topics
    - `trends`: Analyze document frequency over time
  - The `query` tool allows users to perform a semantic search across local files (PDF, CSV, DOCX, MD, TXT).
  - The `document_summary` tool provides a concise summary of key documents based on a search query, date range, or tags.
  - The `document_timeline` tool generates a chronological view of notes, highlighting key concepts and allowing grouping by day, week, or month.
  - The `document_topics` tool extracts and groups key topics from notes, identifying main themes and their relationships.
  - The `document_trends` tool analyzes frequency and content patterns in notes over time, showing document count trends.
  - The `deep_search` tool offers advanced semantic search with temporal filtering and analysis capabilities, including modes for summary, timeline, topics, and trends.
  - These tools are integrated into the MCP server and can be called via the `call_tool` method.
