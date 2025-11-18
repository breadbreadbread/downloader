"""Extraction fallback components."""

from .bibtex_parser import BibTeXParser
from .html_fallback import HTMLFallbackExtractor
from .manager import ExtractionFallbackManager
from .table_extractor import TableExtractor

__all__ = [
    "BibTeXParser",
    "HTMLFallbackExtractor",
    "TableExtractor",
    "ExtractionFallbackManager",
]
