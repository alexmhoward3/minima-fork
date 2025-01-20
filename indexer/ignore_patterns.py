import os
import fnmatch
import logging
from typing import List

logger = logging.getLogger(__name__)

class IgnorePatterns:
    def __init__(self, vault_path: str):
        self.patterns: List[str] = []
        self.vault_path = vault_path
        self.load_patterns()

    def load_patterns(self) -> None:
        """Load patterns from .minimaignore file if it exists."""
        ignore_file = os.path.join(self.vault_path, '.minimaignore')
        logger.info(f"Looking for .minimaignore at: {ignore_file}")
        
        if os.path.exists(ignore_file):
            logger.info("Found .minimaignore file")
            with open(ignore_file, 'r') as f:
                self.patterns = [
                    line.strip() 
                    for line in f.readlines() 
                    if line.strip() and not line.startswith('#')
                ]
            logger.info(f"Loaded ignore patterns: {self.patterns}")
        else:
            logger.warning("No .minimaignore file found")

    def should_ignore(self, path: str) -> bool:
        """Check if a given path should be ignored based on the patterns."""
        # Get relative path from vault root
        try:
            rel_path = os.path.relpath(path, self.vault_path)
        except ValueError:
            logger.error(f"Could not get relative path for {path} from {self.vault_path}")
            return False
            
        for pattern in self.patterns:
            # Remove trailing slashes for directory patterns
            pattern = pattern.rstrip('/')
            
            # Check if path matches the pattern
            if fnmatch.fnmatch(rel_path, pattern):
                logger.info(f"Ignoring {rel_path} - matches pattern {pattern}")
                return True
            
            # Check if any parent directory matches the pattern
            path_parts = rel_path.split(os.sep)
            for i in range(len(path_parts)):
                partial_path = os.sep.join(path_parts[:i+1])
                if fnmatch.fnmatch(partial_path, pattern):
                    logger.info(f"Ignoring {rel_path} - parent dir matches pattern {pattern}")
                    return True
        
        return False