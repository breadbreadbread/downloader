"""BibTeX reference parser for embedded BibTeX blocks."""

import logging
import re
from typing import List, Optional, Dict, Any
from src.models import Reference

logger = logging.getLogger(__name__)


class BibTeXParser:
    """
    Parse BibTeX formatted references from text.
    
    Handles BibTeX blocks embedded in PDFs or HTML pages.
    """
    
    def __init__(self):
        """Initialize the BibTeX parser."""
        # Note: This pattern is for simple matching, actual parsing happens in parse method
        self.entry_type_pattern = re.compile(
            r'@(\w+)\s*\{',
            re.IGNORECASE
        )
    
    def extract_bibtex_blocks(self, text: str) -> List[str]:
        """
        Extract BibTeX entry blocks from text with proper brace matching.
        
        Args:
            text: Text containing potential BibTeX entries
            
        Returns:
            List of BibTeX entry strings
        """
        blocks = []
        
        # Find all @type{ starts
        for match in self.entry_type_pattern.finditer(text):
            start_pos = match.start()
            brace_start = match.end() - 1  # Position of opening brace
            
            # Find matching closing brace
            brace_count = 0
            end_pos = None
            
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            if end_pos:
                full_entry = text[start_pos:end_pos]
                blocks.append(full_entry)
        
        logger.debug(f"Extracted {len(blocks)} BibTeX entries")
        return blocks
    
    def has_bibtex(self, text: str) -> bool:
        """
        Check if text contains BibTeX entries.
        
        Args:
            text: Text to check
            
        Returns:
            True if BibTeX entries are found
        """
        # Look for BibTeX entry markers
        bibtex_markers = [
            r'@article\s*\{',
            r'@inproceedings\s*\{',
            r'@book\s*\{',
            r'@incollection\s*\{',
            r'@phdthesis\s*\{',
            r'@techreport\s*\{',
        ]
        
        for marker in bibtex_markers:
            if re.search(marker, text, re.IGNORECASE):
                return True
        
        return False
    
    def parse_bibtex_entry(self, entry: str) -> Optional[Reference]:
        """
        Parse a single BibTeX entry into a Reference object.
        
        Args:
            entry: BibTeX entry string
            
        Returns:
            Reference object or None if parsing fails
        """
        try:
            # Extract entry type
            type_match = re.match(r'@(\w+)\s*\{', entry, re.IGNORECASE)
            if not type_match:
                return None
            
            entry_type = type_match.group(1).lower()
            
            # Extract citation key (first field before comma)
            key_match = re.search(r'@\w+\s*\{\s*([^,]+)\s*,', entry, re.IGNORECASE)
            if not key_match:
                return None
            
            citation_key = key_match.group(1).strip()
            
            # Extract fields (everything after citation key)
            fields_start = key_match.end()
            fields_end = entry.rfind('}')
            if fields_end == -1:
                return None
            
            fields_text = entry[fields_start:fields_end]
            
            # Parse fields
            fields = self._parse_bibtex_fields(fields_text)
            
            # Create Reference object
            ref = Reference(
                raw_text=entry,
                metadata={'source': 'bibtex', 'entry_type': entry_type, 'citation_key': citation_key}
            )
            
            # Map BibTeX fields to Reference fields
            ref.title = fields.get('title')
            ref.authors = self._parse_bibtex_authors(fields.get('author', ''))
            ref.year = self._extract_year_from_bibtex(fields)
            ref.journal = fields.get('journal') or fields.get('booktitle')
            ref.volume = fields.get('volume')
            ref.issue = fields.get('number')
            ref.pages = fields.get('pages')
            ref.publisher = fields.get('publisher')
            ref.doi = fields.get('doi')
            ref.url = fields.get('url')
            
            # Set first author last name
            if ref.authors:
                ref.first_author_last_name = self._extract_last_name(ref.authors[0])
            
            logger.debug(f"Parsed BibTeX entry: {citation_key}")
            return ref
            
        except Exception as e:
            logger.warning(f"Error parsing BibTeX entry: {str(e)}")
            return None
    
    def _parse_bibtex_fields(self, fields_text: str) -> Dict[str, str]:
        """
        Parse BibTeX field assignments.
        
        Args:
            fields_text: Text containing field assignments
            
        Returns:
            Dictionary of field names to values
        """
        fields = {}
        
        # Pattern to match field = {value} or field = "value"
        field_pattern = re.compile(
            r'(\w+)\s*=\s*(?:\{([^}]*)\}|"([^"]*)")',
            re.DOTALL
        )
        
        for match in field_pattern.finditer(fields_text):
            field_name = match.group(1).lower()
            # Try braces first, then quotes
            field_value = match.group(2) if match.group(2) else match.group(3)
            
            if field_value:
                # Clean up the value
                field_value = field_value.strip()
                fields[field_name] = field_value
        
        return fields
    
    def _parse_bibtex_authors(self, author_string: str) -> List[str]:
        """
        Parse BibTeX author field.
        
        Args:
            author_string: BibTeX author field value
            
        Returns:
            List of author names
        """
        if not author_string:
            return []
        
        # BibTeX uses "and" to separate authors
        authors = author_string.split(' and ')
        
        # Clean up each author name
        cleaned_authors = []
        for author in authors:
            author = author.strip()
            if author:
                # Remove extra whitespace and newlines
                author = re.sub(r'\s+', ' ', author)
                cleaned_authors.append(author)
        
        return cleaned_authors[:10]  # Limit to 10 authors
    
    def _extract_year_from_bibtex(self, fields: Dict[str, str]) -> Optional[int]:
        """
        Extract year from BibTeX fields.
        
        Args:
            fields: Dictionary of BibTeX fields
            
        Returns:
            Year as integer or None
        """
        year_str = fields.get('year', '')
        
        # Try to extract 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', year_str)
        if year_match:
            return int(year_match.group(0))
        
        return None
    
    def _extract_last_name(self, author: str) -> str:
        """
        Extract last name from author string.
        
        Args:
            author: Author name string
            
        Returns:
            Last name
        """
        # BibTeX format can be "Last, First" or "First Last"
        if ',' in author:
            # "Last, First" format
            return author.split(',')[0].strip()
        else:
            # "First Last" format - take last word
            parts = author.split()
            if parts:
                return parts[-1]
        
        return author