"""Table-based reference extractor for PDFs with tabular references."""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TableExtractor:
    """
    Extract references from tables in PDF documents.
    
    Some academic papers organize references in table format.
    This extractor identifies and extracts such references.
    """
    
    def __init__(self):
        """Initialize the table extractor."""
        self.min_table_rows = 3  # Minimum rows to consider as a reference table
    
    def extract_from_tables(self, pdf) -> List[str]:
        """
        Extract reference text from tables in a PDF.
        
        Args:
            pdf: pdfplumber PDF object
            
        Returns:
            List of reference text strings extracted from tables
        """
        logger.debug("Starting table-based extraction")
        
        all_references = []
        
        for page_num, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
                
                if not tables:
                    continue
                
                logger.debug(f"Found {len(tables)} tables on page {page_num + 1}")
                
                for table_idx, table in enumerate(tables):
                    if self._is_reference_table(table):
                        logger.debug(f"Table {table_idx + 1} on page {page_num + 1} appears to be a reference table")
                        refs = self._extract_references_from_table(table)
                        all_references.extend(refs)
                        logger.debug(f"Extracted {len(refs)} references from table")
                    
            except Exception as e:
                logger.warning(f"Error extracting tables from page {page_num}: {str(e)}")
        
        logger.debug(f"Total references extracted from tables: {len(all_references)}")
        return all_references
    
    def _is_reference_table(self, table: List[List[Any]]) -> bool:
        """
        Check if a table contains references.
        
        Args:
            table: Extracted table data
            
        Returns:
            True if table appears to contain references
        """
        if not table or len(table) < self.min_table_rows:
            return False
        
        # Check if table has reference-like content
        reference_indicators = 0
        total_cells = 0
        
        for row in table[:min(10, len(table))]:  # Check first 10 rows
            for cell in row:
                if cell and isinstance(cell, str):
                    total_cells += 1
                    cell_lower = cell.lower()
                    
                    # Check for reference indicators
                    if any(indicator in cell_lower for indicator in [
                        'doi', 'http', 'author', 'journal', 'published',
                        '19', '20'  # Years
                    ]):
                        reference_indicators += 1
                    
                    # Check for year patterns
                    if re.search(r'\b(19|20)\d{2}\b', cell):
                        reference_indicators += 1
        
        # If >30% of cells have reference indicators, consider it a reference table
        if total_cells > 0 and (reference_indicators / total_cells) > 0.3:
            return True
        
        return False
    
    def _extract_references_from_table(self, table: List[List[Any]]) -> List[str]:
        """
        Extract reference strings from a table.
        
        Args:
            table: Extracted table data
            
        Returns:
            List of reference text strings
        """
        references = []
        
        for row_idx, row in enumerate(table):
            # Skip header row if present
            if row_idx == 0:
                row_text = " ".join(str(cell or "") for cell in row).lower()
                if any(header in row_text for header in ['author', 'title', 'journal', 'year', 'reference']):
                    logger.debug(f"Skipping header row: {row_text[:50]}")
                    continue
            
            # Combine cells in the row to form a reference
            ref_text = " ".join(str(cell or "") for cell in row if cell)
            
            # Only include if it looks substantial
            if len(ref_text.strip()) > 20:
                references.append(ref_text.strip())
        
        return references
    
    def has_tables(self, pdf) -> bool:
        """
        Check if PDF contains any tables.
        
        Args:
            pdf: pdfplumber PDF object
            
        Returns:
            True if PDF contains tables
        """
        for page in pdf.pages[:5]:  # Check first 5 pages
            try:
                tables = page.extract_tables()
                if tables:
                    return True
            except Exception:
                pass
        
        return False