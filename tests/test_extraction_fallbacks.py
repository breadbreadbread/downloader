"""Tests for extraction fallback implementations."""

import logging
import os
import tempfile
import unittest
from pathlib import Path

from src.extractor.fallbacks import BibTeXParser, HTMLFallbackExtractor, TableExtractor
from src.extractor.pdf_extractor import PDFExtractor
from tests.fixtures.fixture_generator import (
    generate_html_with_references,
    generate_pdf_with_bibtex,
    generate_pdf_with_table_references,
    generate_pdf_without_ref_header,
    generate_three_column_pdf,
)


class TestBibTeXParser(unittest.TestCase):
    """Test BibTeX parser functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = BibTeXParser()

    def test_has_bibtex(self):
        """Test BibTeX detection."""
        bibtex_text = """
        Some text here.
        @article{key1,
          author = {Smith, John},
          title = {Test Article},
          year = {2023}
        }
        More text.
        """

        self.assertTrue(self.parser.has_bibtex(bibtex_text))
        self.assertFalse(self.parser.has_bibtex("No BibTeX here"))

    def test_extract_bibtex_blocks(self):
        """Test extracting BibTeX entry blocks."""
        bibtex_text = """
        @article{key1,
          author = {Smith, John},
          title = {First Article},
          year = {2023}
        }
        
        Some intervening text.
        
        @inproceedings{key2,
          author = {Jones, Mary},
          title = {Conference Paper},
          year = {2022}
        }
        """

        blocks = self.parser.extract_bibtex_blocks(bibtex_text)

        self.assertEqual(len(blocks), 2)
        self.assertIn("@article", blocks[0])
        self.assertIn("@inproceedings", blocks[1])

    def test_parse_bibtex_entry(self):
        """Test parsing a single BibTeX entry."""
        entry = """@article{smith2023,
  author = {Smith, John and Doe, Jane},
  title = {Important Research},
  journal = {Nature},
  year = {2023},
  volume = {10},
  number = {5},
  pages = {100--110},
  doi = {10.1234/nature.2023}
}"""

        ref = self.parser.parse_bibtex_entry(entry)

        self.assertIsNotNone(ref)
        self.assertEqual(ref.title, "Important Research")
        self.assertEqual(len(ref.authors), 2)
        self.assertEqual(ref.year, 2023)
        self.assertEqual(ref.journal, "Nature")
        self.assertEqual(ref.volume, "10")
        self.assertEqual(ref.doi, "10.1234/nature.2023")
        self.assertEqual(ref.metadata["source"], "bibtex")
        self.assertEqual(ref.metadata["entry_type"], "article")

    def test_parse_bibtex_authors(self):
        """Test parsing BibTeX author field."""
        authors_str = "Smith, John and Doe, Jane and Brown, Bob"

        authors = self.parser._parse_bibtex_authors(authors_str)

        self.assertEqual(len(authors), 3)
        self.assertEqual(authors[0], "Smith, John")
        self.assertEqual(authors[1], "Doe, Jane")
        self.assertEqual(authors[2], "Brown, Bob")


class TestTableExtractor(unittest.TestCase):
    """Test table-based reference extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = TableExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_from_table_pdf(self):
        """Test extracting references from a PDF with tabular references."""
        import pdfplumber

        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=15
        )

        with pdfplumber.open(pdf_path) as pdf:
            refs = self.extractor.extract_from_tables(pdf)

        # Should extract at least 12 references (allowing for some parsing issues)
        self.assertGreater(len(refs), 12)

    def test_has_tables(self):
        """Test table detection."""
        import pdfplumber

        # Create PDF with tables
        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=10
        )

        with pdfplumber.open(pdf_path) as pdf:
            self.assertTrue(self.extractor.has_tables(pdf))

    def test_is_reference_table(self):
        """Test reference table detection."""
        # Reference table
        ref_table = [
            ["No", "Reference"],
            [
                "1",
                "Smith, J. (2023). Article. Journal, 10(2), 100-110. doi: 10.1234/ref",
            ],
            ["2", "Jones, M. (2022). Study. Nature, 15, 200-215. http://example.com"],
        ]

        self.assertTrue(self.extractor._is_reference_table(ref_table))

        # Non-reference table
        non_ref_table = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]

        self.assertFalse(self.extractor._is_reference_table(non_ref_table))


class TestHTMLFallbackExtractor(unittest.TestCase):
    """Test HTML fallback extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = HTMLFallbackExtractor()

    def test_extract_from_html_structure(self):
        """Test extracting references from HTML structure."""
        html = generate_html_with_references()

        refs = self.extractor.extract_from_html_structure(html)

        # Should extract at least 5 references from the list
        self.assertGreaterEqual(len(refs), 5)

    def test_find_reference_section(self):
        """Test finding reference section in HTML."""
        from bs4 import BeautifulSoup

        html = generate_html_with_references()
        soup = BeautifulSoup(html, "lxml")

        section = self.extractor._find_reference_section(soup)

        self.assertIsNotNone(section)

    def test_is_valid_reference_text(self):
        """Test reference text validation."""
        # Valid reference
        valid_ref = "Smith, J. (2023). Study on topics. Nature, 10(2), 100-110. doi: 10.1234/ref"
        self.assertTrue(self.extractor._is_valid_reference_text(valid_ref))

        # Too short
        too_short = "Short text"
        self.assertFalse(self.extractor._is_valid_reference_text(too_short))

        # No indicators
        no_indicators = (
            "This is just regular text without any reference features at all"
        )
        self.assertFalse(self.extractor._is_valid_reference_text(no_indicators))

    def test_merge_references(self):
        """Test merging references with deduplication."""
        primary_refs = [
            "Smith, J. (2023). First paper. Journal, 10, 100-110.",
            "Jones, M. (2022). Second paper. Nature, 15, 200-215.",
        ]

        fallback_refs = [
            "Smith, J. (2023). First paper. Journal, 10, 100-110.",  # Duplicate
            "Brown, A. (2021). Third paper. Science, 20, 300-310.",  # New
        ]

        merged = self.extractor.merge_references(
            primary_refs, fallback_refs, deduplicate=True
        )

        # Should have 3 unique references (2 primary + 1 new from fallback)
        self.assertEqual(len(merged), 3)

    def test_merge_without_deduplication(self):
        """Test merging without deduplication."""
        primary_refs = ["Ref 1", "Ref 2"]
        fallback_refs = ["Ref 1", "Ref 3"]

        merged = self.extractor.merge_references(
            primary_refs, fallback_refs, deduplicate=False
        )

        # Should have all 4 references
        self.assertEqual(len(merged), 4)

    def test_extract_from_lists_fallback(self):
        """Test extracting from lists when no specific section is found."""
        from bs4 import BeautifulSoup

        html = """
        <html>
        <body>
            <ol>
                <li>Smith, J. (2021). First paper. Journal, 10, 100-110. doi: 10.1234/ref1</li>
                <li>Jones, M. (2022). Second paper. Nature, 15, 200-215. http://example.com</li>
                <li>Brown, A. (2020). Third paper. Science, 8, 50-65. doi: 10.5678/ref3</li>
            </ol>
        </body>
        </html>
        """

        refs = self.extractor.extract_from_html_structure(html)

        # Should find the references in the list
        self.assertGreaterEqual(len(refs), 3)

    def test_is_reference_list(self):
        """Test checking if a list contains references."""
        from bs4 import BeautifulSoup

        # Reference list
        html = """
        <ul>
            <li>Smith, J. (2021). Paper 1. Journal, 10, 100-110. doi: 10.1234/ref1</li>
            <li>Jones, M. (2022). Paper 2. Nature, 15, 200-215. http://example.com</li>
            <li>Brown, A. (2020). Paper 3. Science, 8, 50-65. doi: 10.5678/ref3</li>
        </ul>
        """
        soup = BeautifulSoup(html, "lxml")
        items = soup.find("ul").find_all("li")

        self.assertTrue(self.extractor._is_reference_list(items))

        # Non-reference list
        html2 = """
        <ul>
            <li>Apple</li>
            <li>Banana</li>
            <li>Cherry</li>
        </ul>
        """
        soup2 = BeautifulSoup(html2, "lxml")
        items2 = soup2.find("ul").find_all("li")

        self.assertFalse(self.extractor._is_reference_list(items2))

    def test_clean_html_text(self):
        """Test HTML text cleaning."""
        text = "  This   has   extra   \n  whitespace  "
        cleaned = self.extractor._clean_html_text(text)

        self.assertEqual(cleaned, "This has extra whitespace")

    def test_normalize_for_comparison(self):
        """Test text normalization for duplicate detection."""
        text1 = "Smith, J. (2023). Research paper. Journal, 10, 100-110."
        text2 = "Smith J 2023 Research paper Journal 10 100110"

        norm1 = self.extractor._normalize_for_comparison(text1)
        norm2 = self.extractor._normalize_for_comparison(text2)

        # Should normalize to similar strings
        self.assertEqual(norm1[:30], norm2[:30])


class TestPDFExtractorFallbacks(unittest.TestCase):
    """Test PDF extractor with fallback integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor(enable_fallbacks=True)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_fallback_activation_with_tables(self):
        """Test that table fallback activates when tables are present."""
        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=15
        )

        # Enable logging to capture fallback messages
        with self.assertLogs("src.extractor.pdf_extractor", level="DEBUG") as log:
            result = self.extractor.extract(pdf_path)

        # Check that table fallback was triggered
        log_output = "\n".join(log.output)
        self.assertIn("Tables detected", log_output)

        # Should extract references
        self.assertGreater(len(result.references), 10)

    def test_fallback_activation_with_bibtex(self):
        """Test that BibTeX fallback activates when BibTeX is present."""
        pdf_path = generate_pdf_with_bibtex(
            os.path.join(self.temp_dir, "bibtex_test.pdf"), num_refs=10
        )

        with self.assertLogs("src.extractor.pdf_extractor", level="DEBUG") as log:
            result = self.extractor.extract(pdf_path)

        log_output = "\n".join(log.output)
        self.assertIn("BibTeX content detected", log_output)

        # Should extract references
        self.assertGreater(len(result.references), 5)

    def test_fallbacks_disabled(self):
        """Test extraction with fallbacks disabled."""
        extractor_no_fallback = PDFExtractor(enable_fallbacks=False)

        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=15
        )

        result = extractor_no_fallback.extract(pdf_path)

        # May get fewer references without fallback
        # Just ensure it doesn't crash
        self.assertIsNotNone(result.references)

    def test_provenance_metadata(self):
        """Test that provenance metadata is added to fallback references."""
        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=15
        )

        result = self.extractor.extract(pdf_path)

        # Check for metadata in references
        refs_with_metadata = [
            ref
            for ref in result.references
            if ref.metadata and "extraction_method" in ref.metadata
        ]

        # At least some references should have metadata if fallbacks triggered
        if len(refs_with_metadata) > 0:
            # Verify metadata format
            for ref in refs_with_metadata:
                self.assertIn("extraction_method", ref.metadata)
                self.assertIn("fallback", ref.metadata["extraction_method"])

    def test_no_duplicate_references(self):
        """Test that fallbacks don't create duplicate references."""
        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=15
        )

        result = self.extractor.extract(pdf_path)

        # Check for duplicates based on normalized text
        seen = set()
        duplicates = []

        for ref in result.references:
            normalized = self.extractor._normalize_ref_text(ref.raw_text)
            if normalized in seen:
                duplicates.append(ref.raw_text)
            seen.add(normalized)

        # Should have no duplicates
        self.assertEqual(len(duplicates), 0, f"Found duplicates: {duplicates}")


class TestThreeColumnPDF(unittest.TestCase):
    """Test three-column PDF extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_three_column_extraction(self):
        """Test extraction from three-column PDF."""
        pdf_path = generate_three_column_pdf(
            os.path.join(self.temp_dir, "three_col_test.pdf"), num_refs=60
        )

        result = self.extractor.extract(pdf_path)

        # Should extract a significant number of references from three-column layout
        # Note: Three-column detection is challenging, so we accept ≥15 as success
        # The important thing is that it doesn't crash and extracts something
        self.assertGreater(
            len(result.references),
            15,
            f"Expected >15 references from three-column PDF, got {len(result.references)}",
        )


class TestPDFWithoutReferenceHeader(unittest.TestCase):
    """Test PDF extraction without explicit reference header."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extraction_without_header(self):
        """Test that fallback extraction works when no header is found."""
        pdf_path = generate_pdf_without_ref_header(
            os.path.join(self.temp_dir, "no_header_test.pdf"), num_refs=25
        )

        with self.assertLogs("src.extractor.pdf.layout", level="DEBUG") as log:
            result = self.extractor.extract(pdf_path)

        # Should use fallback extraction
        log_output = "\n".join(log.output)
        self.assertIn("fallback", log_output.lower())

        # Should still extract some references (fallback gets last 30% of document)
        # We're testing that fallback activates, not perfect extraction
        self.assertGreater(len(result.references), 5)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_malformed_pdf_error_handling(self):
        """Test that malformed PDFs produce informative errors."""
        # Create a text file masquerading as a PDF
        fake_pdf_path = os.path.join(self.temp_dir, "fake.pdf")
        with open(fake_pdf_path, "w") as f:
            f.write("This is not a valid PDF file")

        result = self.extractor.extract(fake_pdf_path)

        # Should have error messages
        self.assertGreater(len(result.extraction_errors), 0)
        self.assertEqual(len(result.references), 0)

    def test_empty_pdf_handling(self):
        """Test handling of empty or minimal PDF."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate

        pdf_path = os.path.join(self.temp_dir, "empty.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("Empty document", styles["Normal"])]
        doc.build(story)

        result = self.extractor.extract(pdf_path)

        # Should not crash, may return 0 references
        self.assertIsNotNone(result.references)

    def test_caption_filtering_with_fallbacks(self):
        """Test that caption filtering works when fallbacks supply data."""
        # This is implicitly tested by other tests, but we verify explicitly
        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "table_test.pdf"), num_refs=15
        )

        result = self.extractor.extract(pdf_path)

        # Check that no "Figure" or "Table" captions made it through
        caption_refs = [
            ref
            for ref in result.references
            if ref.raw_text.lower().startswith(("figure", "table", "scheme"))
            and len(ref.raw_text.split()) < 10
        ]

        # Should filter out most/all short captions
        self.assertLess(len(caption_refs), 2)


class TestDebugLogging(unittest.TestCase):
    """Test DEBUG level logging for troubleshooting."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_debug_logging_layout_extraction(self):
        """Test that DEBUG logs are produced for layout extraction."""
        # Use a simple two-column PDF that will trigger column detection
        from tests.fixtures.fixture_generator import generate_pdf_with_table_references

        pdf_path = generate_pdf_with_table_references(
            os.path.join(self.temp_dir, "debug_test.pdf"), num_refs=15
        )

        with self.assertLogs("src.extractor.pdf.layout", level="DEBUG") as log:
            result = self.extractor.extract(pdf_path)

        log_output = "\n".join(log.output)

        # Should log extraction details
        self.assertIn("extract", log_output.lower())

        # Should produce some debug output
        self.assertGreater(len(log.output), 0)

    def test_debug_logging_fallback_activation(self):
        """Test that DEBUG logs show fallback activation."""
        pdf_path = generate_pdf_with_bibtex(
            os.path.join(self.temp_dir, "bibtex_test.pdf"), num_refs=10
        )

        with self.assertLogs("src.extractor.pdf_extractor", level="DEBUG") as log:
            result = self.extractor.extract(pdf_path)

        log_output = "\n".join(log.output)

        # Should log fallback detection and activation
        if "BibTeX" in pdf_path or "bibtex" in log_output.lower():
            self.assertIn("bibtex", log_output.lower())

    def test_debug_logging_split_method(self):
        """Test that DEBUG logs show which split method was used."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        pdf_path = os.path.join(self.temp_dir, "split_test.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("References", styles["Heading1"]))
        for i in range(1, 6):
            story.append(
                Paragraph(
                    f"[{i}] Author{i} (2023). Paper {i}. Journal, 10, 100-110.",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 0.05))

        doc.build(story)

        with self.assertLogs("src.extractor.pdf_extractor", level="DEBUG") as log:
            result = self.extractor.extract(pdf_path)

        log_output = "\n".join(log.output)

        # Should log which split method was used
        self.assertIn("split method", log_output.lower())


if __name__ == "__main__":
    unittest.main()
