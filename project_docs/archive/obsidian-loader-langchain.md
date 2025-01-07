LangChain Python API Reference
langchain-community: 0.3.13
document_loaders
ObsidianLoader
ObsidianLoader#
class langchain_community.document_loaders.obsidian.ObsidianLoader(path: str | Path, encoding: str = 'UTF-8', collect_metadata: bool = True)
[source]
#

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
#

Initialize with a path.

Parameters
:

path (str | Path) – Path to the directory containing the Obsidian files.

encoding (str) – Charset encoding, defaults to “UTF-8”

collect_metadata (bool) – Whether to collect metadata from the front matter. Defaults to True.

async alazy_load() → AsyncIterator[Document]#

A lazy loader for Documents.

Return type
:

AsyncIterator[Document]

async aload() → list[Document]#

Load data into Document objects.

Return type
:

list[Document]

lazy_load() → Iterator[Document]
[source]
#

A lazy loader for Documents.

Return type
:

Iterator[Document]

load() → list[Document]#

Load data into Document objects.

Return type
:

list[Document]

load_and_split(text_splitter: TextSplitter | None = None) → list[Document]#

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

list[Document]

Examples using ObsidianLoader

Obsidian

ObsidianLoader
__init__()
alazy_load()
aload()
lazy_load()
load()
load_and_split()
