"""HTML structure-based reference extraction."""

import logging
from typing import List
from bs4 import BeautifulSoup

from src.models import Reference
from src.extractor.parser import ReferenceParser

logger = logging.getLogger(__name__)


class HTMLFallbackExtractor:
    """Extract references from HTML structure elements."""
    
    def __init__(self):
        self.parser = ReferenceParser()
    
    def extract_from_html(self, html_content: str) -> List[Reference]:
        """
        Extract references from HTML structure elements.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            List of Reference objects
        """
        references = []
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Look for structured elements that might contain references
            selectors = [
                'ol li',           # Ordered list items
                'ul li',           # Unordered list items
                'cite',            # Citation elements
                '.reference',      # Elements with reference class
                '.citation',       # Elements with citation class
                '[id*="ref"]',   # Elements with ref in id
            ]
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    
                    for element in elements:
                        text = element.get_text(strip=True)
                        
                        # Skip very short or very long text
                        if len(text) < 20 or len(text) > 1000:
                            continue
                        
                        # Skip if it doesn't look like a reference
                        if not self._looks_like_reference(text):
                            continue
                        
                        try:
                            ref = self.parser.parse_reference(text)
                            if ref:
                                references.append(ref)
                                logger.debug(f"Extracted HTML reference: {text[:50]}...")
                        except Exception as e:
                            logger.debug(f"Failed to parse HTML reference: {text[:50]}... - {str(e)}")
                
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in HTML structure extraction: {str(e)}")
        
        return references
    
    def _looks_like_reference(self, text: str) -> bool:
        """Heuristically determine if text looks like a reference."""
        if not text or len(text.strip()) < 20:
            return False
        
        # Look for reference indicators
        import re
        patterns = [
            r'\b\d{4}\b',  # Years
            r'\bdoi:\s*10\.|10\.\d+',  # DOI patterns
            r'\bvol\.?\s*\d+|volume\s*\d+',  # Volume patterns
            r'\bpp\.?\s*\d+|pages?\s*\d+',  # Page patterns
            r'\[?\d+\]?',  # Reference numbers
            r'\b(ed|eds|editors?)\.?\b',  # Editor indicators
            r'\b(in|proc|conference|journal|university|press)\b',  # Publication venues
        ]
        
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        return pattern_matches >= 2