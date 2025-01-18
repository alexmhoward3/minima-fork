import logging
from typing import Dict, Any
from collections import defaultdict

# Custom formatter with emojis
class EmojiFormatter(logging.Formatter):
    EMOJI_LEVELS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨"
    }

    def format(self, record):
        # Add emoji only if not already present
        if not hasattr(record, 'emoji'):
            emoji = self.EMOJI_LEVELS.get(record.levelno, "")
            record.emoji = emoji
        return super().format(record)

# Aggregate logger for batch operations
class AggregateLogger:
    def __init__(self):
        self.reset_counters()
        self.logger = logging.getLogger("indexer.aggregate")

    def reset_counters(self):
        self.counters = defaultdict(int)
        self.details = defaultdict(list)

    def add_event(self, event_type: str, detail: Any = None):
        self.counters[event_type] += 1
        if detail:
            self.details[event_type].append(detail)

    def summarize(self, reset: bool = True):
        summary = []
        for event_type, count in self.counters.items():
            if count > 0:
                summary.append(f"{count} {event_type}")

        if summary:
            self.logger.info("📊 Batch Summary: " + ", ".join(summary))
            
        if reset:
            self.reset_counters()

def configure_logging(force=False):
    """Configure logging with emoji support and proper log levels.
    
    Args:
        force: If True, reconfigure logging even if already configured
    """
    # Prevent multiple configurations
    if hasattr(configure_logging, '_configured') and not force:
        return logging.getLogger('indexer.aggregate')
    configure_logging._configured = True

    # Remove any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    detailed_formatter = EmojiFormatter(
        '%(asctime)s %(emoji)s %(message)s',
        datefmt='%H:%M:%S'
    )

    # Configure root logger
    root_logger.setLevel(logging.INFO)

    # Console handler with detailed format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(detailed_formatter)
    console_handler.addFilter(lambda record: not any(module in record.name.lower() for module in 
        ['uvicorn', 'asyncio', 'httpx']))
    root_logger.addHandler(console_handler)

    # Set specific log levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Create and return aggregate logger instance
    return AggregateLogger()
