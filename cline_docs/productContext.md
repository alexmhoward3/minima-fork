# Product Context

## Why this project exists
This project aims to provide a tool for indexing and searching through documents. It has connection to Claude and other LLMs via the Model Context Protocol (MCP).

## What problems it solves
- Quickly finding information within a large collection of documents
- Leveraging Obsidian's knowledge graph features for enhanced search relevance
- Understanding and utilizing document relationships through internal links and tags
- Maintaining context through metadata and backlinks

## How it should work
The system should:
- Index documents while preserving Obsidian-specific features:
  - Tags (#tag) for content categorization
  - YAML frontmatter for structured metadata
  - Hierarchical tags for taxonomy
  - Backlinks for reverse relationship tracking (deferred for future implementation)
- Allow users to search using Obsidian syntax and features
- Respect ignore files to prevent indexing of unwanted documents
- Use document relationships to improve search relevance
- Provide advanced analysis capabilities:
  - Summarize key documents (`document_summary`)
  - Generate timelines of documents (`document_timeline`)
  - Group documents by topics/tags (`document_topics`)
  - Analyze document frequency trends over time (`document_trends`)
- Offer both basic and advanced search options
  - Basic search (`query`) for quick lookups
  - Advanced search (`deep_search`) with filtering by date range and tags, and different analysis modes (`summary`, `timeline`, `topics`, `trends`)
