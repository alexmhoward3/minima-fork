1. caching huggingface models
2. .minimaignore - file that flags directories and files to ignore
3. move qdrant_data to F drive
4. Configurable chunking strategy (size, overlap, character or H2)
5. Improved ObsidianLoader integration:
    Built-in metadata extraction
    Tag parsing from frontmatter and inline
    Proper timestamp handling
    Standardized metadata format
6. BAAI/bge-m3 reranker implementation
7. MCP tools: 
   1. refactor into tools directory
   2. topic trends/temporal-based search -  track the semantic drift of concepts through your knowledge base. This could enable fascinating queries like "How has my understanding of [concept] evolved over the past year?"