"""Compatibility wrapper for BibTeX parser.

The BibTeX parser implementation now lives in
``src.extractor.fallbacks.bibtex_parser``.  This module re-exports the
``BibTeXParser`` class to preserve backwards compatibility for any legacy
imports while avoiding duplicate implementations.
"""

from src.extractor.fallbacks.bibtex_parser import BibTeXParser

__all__ = ["BibTeXParser"]
