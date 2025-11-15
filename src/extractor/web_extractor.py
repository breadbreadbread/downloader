"""Web page reference extractor."""

import logging
from typing import List
import requests
from bs4 import BeautifulSoup

from src.models import ExtractionResult, Reference
from src.extractor.base import BaseExtractor
from src.extractor.parser import ReferenceParser
from src.config import settings
from src.network.http_client import HTTPClient

logger = logging.getLogger(__name__)


class WebExtractor(BaseExtractor):
    """Extract references from web pages."""
    
    def __init__(self):
        self.parser = ReferenceParser()
        self.http_client = HTTPClient()
    
    def extract(self, source: str) -> ExtractionResult:
        """
        Extract references from a web page.
        
        Args:
            source: URL to fetch
            
        Returns:
            ExtractionResult containing extracted references
        """
        result = ExtractionResult(source=source)
        
        if not source.startswith(('http://', 'https://')):
            result.extraction_errors.append("Invalid URL format")
            return result
        
        try:
            response = self.http_client.get(
                source,
                allow_redirects=True
            )
            
            html_text = response.text
            references_text = self._extract_references_from_html(html_text)
            references = self._parse_references(references_text)
            
            result.references = references
            result.total_references = len(references)
            
            logger.info(f"Extracted {len(references)} references from {source}")
            
        except requests.RequestException as e:
            error_msg = f"Error fetching URL: {str(e)}"
            result.extraction_errors.append(error_msg)
            logger.error(f"Error fetching {source}: {str(e)}")
        except Exception as e:
            error_msg = f"Error extracting references: {str(e)}"
            result.extraction_errors.append(error_msg)
            logger.error(f"Error extracting from {source}: {str(e)}")
        
        return result
    
    def _extract_references_from_html(self, html: str) -> str:
        """Extract text content from HTML."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Find reference section
        return self._identify_reference_section(text)
    
    def _parse_references(self, text: str) -> List[Reference]:
        """Parse reference text into structured references."""
        if not text or len(text.strip()) == 0:
            return []
        
        references_raw = self._split_references(text)
        
        references = []
        for ref_text in references_raw:
            try:
                ref = self.parser.parse_reference(ref_text)
                if ref:
                    references.append(ref)
            except Exception as e:
                logger.warning(f"Error parsing reference: {str(e)}")
        
        return references
    
    def _split_references(self, text: str) -> List[str]:
        """Split reference text into individual references."""
        import re
        
        references = []
        
        # Try numbered references [1], [2], etc.
        numbered_pattern = r'\n\s*\[\d+\]'
        if re.search(numbered_pattern, text):
            parts = re.split(numbered_pattern, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            return references
        
        # Try numbered references 1., 2., etc.
        numbered_pattern2 = r'\n\s*\d+\.\s'
        if re.search(numbered_pattern2, text):
            parts = re.split(numbered_pattern2, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            return references
        
        # Try bullet points
        bullet_pattern = r'\n\s*[-•*]\s'
        if re.search(bullet_pattern, text):
            parts = re.split(bullet_pattern, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            return references
        
        # Fallback: split by double newlines
        parts = text.split('\n\n')
        references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
        
        return references if references else [text]
