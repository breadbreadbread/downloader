"""Table-based reference extraction from PDF documents."""

import logging
from typing import List
import pdfplumber

from src.models import Reference
from src.extractor.parser import ReferenceParser

logger = logging.getLogger(__name__)


class TableExtractor:
    """Extract references from tables in PDF documents."""
    
    def __init__(self):
        self.parser = ReferenceParser()
    
    def extract_from_pdf(self, pdf_object) -> List[Reference]:
        """
        Extract references from PDF tables.
        
        Args:
            pdf_object: pdfplumber PDF object
            
        Returns:
            List of Reference objects extracted from tables
        """
        references = []
        
        try:
            for page_num, page in enumerate(pdf_object.pages):
                try:
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if not table:
                            continue
                        
                        # Check if this looks like a reference table
                        table_text = self._normalize_table_cells(table)
                        if self._looks_like_reference_table(table_text):
                            table_refs = self._parse_table_references(table_text)
                            references.extend(table_refs)
                            logger.info(f"Extracted {len(table_refs)} references from table {table_idx+1} on page {page_num+1}")
                        
                except Exception as e:
                    logger.warning(f"Error extracting tables from page {page_num}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in table extraction: {str(e)}")
        
        return references
    
    def _normalize_table_cells(self, table: List[List[str]]) -> str:
        """Normalize table cells into a coherent text string."""
        normalized_rows = []
        
        for row in table:
            if not row:
                continue
            
            # Filter out empty cells and strip whitespace
            cells = [cell.strip() for cell in row if cell and cell.strip()]
            
            if cells:
                # Join cells with reasonable spacing
                row_text = " ".join(cells)
                normalized_rows.append(row_text)
        
        return "\n".join(normalized_rows)
    
    def _looks_like_reference_table(self, text: str) -> bool:
        """Heuristically determine if table text contains references."""
        if not text or len(text.strip()) < 50:
            return False
        
        # Look for reference patterns
        import re
        patterns = [
            r'\b\d{4}\b',  # Years
            r'\bdoi:\s*10\.|10\.\d+',  # DOI patterns
            r'\bvol\.?\s*\d+|volume\s*\d+',  # Volume patterns
            r'\bpp\.?\s*\d+|pages?\s*\d+',  # Page patterns
            r'\[?\d+\]?',  # Reference numbers
        ]
        
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        
        # Consider it a reference table if it matches multiple patterns
        return pattern_matches >= 2
    
    def _parse_table_references(self, text: str) -> List[Reference]:
        """Parse references from normalized table text."""
        references = []
        
        # Split by lines and treat each line as a potential reference
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) > 20:  # Minimum length for meaningful reference
                try:
                    ref = self.parser.parse_reference(line)
                    if ref:
                        references.append(ref)
                except Exception as e:
                    logger.debug(f"Failed to parse table reference: {line[:50]}... - {str(e)}")
        
        return references