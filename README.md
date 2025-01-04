**Minima-fork** is an open source RAG on-premises container, with MCP access.
Minima can be used as a fully local RAG.

Minima currently supports two modes:
1. Isolated installation – Operate fully on-premises with containers. All neural networks (reranker, embedding) run on your cloud or PC, ensuring your data remains secure.

2. Anthropic Claude – Use Anthropic Claude app to query your local documents. The indexer operates on your local PC, while Anthropic Claude serves as the primary LLM.

**For MCP usage, please be sure that your local machines python is >=3.10 and 'uv' installed.**

1. Create a .env file in the project’s root directory (where you’ll find env.sample). Place .env in the same folder and copy all environment variables from env.sample to .env.

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

Explanation of Variables:

**LOCAL_FILES_PATH**: Specify the root folder for indexing (on your cloud or local pc). Indexing is a recursive process, meaning all documents within subfolders of this root folder will also be indexed. Supported file types: .pdf, .xls, .docx, .txt, .md, .csv.

**EMBEDDING_MODEL_ID**: Specify the embedding model to use. Currently, only Sentence Transformer models are supported. Testing has been done with sentence-transformers/all-mpnet-base-v2, but other Sentence Transformer models can be used.

**EMBEDDING_SIZE**: Define the embedding dimension provided by the model, which is needed to configure Qdrant vector storage. Ensure this value matches the actual embedding size of the specified EMBEDDING_MODEL_ID.

**START_INDEXING**: Set this to ‘true’ on initial startup to begin indexing. Data can be queried while it indexes. Note that reindexing is not yet supported. To reindex, remove the qdrant_data folder (created automatically), set this flag to ‘true,’ and restart the containers. After indexing completes, you can keep the container running or restart without reindexing by setting this flag to ‘false’.

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
