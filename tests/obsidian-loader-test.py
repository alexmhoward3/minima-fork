import asyncio
import sys
sys.path.append('.')
from indexer.indexer import Indexer, Config
from pathlib import Path
from langchain_community.document_loaders import ObsidianLoader

async def test_search(query: str, test_path: str):
    # Test with current TextLoader
    indexer = Indexer()
    results_text = indexer.find(query)
    
    # Modify Config to use ObsidianLoader
    Config.EXTENSIONS_TO_LOADERS[".md"] = ObsidianLoader
    indexer_obsidian = Indexer()
    results_obsidian = indexer_obsidian.find(query)
    
    print(f"Query: {query}\n")
    print("TextLoader Results:")
    print(f"Links found: {len(results_text['links'])}")
    print(f"First result: {results_text['output'][:200]}...\n")
    
    print("ObsidianLoader Results:")
    print(f"Links found: {len(results_obsidian['links'])}")
    print(f"First result: {results_obsidian['output'][:200]}...")

# Test with sample queries
queries = [
    "project architecture",
    "#important tasks",
    "[[linked notes]]"
]

async def main():
    for query in queries:
        await test_search(query, "/Users/alexhoward/Projects/minima-fork/sample_vault")

if __name__ == "__main__":
    asyncio.run(main())
