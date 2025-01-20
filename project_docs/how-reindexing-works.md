## How Reindexing Works in Minima

Minima has an automatic reindexing mechanism to keep the search index up-to-date with changes in the file system.

### 1. Scheduled Reindexing

- Reindexing is scheduled to run automatically every 20 minutes.
- This is implemented using the `@repeat_every(seconds=60*20)` decorator on the `schedule_reindexing()` function in `app.py`.
- The `schedule_reindexing()` function calls `trigger_re_indexer()` to start the reindexing process.

### 2. Initial Indexing

- Initial indexing can be triggered when the application starts by setting the `START_INDEXING` environment variable to 'true'.
- This is handled by the `lifespan` context manager in `app.py`.

### 3. The Reindexing Process

- The `trigger_re_indexer()` function creates and runs two asynchronous tasks:
  - `crawl_loop`: Scans the file system for new, modified, or deleted files and adds them to an asynchronous queue for processing.
  - `index_loop`: Processes the files in the queue and updates the Qdrant vector database accordingly.

### 4. File Change Detection using database.db

- The system uses an SQLite database file named "database.db" located in "indexer\_data/" to track the indexing status of files.
- The database contains a table called `MinimaDoc` with the following schema:
    - `fpath` (str): The file path (primary key).
    - `last_updated_seconds` (int): The last modified timestamp of the file in seconds.
- The `MinimaStore` class in `storage.py` manages this database and provides methods to:
    - Create the database and table.
    - Add new files to the database.
    - Update the `last_updated_seconds` of existing files.
    - Delete records for files that have been removed.
    - Check if a file needs to be indexed or reindexed based on its `last_updated_seconds` value.
- The `Indexer` class in `indexer.py` uses `MinimaStore.check_needs_indexing()` to determine whether a file needs to be indexed or reindexed:
    - If a file is new (not in the database), it's marked for indexing.
    - If a file's `last_updated_seconds` is newer than the value in the database, it's marked for reindexing.
    - Otherwise, the file is skipped.
- When `index_loop` processes a file, it updates the `last_updated_seconds` in "database.db" to the current timestamp.
- The `purge()` method in `Indexer` uses `MinimaStore.find_removed_files()` to identify and remove deleted files from the index.

### 5. Summary

The system detects file changes through a combination of scheduled reindexing and by tracking file modification times in "database.db". While it's not using a real-time file system watcher, the regular reindexing process, along with the use of "database.db", ensures that the search index is updated to reflect changes in the file system.
