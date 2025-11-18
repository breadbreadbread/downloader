"""Reference extraction module."""
# isort: skip_file

from .base import BaseExtractor
from .fallbacks import (
    BibTeXParser,
    ExtractionFallbackManager,
    HTMLFallbackExtractor,
    TableExtractor,
)
from .parser import ReferenceParser
from .pdf_extractor import PDFExtractor
from .web_extractor import WebExtractor

__all__ = [
    "BaseExtractor",
    "PDFExtractor",
    "WebExtractor",
    "ReferenceParser",
    "BibTeXParser",
    "HTMLFallbackExtractor",
    "TableExtractor",
    "ExtractionFallbackManager",
]
