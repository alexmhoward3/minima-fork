# Qdrant MCP Server Implementation Plan

This document outlines the plan for creating a new MCP server that connects directly to a Qdrant database for vector search.

## Project Setup

1. **Directory Creation:**
    *   Create a new directory named `qdrant-server` within the default MCP servers directory: `C:\Users\Alex\Documents\Cline\MCP\qdrant-server`.
2. **Initialization:**
    *   Initialize a new Python project using `uv`:
        ```bash
        cd C:\Users\Alex\Documents\Cline\MCP\qdrant-server
        uv init
        uv venv
        ```
3. **Dependency Installation:**
    *   Install the necessary dependencies:
        ```bash
        uv add mcp qdrant-client
        ```

## Server Implementation

1. **File Structure:**
    *   Create a main server file: `server.py`.
2. **Import Statements:**
    ```python
    from mcp.server.fastmcp import FastMCP
    from qdrant_client import QdrantClient, models
    ```
3. **Server Initialization:**
    ```python
    mcp = FastMCP("qdrant-server")
    ```
4. **Tool Definition:**
    *   **List Tools Handler:**
        ```python
        @mcp.tool()
        async def list_tools() -> list[dict]:
            return [
                {
                    "name": "search_documents",
                    "description": "Search documents in the Qdrant database.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query string."
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        ```
    *   **Call Tool Handler:**
        ```python
        @mcp.tool()
        async def search_documents(query: str) -> str:
            \"\"\"
            Perform a vector search in the Qdrant database.

            Args:
                query: The search query string.

            Returns:
                A string containing the formatted search results.
            \"\"\"
            client = QdrantClient(host="localhost", port=6333) # Connect to Qdrant

            # Perform search using the Qdrant client
            search_result = client.search(
                collection_name="documents", # Replace with your collection name
                query_vector=[...], # Replace with the query vector
                query_filter=None, # Add any filters here
                limit=10 # Limit the number of results
            )

            # Format the search results
            formatted_results = []
            for hit in search_result:
                formatted_results.append(f"Document: {hit.payload['document_id']}, Score: {hit.score}") # Customize based on your payload structure

            return "\n".join(formatted_results)
        ```
5. **Qdrant Client Initialization:**
    ```python
    client = QdrantClient(host="localhost", port=6333) # Initialize Qdrant client
    ```
6. **Search Logic:**
    *   Implement the vector search logic within the `search_documents` tool using the `qdrant_client`'s `search` method.
    *   Retrieve the search query from the tool's input parameters.
    *   Convert the search query into a vector embedding (if necessary).
    *   Specify the collection name to search in.
    *   Optionally, add filters to narrow down the search results.
    *   Set a limit on the number of results returned.
7. **Error Handling:**
    *   Wrap the Qdrant client calls in `try-except` blocks to handle potential errors (e.g., connection errors, invalid queries).
    *   Return informative error messages in the tool's output.
8. **Logging:**
    *   Use `print` statements to log important events, such as server startup, tool calls, and errors. These will be captured by stderr.

## MCP Server Configuration

1. Add the new MCP server to the `cline_mcp_settings.json` file:
    ```json
    {
      "mcpServers": {
        "qdrant-server": {
          "command": "uv",
          "args": ["run", "C:\\Users\\Alex\\Documents\\Cline\\MCP\\qdrant-server\\server.py"],
          "env": {
            "PYTHONPATH": "C:\\Users\\Alex\\Documents\\Cline\\MCP\\qdrant-server"
          },
          "disabled": false,
          "alwaysAllow": []
        }
      }
    }
    ```

## Testing

1. Test the server locally using the MCP Inspector or by manually sending requests.
2. Verify that the server can connect to the Qdrant database and perform searches.
3. Test with various search queries and edge cases.