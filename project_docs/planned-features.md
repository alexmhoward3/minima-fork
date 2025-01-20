1.  caching huggingface models
2. X .minimaignore - file that flags directories and files to ignore
3. X gpu usage
4. x move qdrant_data to F drive
5. Configurable chunking strategy (size, overlap, character or H2)
6. x Improved ObsidianLoader integration:
    Built-in metadata extraction
    Tag parsing from frontmatter and inline
    Proper timestamp handling
    Standardized metadata format
    Focus on create and modification times as key values
7. BAAI/bge-m3 reranker implementation
8. MCP tools: 
   1. refactor into tools directory
   2. topic trends/temporal-based search -  track the semantic drift of concepts through your knowledge base. This could enable fascinating queries like "How has my understanding of [concept] evolved over the past year?"