"""Base extractor class."""

from abc import ABC, abstractmethod
from typing import List
from src.models import ExtractionResult


class BaseExtractor(ABC):
    """Abstract base class for reference extractors."""
    
    @abstractmethod
    def extract(self, source: str) -> ExtractionResult:
        """
        Extract references from a source.
        
        Args:
            source: Source to extract from (file path or URL)
            
        Returns:
            ExtractionResult containing extracted references
        """
        pass
    
    def _identify_reference_section(self, text: str) -> str:
        """
        Identify and extract the reference section from text.
        
        Args:
            text: Full text to search
            
        Returns:
            Text containing the reference section
        """
        # Common reference section headers
        headers = [
            r"(?i)references?\b",
            r"(?i)bibliography\b",
            r"(?i)cited works?\b",
            r"(?i)works cited\b",
            r"(?i)further reading\b",
            r"(?i)sources?\b",
        ]
        
        import re
        for header in headers:
            match = re.search(header, text)
            if match:
                # Return text from the header onwards
                return text[match.start():]
        
        # If no header found, assume references are at the end
        # Try to find numbered references or bullet points
        if re.search(r'\n\s*\[\d+\]', text):
            return text
        
        # Return last 30% of text as fallback
        lines = text.split('\n')
        return '\n'.join(lines[int(len(lines) * 0.7):])
