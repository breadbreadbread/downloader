"""Reference extraction module."""

from .base import BaseExtractor
from .pdf_extractor import PDFExtractor
from .web_extractor import WebExtractor
from .parser import ReferenceParser
from .fallbacks.bibtex_parser import BibTeXParser
from .fallbacks.html_fallback import HTMLFallbackExtractor
from .fallbacks.table_extractor import TableExtractor

__all__ = [
    "BaseExtractor",
    "PDFExtractor",
    "WebExtractor",
    "ReferenceParser",
    "BibTeXParser",
    "HTMLFallbackExtractor",
    "TableExtractor",
]
