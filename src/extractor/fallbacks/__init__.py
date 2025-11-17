"""Extraction fallback components."""

from .bibtex_parser import BibTeXParser
from .html_fallback import HTMLFallbackExtractor
from .table_extractor import TableExtractor
from .manager import ExtractionFallbackManager

__all__ = ["BibTeXParser", "HTMLFallbackExtractor", "TableExtractor", "ExtractionFallbackManager"]