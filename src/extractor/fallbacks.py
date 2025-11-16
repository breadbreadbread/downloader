"""Extraction fallback strategies for handling edge cases."""

import logging
import re
from typing import List, Optional, Dict, Any, Tuple
import pdfplumber
from bs4 import BeautifulSoup

from src.models import Reference, ExtractionResult
from src.extractor.parser import ReferenceParser
from src.extractor.pdf.table_extractor import TableExtractor
from src.extractor.bibtex_parser import BibTeXParser
from src.extractor.html_fallback import HTMLFallbackExtractor
from src.config import settings

logger = logging.getLogger(__name__)


class ExtractionFallbackManager:
    """Manages fallback extraction strategies for edge cases."""
    
    def __init__(self):
        self.parser = ReferenceParser()
        self.table_extractor = TableExtractor()
        self.bibtex_parser = BibTeXParser()
        self.html_extractor = HTMLFallbackExtractor()
        
        # Configuration thresholds from settings
        self.min_reference_threshold = settings.FALLBACK_MIN_REFERENCE_THRESHOLD
        self.enable_table_fallback = settings.ENABLE_TABLE_FALLBACK
        self.enable_bibtex_fallback = settings.ENABLE_BIBTEX_FALLBACK
        self.enable_html_structure_fallback = settings.ENABLE_HTML_STRUCTURE_FALLBACK
    
    def apply_fallbacks(
        self, 
        result: ExtractionResult, 
        source_text: str, 
        source_type: str,
        pdf_object: Any = None,
        html_content: Optional[str] = None
    ) -> ExtractionResult:
        """
        Apply fallback strategies to improve extraction results.
        
        Args:
            result: Current extraction result
            source_text: Raw text content
            source_type: 'pdf' or 'web'
            pdf_object: pdfplumber PDF object (for PDF sources)
            html_content: Raw HTML content (for web sources)
            
        Returns:
            Enhanced ExtractionResult with additional references
        """
        if not self.should_trigger_fallbacks(result):
            return result
        
        logger.info(f"Applying fallback strategies for {source_type} source")
        fallback_results = []
        existing_refs_set = self._create_reference_fingerprint_set(result.references)
        
        # Apply table-based fallback (PDF only)
        if source_type == 'pdf' and self.enable_table_fallback and pdf_object:
            table_refs = self.table_extractor.extract_from_pdf(pdf_object)
            if table_refs:
                new_refs = self._deduplicate_references(table_refs, existing_refs_set)
                if new_refs:
                    fallback_results.extend(new_refs)
                    existing_refs_set.update(self._create_reference_fingerprint_set(new_refs))
                    logger.info(f"Table fallback extracted {len(new_refs)} additional references")
                else:
                    result.extraction_errors.append("Table fallback: No new unique references found")
            else:
                result.extraction_errors.append("Table fallback: No reference tables detected")
        
        # Apply BibTeX fallback (both PDF and web)
        if self.enable_bibtex_fallback:
            bibtex_refs = self.bibtex_parser.extract_from_text(source_text)
            if bibtex_refs:
                new_refs = self._deduplicate_references(bibtex_refs, existing_refs_set)
                if new_refs:
                    fallback_results.extend(new_refs)
                    existing_refs_set.update(self._create_reference_fingerprint_set(new_refs))
                    logger.info(f"BibTeX fallback extracted {len(new_refs)} additional references")
                else:
                    result.extraction_errors.append("BibTeX fallback: No new unique references found")
            else:
                result.extraction_errors.append("BibTeX fallback: No BibTeX blocks detected")
        
        # Apply HTML structure fallback (web only)
        if source_type == 'web' and self.enable_html_structure_fallback and html_content:
            html_refs = self.html_extractor.extract_from_html(html_content)
            if html_refs:
                new_refs = self._deduplicate_references(html_refs, existing_refs_set)
                if new_refs:
                    fallback_results.extend(new_refs)
                    existing_refs_set.update(self._create_reference_fingerprint_set(new_refs))
                    logger.info(f"HTML structure fallback extracted {len(new_refs)} additional references")
                else:
                    result.extraction_errors.append("HTML structure fallback: No structured citation elements found")
            else:
                result.extraction_errors.append("HTML structure fallback: No structured citation elements found")
        
        # Merge fallback results with original
        if fallback_results:
            result.references.extend(fallback_results)
            result.total_references = len(result.references)
            logger.info(f"Fallback strategies added {len(fallback_results)} references (total: {result.total_references})")
        else:
            result.extraction_errors.append("All fallback strategies failed to extract new references")
        
        return result
    
    def apply_fallbacks(
        self, 
        result: ExtractionResult, 
        source_text: str, 
        source_type: str,
        pdf_object: Any = None,
        html_content: Optional[str] = None
    ) -> ExtractionResult:
        """
        Apply fallback strategies to improve extraction results.
        
        Args:
            result: Current extraction result
            source_text: Raw text content
            source_type: 'pdf' or 'web'
            pdf_object: pdfplumber PDF object (for PDF fallbacks)
            html_content: Raw HTML content (for web fallbacks)
            
        Returns:
            Enhanced ExtractionResult with fallback references
        """
        if not self.should_trigger_fallbacks(result):
            return result
        
        logger.info(f"Applying fallback strategies for {source_type} source")
        
        fallback_results = []
        existing_refs_set = self._create_reference_fingerprint_set(result.references)
        
        # Apply table-based fallback (PDF only)
        if source_type == 'pdf' and self.enable_table_fallback and pdf_object:
            table_refs = self._extract_from_tables(pdf_object)
            if table_refs:
                new_refs = self._deduplicate_references(table_refs, existing_refs_set)
                if new_refs:
                    fallback_results.extend(new_refs)
                    existing_refs_set.update(self._create_reference_fingerprint_set(new_refs))
                    logger.info(f"Table fallback extracted {len(new_refs)} additional references")
                else:
                    result.extraction_errors.append("Table fallback: No new unique references found")
            else:
                result.extraction_errors.append("Table fallback: No reference tables detected")
        
        # Apply BibTeX fallback (both PDF and web)
        if self.enable_bibtex_fallback:
            bibtex_refs = self._extract_from_bibtex(source_text)
            if bibtex_refs:
                new_refs = self._deduplicate_references(bibtex_refs, existing_refs_set)
                if new_refs:
                    fallback_results.extend(new_refs)
                    existing_refs_set.update(self._create_reference_fingerprint_set(new_refs))
                    logger.info(f"BibTeX fallback extracted {len(new_refs)} additional references")
                else:
                    result.extraction_errors.append("BibTeX fallback: No new unique references found")
            else:
                result.extraction_errors.append("BibTeX fallback: No BibTeX blocks detected")
        
        # Apply HTML structure fallback (web only)
        if source_type == 'web' and self.enable_html_structure_fallback and html_content:
            html_refs = self._extract_from_html_structure(html_content)
            if html_refs:
                new_refs = self._deduplicate_references(html_refs, existing_refs_set)
                if new_refs:
                    fallback_results.extend(new_refs)
                    existing_refs_set.update(self._create_reference_fingerprint_set(new_refs))
                    logger.info(f"HTML structure fallback extracted {len(new_refs)} additional references")
                else:
                    result.extraction_errors.append("HTML structure fallback: No new unique references found")
            else:
                result.extraction_errors.append("HTML structure fallback: No structured citation elements found")
        
        # Merge fallback results with original
        if fallback_results:
            result.references.extend(fallback_results)
            result.total_references = len(result.references)
            logger.info(f"Fallback strategies added {len(fallback_results)} references (total: {result.total_references})")
        else:
            result.extraction_errors.append("All fallback strategies failed to extract new references")
        
        return result
    
    def _extract_from_tables(self, pdf_object) -> List[Reference]:
        """Extract references from tables in PDF."""
        references = []
        
        try:
            for page_num, page in enumerate(pdf_object.pages):
                try:
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if not table:
                            continue
                        
                        # Flatten table cells and look for reference patterns
                        table_text = self._normalize_table_cells(table)
                        
                        if self._looks_like_reference_table(table_text):
                            table_refs = self._parse_table_references(table_text)
                            references.extend(table_refs)
                            
                except Exception as e:
                    logger.warning(f"Error extracting tables from page {page_num}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in table fallback extraction: {str(e)}")
        
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
        patterns = [
            r'\b\d{4}\b',  # Years
            r'\bdoi:\s*10\.',  # DOI patterns
            r'\bvol\.?\s*\d+',  # Volume patterns
            r'\bpp\.?\s*\d+',  # Page patterns
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
            if len(line) > 20:  # Minimum length for a meaningful reference
                try:
                    ref = self.parser.parse_reference(line)
                    if ref:
                        references.append(ref)
                except Exception as e:
                    logger.debug(f"Failed to parse table reference: {line[:50]}... - {str(e)}")
        
        return references
    
    def _extract_from_bibtex(self, text: str) -> List[Reference]:
        """Extract references from embedded BibTeX blocks."""
        references = []
        
        # BibTeX entry patterns - improved to handle multi-line entries
        bibtex_pattern = r'@[a-zA-Z]+\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        
        try:
            matches = re.findall(bibtex_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for bibtex_entry in matches:
                try:
                    ref = self._parse_bibtex_entry(bibtex_entry)
                    if ref:
                        references.append(ref)
                except Exception as e:
                    logger.debug(f"Failed to parse BibTeX entry: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in BibTeX fallback extraction: {str(e)}")
        
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
            # Find all key = value pairs
            field_pattern = r'(\w+)\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
            matches = re.findall(field_pattern, bibtex_text)
            
            for key, value in matches:
                fields[key.lower()] = value.strip()
            
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
            logger.debug(f"Error parsing BibTeX entry: {str(e)}")
            return None
    
    def _extract_from_html_structure(self, html_content: str) -> List[Reference]:
        """Extract references from HTML structural elements."""
        references = []
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Look for ordered lists, unordered lists, and citation elements
            selectors = [
                'ol li',           # Ordered list items
                'ul li',           # Unordered list items  
                'cite',            # Citation elements
                '.reference',      # Elements with reference class
                '.citation',       # Elements with citation class
                '[id*="ref"]',     # Elements with ref in id
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
                        except Exception as e:
                            logger.debug(f"Failed to parse HTML reference: {text[:50]}... - {str(e)}")
                
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in HTML structure fallback extraction: {str(e)}")
        
        return references
    
    def _looks_like_reference(self, text: str) -> bool:
        """Heuristically determine if text looks like a reference."""
        if not text or len(text.strip()) < 20:
            return False
        
        # Look for reference indicators
        patterns = [
            r'\b\d{4}\b',  # Years
            r'\bdoi:\s*10\.|10\.\d+',  # DOI patterns
            r'\bvol\.?\s*\d+|volume\s*\d+|\b\d+\(\d+\)',  # Volume patterns including 15(3)
            r'\bpp\.?\s*\d+|pages?\s*\d+|\d+-\d+',  # Page patterns including ranges
            r'\b(ed|eds|editors?)\.?\b',  # Editor indicators
            r'\b(in|proc|conference|journal|university|press)\b',  # Publication venues
        ]
        
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        return pattern_matches >= 2
    
    def _create_reference_fingerprint_set(self, references: List[Reference]) -> set:
        """Create a set of reference fingerprints for deduplication."""
        fingerprints = set()
        
        for ref in references:
            # Create fingerprint based on DOI, title+year, or raw text
            if ref.doi:
                fingerprints.add(f"doi:{ref.doi.lower()}")
            elif ref.title and ref.year:
                title_fingerprint = re.sub(r'\s+', ' ', ref.title.lower().strip())
                fingerprints.add(f"title_year:{title_fingerprint}_{ref.year}")
            else:
                # Fallback to raw text fingerprint
                raw_fingerprint = re.sub(r'\s+', ' ', ref.raw_text.lower().strip()[:100])
                fingerprints.add(f"raw:{raw_fingerprint}")
        
        return fingerprints
    
    def _deduplicate_references(
        self, 
        new_references: List[Reference], 
        existing_fingerprints: set
    ) -> List[Reference]:
        """Remove duplicate references based on fingerprints."""
        unique_refs = []
        
        for ref in new_references:
            # Create fingerprint for this reference
            if ref.doi:
                fingerprint = f"doi:{ref.doi.lower()}"
            elif ref.title and ref.year:
                title_fingerprint = re.sub(r'\s+', ' ', ref.title.lower().strip())
                fingerprint = f"title_year:{title_fingerprint}_{ref.year}"
            else:
                raw_fingerprint = re.sub(r'\s+', ' ', ref.raw_text.lower().strip()[:100])
                fingerprint = f"raw:{raw_fingerprint}"
            
            # Check if this reference already exists
            if fingerprint not in existing_fingerprints:
                unique_refs.append(ref)
                existing_fingerprints.add(fingerprint)
        
        return unique_refs