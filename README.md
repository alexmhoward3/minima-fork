**Minima-fork** is an open source RAG on-premises container, with MCP access.
Minima can be used as a fully local RAG.

Minima currently supports two modes:
1. Isolated installation – Operate fully on-premises with containers. All neural networks (reranker, embedding) run on your cloud or PC, ensuring your data remains secure.

2. Anthropic Claude – Use Anthropic Claude app to query your local documents. The indexer operates on your local PC, while Anthropic Claude serves as the primary LLM.

**For MCP usage, please be sure that your local machines python is >=3.10 and 'uv' installed.**

1. Create a .env file in the project's root directory (where you'll find env.sample). Place .env in the same folder and copy all environment variables from env.sample to .env.

2. Ensure your .env file includes the following variables:
<ul>
   <li> LOCAL_FILES_PATH </li>
   <li> EMBEDDING_MODEL_ID </li>
   <li> EMBEDDING_SIZE </li>
   <li> START_INDEXING </li>
   <li> RERANKER_MODEL </li>
</ul>

1. For MCP integration (Anthropic Desktop app usage): **docker compose -f docker-compose-mcp.yml --env-file .env up --build**.

2. If you use Anthropic Claude, just add folliwing to **/Library/Application\ Support/Claude/claude_desktop_config.json**

```
{
    "mcpServers": {
      "minima": {
        "command": "uv",
        "args": [
          "--directory",
          "/path_to_cloned_minima_project/mcp-server",
          "run",
          "minima"
        ]
      }
    }
  }
```

## Environment Variables

**LOCAL_FILES_PATH**: Specify the root folder for indexing (on your cloud or local pc). Indexing is a recursive process, meaning all documents within subfolders of this root folder will also be indexed. Supported file types: .pdf, .xls, .docx, .txt, .md, .csv.

**EMBEDDING_MODEL_ID**: Specify the embedding model to use. Currently, only Sentence Transformer models are supported. Testing has been done with sentence-transformers/all-mpnet-base-v2, but other Sentence Transformer models can be used.

**EMBEDDING_SIZE**: Define the embedding dimension provided by the model, which is needed to configure Qdrant vector storage. Ensure this value matches the actual embedding size of the specified EMBEDDING_MODEL_ID.

**START_INDEXING**: Set this to 'true' on initial startup to begin indexing. Data can be queried while it indexes. Note that reindexing is not yet supported. To reindex, remove the qdrant_data folder (created automatically), set this flag to 'true,' and restart the containers. After indexing completes, you can keep the container running or restart without reindexing by setting this flag to 'false'.

**RERANKER_MODEL**: Specify the reranker model. Currently, we have tested with BAAI rerankers. You can explore all available rerankers using this [link](https://huggingface.co/collections/BAAI/).

Example of .env file for on-premises/local usage:
```
LOCAL_FILES_PATH=/Users/davidmayboroda/Downloads/PDFs/
EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
EMBEDDING_SIZE=768
START_INDEXING=false # true on the first run for indexing
RERANKER_MODEL=BAAI/bge-reranker-base # please, choose any BAAI reranker model
```

Example of .env file for Claude app:
```
LOCAL_FILES_PATH=/Users/davidmayboroda/Downloads/PDFs/
EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
EMBEDDING_SIZE=768
START_INDEXING=false # true on the first run for indexing
```
For the Claude app, please apply the changes to the claude_desktop_config.json file as outlined above.

## Deep Search Tool

The Deep Search tool provides advanced search capabilities with temporal filtering and analysis features. It extends the basic search functionality with the ability to analyze document patterns, trends, and relationships over time.

### Query Structure

```python
{
    "query": "your search query",          # Required - The search text
    "mode": "summary",                     # Optional - Analysis mode (default: "summary")
    "time_frame": "this_week",            # Optional - Predefined time period
    "start_date": "2024-01-01T00:00:00",  # Optional - Custom start date
    "end_date": "2024-01-10T00:00:00",    # Optional - Custom end date
    "include_raw": false,                  # Optional - Include raw documents (default: false)
    "tags": ["meeting", "project"]         # Optional - Filter by tags
}
```

### Search Modes

The tool supports four analysis modes:

1. **summary** (default)
   - Provides a concise summary of matching documents
   - Highlights key points and common themes

2. **timeline**
   - Organizes information chronologically
   - Shows how topics or discussions evolved over time

3. **topics**
   - Identifies and clusters main topics
   - Shows relationships between different subjects

4. **trends**
   - Analyzes patterns and changes over time
   - Identifies emerging or declining topics

### Time Filtering

Two ways to specify time ranges:

1. Predefined time frames:
   - `today`
   - `this_week`
   - `this_month`
   - `this_year`
   - `custom`

2. Custom date range:
   - Use `start_date` and `end_date` for precise periods
   - Dates should be in ISO format (YYYY-MM-DDTHH:MM:SS)

Note: When using `custom` time frame, both `start_date` and `end_date` are required.

### Example Queries

1. Summarize this week's meeting notes:
```json
{
    "query": "meeting discussion",
    "mode": "summary",
    "time_frame": "this_week",
    "tags": ["meeting"]
}
```

2. Analyze topic evolution with custom date range:
```json
{
    "query": "project progress",
    "mode": "trends",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-10T00:00:00",
    "include_raw": true
}
```

### Response Format

The response includes:

```json
{
    "analysis": "Analysis based on the selected mode",
    "metadata": {
        "total_documents": 10,
        "time_period": "2024-01-01 to 2024-01-10",
        "tags": ["meeting", "project"]
    },
    "raw_results": [  // Only included if include_raw is true
        {
            "source": "path/to/document",
            "content": "Document content",
            "tags": ["meeting"],
            "modified_at": "2024-01-05T10:30:00"
        }
    ]
}
```