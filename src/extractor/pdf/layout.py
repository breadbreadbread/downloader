"""Layout-aware PDF text extractor for accurate reference extraction."""

import logging
import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class LayoutAwareExtractor:
    """
    Extract text from PDF with layout awareness.
    
    Handles multi-column layouts, detects reference sections using font/position
    heuristics, and filters out figure/table captions.
    """
    
    def __init__(self):
        """Initialize the layout-aware extractor."""
        self.reference_headers = [
            "references",
            "bibliography",
            "cited works",
            "works cited",
            "literature cited",
            "reference list",
        ]
        self.caption_keywords = [
            "figure", "fig.", "fig ", "table", "scheme",
            "appendix", "supplementary", "supplement"
        ]
    
    def extract_reference_section(self, pdf) -> str:
        """
        Extract the reference section from a PDF with layout awareness.
        
        Args:
            pdf: pdfplumber PDF object
            
        Returns:
            Extracted reference text with proper column ordering
        """
        logger.debug("Starting layout-aware reference extraction")
        
        # Find the page where references start
        ref_start_page, ref_start_y = self._find_reference_section_start(pdf)
        
        if ref_start_page is None:
            logger.warning("Could not find reference section header, using fallback")
            return self._fallback_extraction(pdf)
        
        logger.debug(f"Reference section detected on page {ref_start_page + 1}, y={ref_start_y:.1f}")
        
        # Extract text from reference section onwards
        reference_text = []
        
        for page_num in range(ref_start_page, len(pdf.pages)):
            page = pdf.pages[page_num]
            
            # Extract words with layout information
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=False
            )
            
            if not words:
                continue
            
            # Filter words based on starting position
            if page_num == ref_start_page:
                words = [w for w in words if w['top'] >= ref_start_y]
            
            # Filter out caption-like text
            filtered_words = self._filter_caption_words(words)
            
            if not filtered_words:
                continue
            
            # Detect column layout and order text
            ordered_text = self._order_text_by_columns(filtered_words, page)
            reference_text.append(ordered_text)
        
        result = "\n\n".join(reference_text)
        logger.debug(f"Extracted {len(result)} characters from reference section")
        
        return result
    
    def _find_reference_section_start(self, pdf) -> Tuple[Optional[int], Optional[float]]:
        """
        Find the page and y-position where the reference section starts.
        
        Uses font size, weight, and text matching heuristics.
        
        Returns:
            Tuple of (page_index, y_position) or (None, None) if not found
        """
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False
            )
            
            if not words:
                continue
            
            # Group words into lines
            lines = self._group_words_into_lines(words)
            
            # Calculate average font size for the page
            avg_font_size = sum(w.get('height', 10) for w in words) / len(words)
            
            for line in lines:
                line_text = " ".join(w['text'] for w in line).strip().lower()
                
                # Check if this line looks like a reference header
                for header in self.reference_headers:
                    if header in line_text and len(line_text) < 50:
                        # Check font size - headers are often larger
                        line_font_size = max(w.get('height', 10) for w in line)
                        
                        # Header should be somewhat prominent
                        if line_font_size >= avg_font_size * 0.9:
                            # Get the y-position where references start (below the header)
                            y_pos = max(w['bottom'] for w in line)
                            logger.debug(
                                f"Found reference header '{line_text}' on page {page_num + 1}, "
                                f"font_size={line_font_size:.1f}, avg={avg_font_size:.1f}"
                            )
                            return page_num, y_pos
        
        return None, None
    
    def _group_words_into_lines(self, words: List[Dict]) -> List[List[Dict]]:
        """
        Group words into lines based on vertical position.
        
        Args:
            words: List of word dictionaries from pdfplumber
            
        Returns:
            List of lines, where each line is a list of word dictionaries
        """
        if not words:
            return []
        
        # Sort by vertical position first, then horizontal
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        lines = []
        current_line = [sorted_words[0]]
        
        for word in sorted_words[1:]:
            # If word is on roughly the same line (within 3 points)
            if abs(word['top'] - current_line[-1]['top']) < 3:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _filter_caption_words(self, words: List[Dict]) -> List[Dict]:
        """
        Filter out words that are likely part of figure/table captions.
        
        Args:
            words: List of word dictionaries
            
        Returns:
            Filtered list of words
        """
        if not words:
            return words
        
        # Group words into lines
        lines = self._group_words_into_lines(words)
        
        # Filter out caption lines
        filtered_lines = []
        for line in lines:
            line_text = " ".join(w['text'] for w in line).strip().lower()
            
            # Check if line starts with caption keywords
            starts_with_caption = any(
                line_text.startswith(keyword) for keyword in self.caption_keywords
            )
            
            # Check if line is very short (likely a caption)
            word_count = len(line_text.split())
            is_very_short = word_count < 6
            
            # Check if line has reference-like indicators
            has_year = re.search(r'\b(19|20)\d{2}\b', line_text)
            has_doi = 'doi' in line_text or '10.' in line_text
            has_numbering = re.match(r'^\s*[\[\(]?\d+[\]\)]?\.?\s', line_text)
            
            is_likely_reference = has_year or has_doi or has_numbering
            
            # Keep line if it doesn't look like a caption or looks like a reference
            if not starts_with_caption or is_likely_reference or not is_very_short:
                filtered_lines.append(line)
            else:
                logger.debug(f"Filtered caption: {line_text[:50]}")
        
        # Flatten lines back to words
        filtered_words = []
        for line in filtered_lines:
            filtered_words.extend(line)
        
        return filtered_words
    
    def _order_text_by_columns(self, words: List[Dict], page) -> str:
        """
        Order words by column layout (left-to-right, top-to-bottom within each column).
        
        Args:
            words: List of word dictionaries
            page: pdfplumber page object
            
        Returns:
            Ordered text string
        """
        if not words:
            return ""
        
        # Detect columns by clustering x-coordinates
        columns = self._detect_columns(words, page)
        
        logger.debug(f"Detected {len(columns)} columns on page")
        
        # Sort columns left-to-right
        columns = sorted(columns, key=lambda col: min(w['x0'] for w in col))
        
        # Extract text from each column top-to-bottom
        column_texts = []
        for col_words in columns:
            # Sort words top-to-bottom, then left-to-right
            sorted_words = sorted(col_words, key=lambda w: (w['top'], w['x0']))
            
            # Group into lines and merge
            lines = self._group_words_into_lines(sorted_words)
            line_texts = []
            for line in lines:
                line_text = " ".join(w['text'] for w in line)
                line_texts.append(line_text)
            
            column_texts.append("\n".join(line_texts))
        
        return "\n\n".join(column_texts)
    
    def _detect_columns(self, words: List[Dict], page) -> List[List[Dict]]:
        """
        Detect column layout by clustering x-coordinates.
        
        Supports 1-3 columns.
        
        Args:
            words: List of word dictionaries
            page: pdfplumber page object
            
        Returns:
            List of columns, each containing word dictionaries
        """
        if not words:
            return []
        
        # Get page width
        page_width = page.width
        
        # Collect x-positions (use center of each word)
        x_positions = [(w['x0'] + w['x1']) / 2 for w in words]
        
        # Try to detect number of columns by analyzing x-position distribution
        # Simple approach: check for gaps in the x-distribution
        x_sorted = sorted(set(int(x) for x in x_positions))
        
        # Find gaps larger than 1/10 of page width
        gap_threshold = page_width * 0.1
        column_boundaries = []
        
        for i in range(len(x_sorted) - 1):
            if x_sorted[i + 1] - x_sorted[i] > gap_threshold:
                boundary = (x_sorted[i] + x_sorted[i + 1]) / 2
                column_boundaries.append(boundary)
        
        # Limit to max 3 columns
        if len(column_boundaries) > 2:
            # Keep the two most prominent gaps
            column_boundaries = sorted(column_boundaries)[:2]
        
        logger.debug(f"Column boundaries: {column_boundaries}")
        
        # Assign words to columns
        if not column_boundaries:
            # Single column
            return [words]
        
        columns = [[] for _ in range(len(column_boundaries) + 1)]
        
        for word in words:
            word_x = (word['x0'] + word['x1']) / 2
            
            # Find which column this word belongs to
            col_idx = 0
            for boundary in column_boundaries:
                if word_x < boundary:
                    break
                col_idx += 1
            
            columns[col_idx].append(word)
        
        # Filter out empty columns
        columns = [col for col in columns if col]
        
        return columns
    
    def _fallback_extraction(self, pdf) -> str:
        """
        Fallback extraction method when reference section can't be detected.
        
        Returns last 30% of document text.
        """
        logger.debug("Using fallback extraction (last 30% of document)")
        
        all_text = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
        
        full_text = "\n".join(all_text)
        
        # Return last 30%
        split_point = int(len(full_text) * 0.7)
        return full_text[split_point:]
