"""PDF reference extractor."""

import logging
import re
from pathlib import Path
from typing import List, Optional
import pdfplumber

from src.models import ExtractionResult, Reference
from src.extractor.base import BaseExtractor
from src.extractor.parser import ReferenceParser
from src.extractor.pdf.layout import LayoutAwareExtractor
from src.extractor.pdf.table_extractor import TableExtractor
from src.extractor.bibtex_parser import BibTeXParser

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extract references from PDF files with layout-aware extraction and fallbacks."""
    
    def __init__(self, enable_fallbacks: bool = True):
        """
        Initialize PDF extractor.
        
        Args:
            enable_fallbacks: Whether to enable fallback extractors
        """
        self.parser = ReferenceParser()
        self.layout_extractor = LayoutAwareExtractor()
        self.table_extractor = TableExtractor()
        self.bibtex_parser = BibTeXParser()
        self.enable_fallbacks = enable_fallbacks
    
    def extract(self, source: str) -> ExtractionResult:
        """
        Extract references from a PDF file using layout-aware extraction with fallbacks.
        
        Fallback order:
        1. Layout-aware extraction (primary)
        2. BibTeX parser (if BibTeX found)
        3. Table extractor (if tables found)
        
        Args:
            source: Path to PDF file
            
        Returns:
            ExtractionResult containing extracted references
        """
        result = ExtractionResult(source=source)
        pdf_path = Path(source)
        
        if not pdf_path.exists():
            result.extraction_errors.append(f"PDF file not found: {source}")
            return result
        
        if not pdf_path.suffix.lower() == '.pdf':
            result.extraction_errors.append(f"File is not a PDF: {source}")
            return result
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.debug(f"Processing PDF with {len(pdf.pages)} pages")
                
                # Primary: Layout-aware extraction
                references_text = self.layout_extractor.extract_reference_section(pdf)
                logger.debug(f"Extracted {len(references_text)} characters from reference section")
                
                # Parse references from primary extraction
                references = self._parse_references(references_text)
                logger.debug(f"Primary extraction: {len(references)} references")
                
                # Apply fallbacks if enabled and needed
                if self.enable_fallbacks:
                    references = self._apply_fallbacks(pdf, references, references_text)
                
                result.references = references
                result.total_references = len(references)
                
                logger.info(f"Extracted {len(references)} references from {pdf_path}")
                
        except Exception as e:
            result.extraction_errors.append(f"Error extracting PDF: {str(e)}")
            logger.error(f"Error extracting PDF {pdf_path}: {str(e)}")
        
        return result
    
    def _apply_fallbacks(
        self,
        pdf,
        primary_refs: List[Reference],
        full_text: str
    ) -> List[Reference]:
        """
        Apply fallback extractors to supplement primary extraction.
        
        Args:
            pdf: pdfplumber PDF object
            primary_refs: References from primary extraction
            full_text: Full extracted text
            
        Returns:
            Enhanced list of references
        """
        all_refs = list(primary_refs)
        seen_texts = {self._normalize_ref_text(ref.raw_text) for ref in primary_refs}
        
        # Fallback 1: BibTeX parser
        if self.bibtex_parser.has_bibtex(full_text):
            logger.debug("BibTeX content detected, applying BibTeX parser")
            bibtex_blocks = self.bibtex_parser.extract_bibtex_blocks(full_text)
            
            for block in bibtex_blocks:
                ref = self.bibtex_parser.parse_bibtex_entry(block)
                if ref:
                    # Add provenance metadata
                    if not ref.metadata:
                        ref.metadata = {}
                    ref.metadata['extraction_method'] = 'bibtex_fallback'
                    
                    # Check for duplicates
                    normalized = self._normalize_ref_text(ref.raw_text)
                    if normalized not in seen_texts:
                        all_refs.append(ref)
                        seen_texts.add(normalized)
            
            logger.debug(f"BibTeX fallback added {len(all_refs) - len(primary_refs)} refs")
        
        # Fallback 2: Table extractor
        if self.table_extractor.has_tables(pdf):
            logger.debug("Tables detected, applying table extractor")
            table_refs_text = self.table_extractor.extract_from_tables(pdf)
            
            for ref_text in table_refs_text:
                # Parse table-extracted reference
                ref = self.parser.parse_reference(ref_text)
                if ref:
                    # Add provenance metadata
                    if not ref.metadata:
                        ref.metadata = {}
                    ref.metadata['extraction_method'] = 'table_fallback'
                    
                    # Check for duplicates
                    normalized = self._normalize_ref_text(ref.raw_text)
                    if normalized not in seen_texts:
                        all_refs.append(ref)
                        seen_texts.add(normalized)
            
            logger.debug(f"Table fallback added {len(all_refs) - len(primary_refs) - (len(all_refs) if self.bibtex_parser.has_bibtex(full_text) else 0)} refs")
        
        return all_refs
    
    def _normalize_ref_text(self, text: str) -> str:
        """
        Normalize reference text for duplicate detection.
        
        Args:
            text: Reference text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase, remove punctuation and extra whitespace
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text[:100].strip()
    
    def _extract_text_from_pdf(self, pdf) -> str:
        """Extract all text from PDF while preserving structure."""
        text_parts = []
        
        for page_num, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
        
        return "\n".join(text_parts)
    
    def _parse_references(self, text: str) -> List[Reference]:
        """Parse reference text into structured references with filtering."""
        if not text or len(text.strip()) == 0:
            logger.debug("No reference text to parse")
            return []
        
        # Split text into individual references
        references_raw = self._split_references(text)
        logger.debug(f"Split into {len(references_raw)} raw reference candidates")
        
        # Parse and filter references
        references = []
        filtered_count = 0
        
        for idx, ref_text in enumerate(references_raw):
            try:
                # Check if this looks like a valid reference before parsing
                if not self._is_valid_reference_candidate(ref_text):
                    filtered_count += 1
                    logger.debug(f"Filtered non-reference block #{idx + 1}: {ref_text[:50]}...")
                    continue
                
                ref = self.parser.parse_reference(ref_text)
                if ref:
                    references.append(ref)
                else:
                    filtered_count += 1
                    logger.debug(f"Failed to parse reference #{idx + 1}")
            except Exception as e:
                filtered_count += 1
                logger.debug(f"Error parsing reference #{idx + 1}: {str(e)}")
        
        logger.debug(
            f"Parsed {len(references)} references, filtered {filtered_count} blocks"
        )
        
        return references
    
    def _split_references(self, text: str) -> List[str]:
        """
        Split reference text into individual references.
        
        Tries multiple splitting strategies with logging.
        """
        references = []
        split_method = None
        
        # Try numbered references [1], [2], etc.
        numbered_pattern = r'\n\s*\[\d+\]'
        matches = re.findall(numbered_pattern, text)
        if len(matches) >= 2:
            parts = re.split(numbered_pattern, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            split_method = "bracketed numbers [N]"
            logger.debug(f"Using split method: {split_method}, found {len(matches)} markers")
            return references
        
        # Try numbered references 1., 2., etc.
        numbered_pattern2 = r'\n\s*\d+\.\s+'
        matches = re.findall(numbered_pattern2, text)
        if len(matches) >= 2:
            parts = re.split(numbered_pattern2, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
            split_method = "numbered list N."
            logger.debug(f"Using split method: {split_method}, found {len(matches)} markers")
            return references
        
        # Try DOI-based splitting
        doi_pattern = r'(?=\n[^\n]*(?:doi|DOI|https?://doi\.org))'
        matches = re.findall(r'(?:doi|DOI|https?://doi\.org)', text)
        if len(matches) >= 2:
            parts = re.split(doi_pattern, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
            if len(references) >= 2:
                split_method = "DOI markers"
                logger.debug(f"Using split method: {split_method}, found {len(matches)} DOIs")
                return references
        
        # Try year-based splitting (look for patterns like "(2023)" or "2023.")
        year_pattern = r'(?=\n[^\n]*\((?:19|20)\d{2}\)|(?:19|20)\d{2}\.)'
        matches = re.findall(r'\((?:19|20)\d{2}\)|(?:19|20)\d{2}\.', text)
        if len(matches) >= 5:
            parts = re.split(year_pattern, text)
            references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]
            if len(references) >= 5:
                split_method = "year markers"
                logger.debug(f"Using split method: {split_method}, found {len(matches)} year markers")
                return references
        
        # Fallback: split by double newlines
        parts = text.split('\n\n')
        references = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]
        split_method = "double newlines"
        logger.debug(f"Using fallback split method: {split_method}, found {len(references)} blocks")
        
        return references if references else [text]
    
    def _is_valid_reference_candidate(self, text: str) -> bool:
        """
        Check if a text block looks like a valid reference.
        
        Filters out figure captions, tables, and other non-reference content.
        """
        if not text or len(text.strip()) < 15:
            logger.debug("Block too short")
            return False
        
        text_lower = text.lower()
        
        # Filter out obvious non-references
        caption_markers = ['figure', 'fig.', 'fig ', 'table', 'scheme']
        starts_with_caption = any(
            text_lower.strip().startswith(marker) for marker in caption_markers
        )
        
        if starts_with_caption:
            # Check if it has reference-like features
            has_year = re.search(r'\b(19|20)\d{2}\b', text)
            has_doi = 'doi' in text_lower or re.search(r'10\.\d{4,}', text)
            has_url = 'http' in text_lower
            
            # If it looks like a caption without reference features, reject it
            word_count = len(text.split())
            if word_count < 15 and not (has_year or has_doi or has_url):
                logger.debug(f"Rejected caption-like block: {text[:30]}...")
                return False
        
        # Check for reference-like features
        has_year = re.search(r'\b(19|20)\d{2}\b', text)
        has_doi = 'doi' in text_lower or re.search(r'10\.\d{4,}', text)
        has_authors = re.search(r'[A-Z][a-z]+,?\s+[A-Z]\.', text)
        has_url = re.search(r'https?://', text)
        
        # At least one strong indicator should be present
        if has_year or has_doi or has_authors or has_url:
            return True
        
        # If nothing looks like a reference, check word count
        # References are usually substantial
        word_count = len(text.split())
        if word_count > 8:
            return True
        
        logger.debug(f"Block lacks reference indicators: {text[:30]}...")
        return False
