"""HTML structure-based reference extraction."""

import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class HTMLFallbackExtractor:
    """
    Fallback extractor for HTML-only references.

    Used when standard text extraction fails or when references
    are embedded in HTML structure (lists, divs, etc.).
    """

    def __init__(self):
        """Initialize the HTML fallback extractor."""
        self.reference_list_tags = ["ol", "ul", "div"]
        self.reference_item_tags = ["li", "p", "div"]

    def extract_from_html_structure(self, html: str) -> List[str]:
        """
        Extract references from HTML structure.

        Args:
            html: HTML content

        Returns:
            List of Reference objects
        """
        logger.debug("Starting HTML structure-based extraction")

        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        references = []

        # Try to find reference section by common IDs/classes
        ref_section = self._find_reference_section(soup)

        if ref_section:
            logger.debug("Found reference section in HTML")
            references = self._extract_from_section(ref_section)
        else:
            logger.debug("No specific reference section found, using fallback")
            references = self._extract_from_lists(soup)

        logger.debug(f"Extracted {len(references)} references from HTML structure")
        return references

    def _find_reference_section(self, soup: BeautifulSoup) -> Optional[Tag]:
        """
        Find the reference section in HTML by ID or class.

        Args:
            soup: BeautifulSoup object

        Returns:
            Reference section tag or None
        """
        # Common reference section identifiers
        ref_identifiers = [
            "references",
            "reference",
            "bibliography",
            "cited-works",
            "works-cited",
            "citations",
            "refs",
        ]

        # Try to find by ID
        for identifier in ref_identifiers:
            section = soup.find(id=re.compile(identifier, re.IGNORECASE))
            if section:
                return section

        # Try to find by class
        for identifier in ref_identifiers:
            section = soup.find(class_=re.compile(identifier, re.IGNORECASE))
            if section:
                return section

        # Try to find by heading text
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            if heading.get_text() and any(
                ref_word in heading.get_text().lower()
                for ref_word in ["reference", "bibliography", "cited work"]
            ):
                # Return the parent section
                if heading.parent and heading.parent.name in ["section", "div"]:
                    return heading.parent

                # Find the next ol/ul after the heading
                next_list = heading.find_next(["ol", "ul"])
                if next_list:
                    return next_list

                # Return next sibling as fallback
                if heading.find_next_sibling():
                    return heading.find_next_sibling()

        return None

    def _extract_from_section(self, section: Tag) -> List[str]:
        """
        Extract references from a specific HTML section.

        Args:
            section: BeautifulSoup tag containing references

        Returns:
            List of reference text strings
        """
        references = []

        # If section is a list itself, extract from it
        if section.name in ["ol", "ul"]:
            for item in section.find_all("li"):
                text = self._clean_html_text(item.get_text())
                if self._is_valid_reference_text(text):
                    references.append(text)
            return references

        # Try lists first (ol, ul)
        for list_tag in section.find_all(["ol", "ul"]):
            for item in list_tag.find_all("li"):
                text = self._clean_html_text(item.get_text())
                if self._is_valid_reference_text(text):
                    references.append(text)

        # If section is a heading, look for lists after it
        if not references and section.name in ["h1", "h2", "h3", "h4"]:
            next_list = section.find_next(["ol", "ul"])
            if next_list:
                for item in next_list.find_all("li"):
                    text = self._clean_html_text(item.get_text())
                    if self._is_valid_reference_text(text):
                        references.append(text)

        # If no list items found, try paragraphs or divs
        if not references:
            for item_tag in section.find_all(["p", "div"]):
                text = self._clean_html_text(item.get_text())
                if self._is_valid_reference_text(text):
                    references.append(text)

        return references

    def _extract_from_lists(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract references from lists in the document.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of reference text strings
        """
        references = []

        # Find all lists
        for list_tag in soup.find_all(["ol", "ul"]):
            items = list_tag.find_all("li")

            # Check if this list contains references
            if self._is_reference_list(items):
                for item in items:
                    text = self._clean_html_text(item.get_text())
                    if self._is_valid_reference_text(text):
                        references.append(text)

        return references

    def _is_reference_list(self, items: List[Tag]) -> bool:
        """
        Check if a list of items appears to be a reference list.

        Args:
            items: List of HTML tags

        Returns:
            True if list appears to contain references
        """
        if not items or len(items) < 3:
            return False

        # Check first few items for reference-like content
        reference_indicators = 0

        for item in items[: min(5, len(items))]:
            text = item.get_text().lower()

            # Look for reference indicators
            if any(
                indicator in text
                for indicator in ["doi", "http", "et al", "vol", "pp."]
            ):
                reference_indicators += 1

            # Check for years
            if re.search(r"\b(19|20)\d{2}\b", text):
                reference_indicators += 1

        # If >60% of checked items have indicators, it's likely a reference list
        return (reference_indicators / min(5, len(items))) > 0.6

    def _is_valid_reference_text(self, text: str) -> bool:
        """
        Check if text looks like a valid reference.

        Args:
            text: Text to check

        Returns:
            True if text appears to be a reference
        """
        if not text or len(text.strip()) < 20:
            return False

        text_lower = text.lower()

        # Check for reference indicators
        has_year = re.search(r"\b(19|20)\d{2}\b", text)
        has_doi = "doi" in text_lower or re.search(r"10\.\d{4,}", text)
        has_url = "http" in text_lower
        has_authors = re.search(r"[A-Z][a-z]+,?\s+[A-Z]\.", text)

        # At least one indicator should be present
        return bool(has_year or has_doi or has_url or has_authors)

    def _clean_html_text(self, text: str) -> str:
        """
        Clean extracted HTML text.

        Args:
            text: Raw text from HTML

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def merge_references(
        self,
        primary_refs: List[str],
        fallback_refs: List[str],
        deduplicate: bool = True,
    ) -> List[str]:
        """
        Merge references from primary and fallback sources.

        Args:
            primary_refs: References from primary extraction
            fallback_refs: References from fallback extraction
            deduplicate: Whether to remove duplicates

        Returns:
            Merged list of references
        """
        logger.debug(
            f"Merging {len(primary_refs)} primary refs with "
            f"{len(fallback_refs)} fallback refs"
        )

        all_refs = list(primary_refs)

        if deduplicate:
            # Use normalized text for comparison
            seen = set()
            for ref in all_refs:
                normalized = self._normalize_for_comparison(ref)
                seen.add(normalized)

            # Add fallback refs that aren't duplicates
            added = 0
            for ref in fallback_refs:
                normalized = self._normalize_for_comparison(ref)
                if normalized not in seen:
                    all_refs.append(ref)
                    seen.add(normalized)
                    added += 1

            logger.debug(f"Added {added} unique references from fallback")
        else:
            all_refs.extend(fallback_refs)

        return all_refs

    def _normalize_for_comparison(self, text: str) -> str:
        """
        Normalize text for duplicate comparison.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and extra whitespace
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)

        # Take first 100 characters for comparison
        return text[:100].strip()
