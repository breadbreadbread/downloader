"""Compatibility wrapper for the PDF table extractor.

The table extractor used by fallback processing now resides in
``src.extractor.fallbacks.table_extractor``.  This module re-exports the
``TableExtractor`` class so that existing imports continue to work without
maintaining duplicate implementations.
"""

from src.extractor.fallbacks.table_extractor import TableExtractor

__all__ = ["TableExtractor"]
