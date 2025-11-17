"""BibTeX reference extraction from text."""

import logging
import re
from typing import List, Optional

from src.models import Reference

logger = logging.getLogger(__name__)


class BibTeXParser:
    """Parse BibTeX entries into Reference objects."""
    
    def __init__(self):
        pass
    
    def extract_from_text(self, text: str) -> List[Reference]:
        """
        Extract references from BibTeX-formatted text.
        
        Args:
            text: Text containing BibTeX entries
            
        Returns:
            List of Reference objects
        """
        references = []
        
        # BibTeX entry patterns - improved for multi-line entries
        bibtex_pattern = r'@[a-zA-Z]+\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        
        try:
            matches = re.findall(bibtex_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for bibtex_entry in matches:
                try:
                    ref = self._parse_bibtex_entry(bibtex_entry)
                    if ref:
                        references.append(ref)
                        logger.debug(f"Successfully parsed BibTeX entry: {ref.title if ref.title else 'Unknown'}")
                except Exception as e:
                    logger.debug(f"Failed to parse BibTeX entry: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in BibTeX extraction: {str(e)}")
        
        return references
    
    def _parse_bibtex_entry(self, bibtex_text: str) -> Optional[Reference]:
        """Parse a single BibTeX entry into a Reference object."""
        try:
            # Extract entry type and key
            type_match = re.match(r'@([a-zA-Z]+)\s*\{([^,]+)', bibtex_text.strip())
            if not type_match:
                return None
            
            entry_type = type_match.group(1).lower()
            entry_key = type_match.group(2).strip()
            
            # Extract fields
            fields = {}
            # Find all key = value pairs, handling nested braces
            field_pattern = r'(\w+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            
            for field_match in re.finditer(field_pattern, bibtex_text):
                field_name = field_match.group(1).lower()
                field_value = field_match.group(2).strip()
                # Remove surrounding braces and clean up
                field_value = re.sub(r'^\s*|\s*$', '', field_value)
                fields[field_name] = field_value
            
            # Create Reference object
            raw_text = bibtex_text.replace('\n', ' ').strip()
            ref = Reference(raw_text=raw_text)
            
            # Map BibTeX fields to Reference fields
            if 'title' in fields:
                ref.title = fields['title']
            
            if 'author' in fields:
                # Parse author names from BibTeX format
                authors_text = fields['author']
                authors = [author.strip() for author in authors_text.split(' and ')]
                ref.authors = authors
                if authors:
                    # Extract first author's last name
                    first_author = authors[0]
                    if ',' in first_author:
                        ref.first_author_last_name = first_author.split(',')[0].strip()
                    else:
                        parts = first_author.split()
                        ref.first_author_last_name = parts[-1] if parts else first_author
            
            if 'year' in fields:
                year_match = re.search(r'\d{4}', fields['year'])
                if year_match:
                    ref.year = int(year_match.group())
            
            if 'journal' in fields:
                ref.journal = fields['journal']
            
            if 'volume' in fields:
                ref.volume = fields['volume']
            
            if 'number' in fields:
                ref.issue = fields['number']
            
            if 'pages' in fields:
                ref.pages = fields['pages']
            
            if 'doi' in fields:
                ref.doi = fields['doi'].replace('doi:', '').strip()
            
            if 'publisher' in fields:
                ref.publisher = fields['publisher']
            
            # Set publication type based on entry type
            type_mapping = {
                'article': 'journal',
                'inproceedings': 'conference',
                'incollection': 'book',
                'book': 'book',
                'phdthesis': 'thesis',
                'mastersthesis': 'thesis',
                'misc': 'other'
            }
            ref.publication_type = type_mapping.get(entry_type, 'other')
            
            return ref
            
        except Exception as e:
            logger.error(f"Error parsing BibTeX entry: {str(e)}")
            return None