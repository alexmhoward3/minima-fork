LangChain Python API Reference
document_loaders
ObsidianLoader
ObsidianLoader
class langchain_community.document_loaders.obsidian.ObsidianLoader(path: str | Path, encoding: str = 'UTF-8', collect_metadata: bool = True)
[source]

Load Obsidian files from directory.

Initialize with a path.

Parameters
:

path (str | Path) – Path to the directory containing the Obsidian files.

encoding (str) – Charset encoding, defaults to “UTF-8”

collect_metadata (bool) – Whether to collect metadata from the front matter. Defaults to True.

Attributes

DATAVIEW_INLINE_BRACKET_REGEX

	




DATAVIEW_INLINE_PAREN_REGEX

	




DATAVIEW_LINE_REGEX

	




FRONT_MATTER_REGEX

	




TAG_REGEX

	




TEMPLATE_VARIABLE_REGEX

	

Methods

__init__(path[, encoding, collect_metadata])

	

Initialize with a path.




alazy_load()

	

A lazy loader for Documents.




aload()

	

Load data into Document objects.




lazy_load()

	

A lazy loader for Documents.




load()

	

Load data into Document objects.




load_and_split([text_splitter])

	

Load Documents and split into chunks.

__init__(path: str | Path, encoding: str = 'UTF-8', collect_metadata: bool = True)
[source]

Initialize with a path.

Parameters
:

path (str | Path) – Path to the directory containing the Obsidian files.

encoding (str) – Charset encoding, defaults to “UTF-8”

collect_metadata (bool) – Whether to collect metadata from the front matter. Defaults to True.

async alazy_load() → AsyncIterator[Document]

A lazy loader for Documents.

Return type
:

AsyncIterator[Document]

async aload() → List[Document]

Load data into Document objects.

Return type
:

List[Document]

lazy_load() → Iterator[Document]
[source]

A lazy loader for Documents.

Return type
:

Iterator[Document]

load() → List[Document]

Load data into Document objects.

Return type
:

List[Document]

load_and_split(text_splitter: TextSplitter | None = None) → List[Document]

Load Documents and split into chunks. Chunks are returned as Documents.

Do not override this method. It should be considered to be deprecated!

Parameters
:

text_splitter (Optional[TextSplitter]) – TextSplitter instance to use for splitting documents. Defaults to RecursiveCharacterTextSplitter.

Returns
:

List of Documents.

Return type
:

List[Document]

Examples using ObsidianLoader

Obsidian

ObsidianLoader
ObsidianLoader.__init__()
ObsidianLoader.alazy_load()
ObsidianLoader.aload()
ObsidianLoader.lazy_load()
ObsidianLoader.load()
ObsidianLoader.load_and_split()