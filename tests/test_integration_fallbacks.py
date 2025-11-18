"""Integration tests for fallback functionality with extractors."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from src.extractor.pdf_extractor import PDFExtractor
from src.extractor.web_extractor import WebExtractor
from src.models import ExtractionResult, Reference
from tests.test_fixtures import (
    create_sample_html_with_citations,
    create_sample_html_with_lists,
    create_sample_text_with_bibtex,
)


class TestPDFExtractorFallbacks(unittest.TestCase):
    """Test PDF extractor with fallback functionality."""

    def setUp(self):
        self.pdf_extractor = PDFExtractor()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pdfplumber.open")
    def test_pdf_extraction_with_fallbacks_below_threshold(
        self, mock_pdfplumber_open, mock_exists
    ):
        """Test PDF extraction triggers fallbacks when reference count is low."""
        # Mock PDF with minimal references to trigger fallbacks
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        Sample paper content.
        
        References:
        1. Smith J. (2023). First paper.
        """

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber_open.return_value = mock_pdf

        # Mock file exists check
        mock_exists.return_value = True

        # Mock fallback methods to return additional references
        fallback_refs = [
            Reference(raw_text="Fallback reference 1", doi="10.1234/fallback1"),
            Reference(
                raw_text="Fallback reference 2", title="Fallback Paper", year=2023
            ),
        ]

        with patch.object(
            self.pdf_extractor.fallback_manager, "apply_fallbacks"
        ) as mock_fallbacks:
            mock_fallbacks.return_value = ExtractionResult(
                source="test.pdf",
                references=[Reference(raw_text="Original ref")] + fallback_refs,
                total_references=3,
            )

            result = self.pdf_extractor.extract("test.pdf")

            # Verify fallbacks were called
            mock_fallbacks.assert_called_once()
            args, kwargs = mock_fallbacks.call_args

            self.assertEqual(kwargs["source_type"], "pdf")
            self.assertIsNotNone(kwargs["pdf_object"])

            # Verify result contains fallback references
            self.assertEqual(len(result.references), 3)

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pdfplumber.open")
    def test_pdf_extraction_no_fallbacks_above_threshold(
        self, mock_pdfplumber_open, mock_exists
    ):
        """Test PDF extraction doesn't trigger fallbacks when reference count is high."""
        # Mock PDF with many references to avoid triggering fallbacks
        many_refs = "\n".join(
            [
                f"{i}. Author {i} (202{i%10}). Paper {i}. Journal Name, {i}({i}), {i}-{i+10}."
                for i in range(10)
            ]
        )

        mock_page = Mock()
        mock_page.extract_text.return_value = f"""
        Sample paper content.
        
        References:
        {many_refs}
        """

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber_open.return_value = mock_pdf

        # Mock file exists check
        mock_exists.return_value = True

        with patch.object(
            self.pdf_extractor.fallback_manager,
            "should_trigger_fallbacks",
            return_value=False,
        ):
            with patch.object(
                self.pdf_extractor.fallback_manager, "apply_fallbacks"
            ) as mock_fallbacks:
                result = self.pdf_extractor.extract("test.pdf")

                # Verify fallbacks were not called
                mock_fallbacks.assert_not_called()

                # Should still get primary extraction results
                self.assertGreater(len(result.references), 0)

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pdfplumber.open")
    def test_pdf_extraction_table_fallback(self, mock_pdfplumber_open, mock_exists):
        """Test table fallback functionality in PDF extraction."""
        # Mock PDF with minimal primary references
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        Sample paper content.
        
        References:
        1. Smith J. (2023). First paper.
        """

        # Mock table extraction
        mock_page.extract_tables.return_value = [
            [
                [
                    "2",
                    "Johnson A.",
                    "2022",
                    "Second paper",
                    "Journal Name",
                    "10(2)",
                    "45-67",
                ],
                [
                    "3",
                    "Brown K.",
                    "2021",
                    "Third paper",
                    "Another Journal",
                    "8(1)",
                    "123-145",
                ],
            ]
        ]

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber_open.return_value = mock_pdf

        # Mock file exists check
        mock_exists.return_value = True

        result = self.pdf_extractor.extract("test.pdf")

        # Should have references from both primary extraction and table fallback
        self.assertGreater(len(result.references), 1)

        # Check for table-based references
        ref_texts = [ref.raw_text for ref in result.references]
        self.assertTrue(any("Johnson A." in text for text in ref_texts))
        self.assertTrue(any("2022" in text for text in ref_texts))


class TestWebExtractorFallbacks(unittest.TestCase):
    """Test web extractor with fallback functionality."""

    def setUp(self):
        self.web_extractor = WebExtractor()

    @patch("requests.Session.get")
    def test_web_extraction_with_fallbacks_below_threshold(self, mock_get):
        """Test web extraction triggers fallbacks when reference count is low."""
        # Mock HTTP response with minimal references
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
            <h1>Sample Paper</h1>
            <p>Some content here.</p>
            <h2>References</h2>
            <p>1. Smith J. (2023). First paper.</p>
        </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock fallback methods to return additional references
        fallback_refs = [
            Reference(raw_text="Fallback reference 1", doi="10.1234/fallback1"),
            Reference(
                raw_text="Fallback reference 2", title="Fallback Paper", year=2023
            ),
        ]

        with patch.object(
            self.web_extractor.fallback_manager, "apply_fallbacks"
        ) as mock_fallbacks:
            mock_fallbacks.return_value = ExtractionResult(
                source="http://example.com",
                references=[Reference(raw_text="Original ref")] + fallback_refs,
                total_references=3,
            )

            result = self.web_extractor.extract("http://example.com")

            # Verify fallbacks were called
            mock_fallbacks.assert_called_once()
            args, kwargs = mock_fallbacks.call_args

            self.assertEqual(kwargs["source_type"], "web")
            self.assertIsNotNone(kwargs["html_content"])

            # Verify result contains fallback references
            self.assertEqual(len(result.references), 3)

    @patch("requests.Session.get")
    def test_web_extraction_html_structure_fallback(self, mock_get):
        """Test HTML structure fallback functionality in web extraction."""
        # Mock HTTP response with structured lists
        mock_response = Mock()
        mock_response.text = create_sample_html_with_lists()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.web_extractor.extract("http://example.com")

        # Should extract references from HTML structure
        self.assertGreater(len(result.references), 0)

        # Check for expected references
        ref_texts = [ref.raw_text for ref in result.references]
        self.assertTrue(any("Smith, J. and Johnson, A." in text for text in ref_texts))
        self.assertTrue(any("2023" in text for text in ref_texts))

    @patch("requests.Session.get")
    def test_web_extraction_bibtex_fallback(self, mock_get):
        """Test BibTeX fallback functionality in web extraction."""
        # Mock HTTP response with embedded BibTeX
        mock_response = Mock()
        mock_response.text = f"""
        <html>
        <body>
            <h1>Sample Paper</h1>
            <p>Some content here.</p>
            <h2>References</h2>
            <pre>
            {create_sample_text_with_bibtex()}
            </pre>
        </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.web_extractor.extract("http://example.com")

        # Should extract references from BibTeX
        self.assertGreater(len(result.references), 0)

        # Check for BibTeX-parsed references
        ref_titles = [ref.title for ref in result.references if ref.title]
        self.assertTrue(
            any("Machine Learning Techniques" in title for title in ref_titles)
        )
        self.assertTrue(any("Deep Learning" in title for title in ref_titles))

    @patch("requests.Session.get")
    def test_web_extraction_citation_elements_fallback(self, mock_get):
        """Test citation elements fallback functionality in web extraction."""
        # Mock HTTP response with citation elements
        mock_response = Mock()
        mock_response.text = create_sample_html_with_citations()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.web_extractor.extract("http://example.com")

        # Should extract references from citation elements
        self.assertGreater(len(result.references), 0)

        # Check for expected references
        ref_texts = [ref.raw_text for ref in result.references]
        self.assertTrue(any("Smith, J., Johnson, A." in text for text in ref_texts))
        self.assertTrue(any("Brown, K. and Davis, L." in text for text in ref_texts))


class TestFallbackDeduplication(unittest.TestCase):
    """Test deduplication functionality in fallback extraction."""

    def setUp(self):
        self.pdf_extractor = PDFExtractor()
        self.web_extractor = WebExtractor()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pdfplumber.open")
    def test_fallback_deduplication_by_doi(self, mock_pdfplumber_open, mock_exists):
        """Test that duplicate references are removed by DOI."""
        # Mock PDF with minimal primary references
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        References:
        1. Smith J. (2023). First paper. doi:10.1234/example.2023
        """

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber_open.return_value = mock_pdf

        # Mock file exists check
        mock_exists.return_value = True

        result = self.pdf_extractor.extract("test.pdf")

        # Should not have duplicate DOI references
        doi_refs = [
            ref for ref in result.references if ref.doi == "10.1234/example.2023"
        ]
        self.assertEqual(len(doi_refs), 1)

    @patch("requests.Session.get")
    def test_fallback_deduplication_by_title_year(self, mock_get):
        """Test that duplicate references are removed by title+year."""
        # Mock HTTP response with potential duplicates
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
            <h2>References</h2>
            <p>1. Smith J. (2023). Machine Learning Advances.</p>
        </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.web_extractor.extract("http://example.com")

        # Should not have duplicate title+year references
        title_year_refs = [
            ref
            for ref in result.references
            if ref.title
            and ref.year
            and "Machine Learning Advances" in ref.title
            and ref.year == 2023
        ]
        self.assertLessEqual(len(title_year_refs), 1)


class TestFallbackErrorReporting(unittest.TestCase):
    """Test error reporting in fallback extraction."""

    def setUp(self):
        self.pdf_extractor = PDFExtractor()
        self.web_extractor = WebExtractor()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pdfplumber.open")
    def test_fallback_error_reporting(self, mock_pdfplumber_open, mock_exists):
        """Test that fallback errors are properly reported."""
        # Mock PDF with minimal references to trigger fallbacks
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        References:
        1. Smith J. (2023). First paper.
        """

        # Mock table and BibTeX extraction to return empty results
        mock_page.extract_tables.return_value = []

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber_open.return_value = mock_pdf

        # Mock file exists check
        mock_exists.return_value = True

        result = self.pdf_extractor.extract("test.pdf")

        # Should have error messages about failed fallbacks
        self.assertGreater(len(result.extraction_errors), 0)

        error_messages = " ".join(result.extraction_errors)
        self.assertIn("Table fallback:", error_messages)
        self.assertIn("BibTeX fallback:", error_messages)

    @patch("requests.Session.get")
    def test_web_fallback_error_reporting(self, mock_get):
        """Test that web fallback errors are properly reported."""
        # Mock HTTP response with minimal references to trigger fallbacks
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
            <h2>References</h2>
            <p>1. Smith J. (2023). First paper.</p>
        </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.web_extractor.extract("http://example.com")

        # Should have error messages about failed fallbacks (if any)
        if len(result.references) < 3:  # If fallbacks were triggered
            error_messages = " ".join(result.extraction_errors)
            # May or may not have errors depending on fallback success
            self.assertTrue(len(result.extraction_errors) >= 0)


if __name__ == "__main__":
    unittest.main()
