"""Compatibility wrapper for HTML fallback extractor.

The HTML fallback extractor implementation now lives in
``src.extractor.fallbacks.html_fallback``.  This module re-exports the
``HTMLFallbackExtractor`` class to preserve backwards compatibility for any
legacy imports while avoiding duplicate implementations.
"""

from src.extractor.fallbacks.html_fallback import HTMLFallbackExtractor

__all__ = ["HTMLFallbackExtractor"]
