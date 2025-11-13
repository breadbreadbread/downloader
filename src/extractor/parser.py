"""Reference parser for extracting bibliographic information."""

import re
import logging
from typing import Optional, List

from src.models import Reference
from src.utils import (
    extract_doi, extract_pmid, extract_year, extract_urls,
    parse_author_string, extract_last_name, extract_page_range
)

logger = logging.getLogger(__name__)


class ReferenceParser:
    """Parse reference text into structured Reference objects."""
    
    def parse_reference(self, text: str) -> Optional[Reference]:
        """
        Parse a single reference string into a Reference object.
        
        Args:
            text: Raw reference text
            
        Returns:
            Reference object or None if parsing fails
        """
        if not text or len(text.strip()) < 10:
            return None
        
        text = text.strip()
        
        # Create reference with raw text
        ref = Reference(raw_text=text)
        
        # Extract identifiers first (highest priority)
        ref.doi = extract_doi(text)
        ref.pmid = extract_pmid(text)
        ref.arxiv_id = self._extract_arxiv_id(text)
        ref.url = extract_urls(text)[0] if extract_urls(text) else None
        
        # Extract year
        ref.year = extract_year(text)
        
        # Extract authors
        ref.authors = self._extract_authors(text)
        if ref.authors:
            ref.first_author_last_name = extract_last_name(ref.authors[0])
        
        # Extract title
        ref.title = self._extract_title(text)
        
        # Extract journal/venue information
        ref.journal = self._extract_journal(text)
        ref.volume = self._extract_volume(text)
        ref.issue = self._extract_issue(text)
        ref.pages = extract_page_range(text)
        
        # Extract publisher
        ref.publisher = self._extract_publisher(text)
        
        return ref
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract author list from reference."""
        authors = []
        
        # Try to find author list before year or title
        # Common patterns: "Author A and Author B (2023)" or "Author A, Author B. (2023)"
        
        # Pattern 1: Before parentheses with year
        year_pattern = r'\((?:19|20)\d{2}\)'
        year_match = re.search(year_pattern, text)
        if year_match:
            author_section = text[:year_match.start()].strip()
            # Remove trailing punctuation
            author_section = author_section.rstrip('.,;:')
            
            # Try to extract authors
            authors = parse_author_string(author_section)
        
        # Pattern 2: Try common author patterns if not found
        if not authors:
            # Look for "A. Author" style
            author_pattern = r'([A-Z]\.[A-Za-z\s\.]+?)(?:,|\band\b|;|$)'
            matches = re.findall(author_pattern, text[:200])  # Check first 200 chars
            authors = [m.strip() for m in matches if m.strip()]
        
        return authors[:10]  # Limit to 10 authors
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from reference."""
        # Titles are often in quotes or between author and journal
        
        # Pattern 1: Quoted text
        quote_pattern = r'["\']([^"\']{10,})["\']'
        match = re.search(quote_pattern, text)
        if match:
            return match.group(1)
        
        # Pattern 2: Title between authors and year/journal
        year_pattern = r'\((?:19|20)\d{2}\)'
        year_match = re.search(year_pattern, text)
        
        if year_match:
            # Get text between first author-like string and year
            text_before_year = text[:year_match.start()]
            
            # Try to find substantial text that looks like a title
            # Remove author names (usually short, capitalized phrases)
            potential_title = text_before_year
            
            # Clean up
            potential_title = potential_title.replace('(', '').replace(')', '').strip()
            if len(potential_title) > 15:
                return potential_title[:200]  # Limit to 200 chars
        
        # Pattern 3: Look for italicized or emphasized text (marked with special chars)
        # This is approximate since we don't have markup info
        lines = text.split('\n')
        for line in lines:
            if len(line) > 15 and len(line) < 200:
                # Check if it looks like a title (has typical title characteristics)
                if not any(x in line for x in ['http', 'doi', 'ISBN', 'pp.']):
                    return line.strip()
        
        return None
    
    def _extract_journal(self, text: str) -> Optional[str]:
        """Extract journal/venue name from reference."""
        # Journals are often in italics or after specific indicators
        
        # Look for common patterns
        patterns = [
            r'(?:in |In |published in )\*?([A-Z][A-Za-z0-9\s&\-\.]*?)(?:\*?[,\.]|\d)',
            r'(?:journal|Journal)[\s:]*([A-Z][A-Za-z0-9\s&\-\.]*?)(?:[,\.])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                journal = match.group(1).strip()
                if len(journal) > 2:
                    return journal
        
        # Look for common journal abbreviations or patterns
        # Usually appears with volume numbers
        volume_pattern = r'([A-Z][A-Za-z0-9\s&\-\.]*?)\s+(?:vol|volume)?\s*\d+(?:[\s,:]|$)'
        match = re.search(volume_pattern, text, re.IGNORECASE)
        if match:
            journal = match.group(1).strip()
            if len(journal) > 2 and len(journal) < 200:
                return journal
        
        return None
    
    def _extract_volume(self, text: str) -> Optional[str]:
        """Extract journal volume from reference."""
        # Look for "vol X" or "volume X" or just "X" before page numbers
        volume_pattern = r'(?:vol|volume)\.?\s*([0-9]+)'
        match = re.search(volume_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Try "volume(issue)" format
        volume_pattern2 = r'(\d+)\s*\([0-9]+\)'
        match = re.search(volume_pattern2, text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_issue(self, text: str) -> Optional[str]:
        """Extract journal issue from reference."""
        # Look for "issue X" or "no. X" or "(X)" after volume
        issue_pattern = r'(?:issue|no|number)\.?\s*([0-9]+)'
        match = re.search(issue_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Try "(issue)" format
        issue_pattern2 = r'\(\s*([0-9]+)\s*\)'
        match = re.search(issue_pattern2, text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_publisher(self, text: str) -> Optional[str]:
        """Extract publisher from reference."""
        # Look for publisher indicators
        publisher_pattern = r'(?:published by|publisher|pub|Pub)\s*:?\s*([A-Z][A-Za-z0-9\s,&\-\.]*?)(?:[,\.]|$)'
        match = re.search(publisher_pattern, text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _extract_arxiv_id(self, text: str) -> Optional[str]:
        """Extract arXiv ID from reference."""
        # Format: arXiv:YYMM.NNNNN or newer: YYMM.NNNNN
        arxiv_pattern = r'(?:arXiv\s*:?\s*)?(\d{4}\.\d{4,5})'
        match = re.search(arxiv_pattern, text)
        if match:
            arxiv_id = match.group(1)
            # Verify it looks like a valid arXiv ID
            if re.match(r'\d{4}\.\d{4,5}', arxiv_id):
                return arxiv_id
        
        # Check for full arXiv URLs
        arxiv_url_pattern = r'arxiv\.org/abs/(\d{4}\.\d{4,5})'
        match = re.search(arxiv_url_pattern, text)
        if match:
            return match.group(1)
        
        return None
