# Active Context

## What you're working on now
The .minimaignore file functionality has been fixed.

## Recent changes
- Fixed the .minimaignore implementation by making the path handling consistent within the container.
  - The .minimaignore file is now loaded from the container path (/usr/src/app/local_files/) where the files are actually mounted.
  - Path matching is done consistently using paths relative to the container mount point.
  - Added debug logging to help troubleshoot pattern matching.
  - Added better error handling for path operations.

## Next steps
Look for a new embedding model.

The embedding model will remain `sentence-transformers/all-mpnet-base-v2`.
