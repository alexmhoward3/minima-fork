import sys
import locale
from . import server
import asyncio

# Fix encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')

def main():
    """Main entry point for the package."""
    asyncio.run(server.main())

# Optionally expose other important items at package level
__all__ = ['main', 'server']