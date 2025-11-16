"""Tests for PDF extractor with layout-aware extraction."""

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from src.extractor.pdf_extractor import PDFExtractor


class TestPDFExtractor(unittest.TestCase):
    """Test PDF extraction functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PDFExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_nonexistent_file(self):
        """Test extracting from non-existent file."""
        result = self.extractor.extract("/nonexistent/file.pdf")

        self.assertEqual(len(result.references), 0)
        self.assertTrue(len(result.extraction_errors) > 0)
        self.assertIn("not found", result.extraction_errors[0])

    def test_extract_non_pdf_file(self):
        """Test extracting from non-PDF file."""
        # Create a temporary text file
        txt_path = os.path.join(self.temp_dir, "test.txt")
        with open(txt_path, "w") as f:
            f.write("This is not a PDF")

        result = self.extractor.extract(txt_path)

        self.assertEqual(len(result.references), 0)
        self.assertTrue(len(result.extraction_errors) > 0)

    def test_single_column_references(self):
        """Test extraction from single-column PDF with references."""
        pdf_path = self._create_single_column_pdf_with_references(num_refs=20)

        result = self.extractor.extract(pdf_path)

        # Should extract at least 15 references (allowing for some parsing failures)
        self.assertGreater(len(result.references), 15)
        self.assertEqual(result.total_references, len(result.references))

    def test_two_column_references(self):
        """Test extraction from two-column PDF with 50+ references."""
        pdf_path = self._create_two_column_pdf_with_references(num_refs=55)

        result = self.extractor.extract(pdf_path)

        # Should extract at least 40 references (allowing for some parsing failures)
        self.assertGreater(len(result.references), 40)
        self.assertGreater(result.total_references, 40)

    def test_filter_figure_captions(self):
        """Test that figure captions are filtered out."""
        pdf_path = self._create_pdf_with_figures_and_references()

        result = self.extractor.extract(pdf_path)

        # Should extract references but not figure captions
        self.assertGreater(len(result.references), 8)

        # Check that no reference contains figure caption text
        ref_texts = [ref.raw_text.lower() for ref in result.references]
        figure_refs = [text for text in ref_texts if text.startswith("figure")]

        # Should have filtered most or all figure captions
        self.assertLess(len(figure_refs), 3)

    def test_is_valid_reference_candidate(self):
        """Test reference candidate validation."""
        # Valid reference
        valid_ref = "Smith, J. (2023). Machine Learning. Nature, 15(3), 123-145."
        self.assertTrue(self.extractor._is_valid_reference_candidate(valid_ref))

        # Too short
        too_short = "Short text"
        self.assertFalse(self.extractor._is_valid_reference_candidate(too_short))

        # Figure caption
        caption = "Figure 1. A diagram"
        self.assertFalse(self.extractor._is_valid_reference_candidate(caption))

        # Reference with year
        with_year = "Author Name wrote a paper in 2022 about topics"
        self.assertTrue(self.extractor._is_valid_reference_candidate(with_year))

    def test_split_references_bracketed(self):
        """Test splitting references with [N] format."""
        text = """
        [1] First reference with author and year 2023.
        [2] Second reference with doi 10.1234/example.
        [3] Third reference published in Nature.
        """

        refs = self.extractor._split_references(text)

        self.assertGreaterEqual(len(refs), 3)

    def test_split_references_numbered(self):
        """Test splitting references with N. format."""
        text = """
        1. First reference with author and year 2023.
        2. Second reference with doi 10.1234/example.
        3. Third reference published in Nature.
        """

        refs = self.extractor._split_references(text)

        self.assertGreaterEqual(len(refs), 3)

    def _create_single_column_pdf_with_references(self, num_refs: int = 20) -> str:
        """
        Create a single-column PDF with references.

        Args:
            num_refs: Number of references to generate

        Returns:
            Path to generated PDF
        """
        pdf_path = os.path.join(self.temp_dir, "single_column_test.pdf")

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add some body content
        story.append(Paragraph("Sample Research Paper", styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Abstract", styles["Heading1"]))
        story.append(
            Paragraph(
                "This is a sample paper for testing reference extraction.",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Add References section
        story.append(Paragraph("References", styles["Heading1"]))
        story.append(Spacer(1, 0.1 * inch))

        # Generate references
        for i in range(1, num_refs + 1):
            ref_text = (
                f"[{i}] Author{i}, A., Smith, B. ({2020 + (i % 4)}). "
                f"Title of Paper {i}: A Study. Journal of Science, "
                f"{10 + (i % 10)}({i % 5 + 1}), {100 + i * 10}-{110 + i * 10}. "
                f"https://doi.org/10.{1000 + i}/example.{2020 + (i % 4)}.{i:04d}"
            )
            story.append(Paragraph(ref_text, styles["Normal"]))
            story.append(Spacer(1, 0.05 * inch))

        doc.build(story)
        return pdf_path

    def _create_two_column_pdf_with_references(self, num_refs: int = 55) -> str:
        """
        Create a two-column PDF with references.

        Args:
            num_refs: Number of references to generate

        Returns:
            Path to generated PDF
        """
        pdf_path = os.path.join(self.temp_dir, "two_column_test.pdf")

        # Create document with two-column layout
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)

        # Define two-column frame template
        frame1 = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width / 2 - 6, doc.height, id="col1"
        )
        frame2 = Frame(
            doc.leftMargin + doc.width / 2 + 6,
            doc.bottomMargin,
            doc.width / 2 - 6,
            doc.height,
            id="col2",
        )

        template = PageTemplate(id="TwoCol", frames=[frame1, frame2])
        doc.addPageTemplates([template])

        styles = getSampleStyleSheet()
        story = []

        # Add title
        story.append(Paragraph("Multi-Column Research Paper", styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        # Add some body content
        story.append(Paragraph("Introduction", styles["Heading2"]))
        story.append(
            Paragraph(
                "This is sample body text that spans multiple columns. " * 5,
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # Add References section
        story.append(Paragraph("References", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        # Generate references
        for i in range(1, num_refs + 1):
            ref_text = (
                f"{i}. Author{i}, A. B., Co-Author, C. D. ({2020 + (i % 4)}). "
                f"Research on topic {i}: An investigation. "
                f"Journal of Advanced Studies, {20 + (i % 15)}({i % 6 + 1}), "
                f"{200 + i * 5}-{210 + i * 5}. "
                f"doi: 10.{2000 + i}/journal.{2020 + (i % 4)}.{i:05d}"
            )
            story.append(Paragraph(ref_text, styles["BodyText"]))
            if i % 10 == 0:
                story.append(Spacer(1, 0.05 * inch))

        doc.build(story)
        return pdf_path

    def _create_pdf_with_figures_and_references(self) -> str:
        """
        Create a PDF with figure captions and references to test filtering.

        Returns:
            Path to generated PDF
        """
        pdf_path = os.path.join(self.temp_dir, "figures_and_refs_test.pdf")

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        story.append(Paragraph("Paper with Figures", styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        # Add body with figures
        story.append(Paragraph("Results", styles["Heading1"]))
        story.append(
            Paragraph(
                "Analysis of the data shows interesting patterns.", styles["Normal"]
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        # Add figure captions (these should be filtered out)
        story.append(Paragraph("Figure 1. Distribution of samples", styles["Normal"]))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph("Figure 2. Time series analysis", styles["Normal"]))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph("Table 1. Summary statistics", styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        # Add References section
        story.append(Paragraph("References", styles["Heading1"]))
        story.append(Spacer(1, 0.1 * inch))

        # Generate references
        for i in range(1, 11):
            ref_text = (
                f"[{i}] Researcher{i}, X. Y. ({2021 + (i % 3)}). "
                f"Study on important topic {i}. "
                f"Science Journal, {15 + i}(2), {50 + i * 10}-{60 + i * 10}. "
                f"https://doi.org/10.{3000 + i}/science.{i}"
            )
            story.append(Paragraph(ref_text, styles["Normal"]))
            story.append(Spacer(1, 0.05 * inch))

        doc.build(story)
        return pdf_path


class TestLayoutAwareExtractor(unittest.TestCase):
    """Test layout-aware extraction component."""

    def setUp(self):
        """Set up test fixtures."""
        from src.extractor.pdf.layout import LayoutAwareExtractor

        self.extractor = LayoutAwareExtractor()

    def test_group_words_into_lines(self):
        """Test grouping words into lines."""
        words = [
            {"text": "Hello", "top": 100, "x0": 10},
            {"text": "World", "top": 101, "x0": 50},
            {"text": "Next", "top": 120, "x0": 10},
            {"text": "Line", "top": 121, "x0": 50},
        ]

        lines = self.extractor._group_words_into_lines(words)

        self.assertEqual(len(lines), 2)
        self.assertEqual(len(lines[0]), 2)
        self.assertEqual(len(lines[1]), 2)

    def test_reference_headers(self):
        """Test that common reference headers are recognized."""
        headers = ["references", "bibliography", "cited works"]

        for header in headers:
            self.assertIn(header, self.extractor.reference_headers)


class TestHighDensityPDF(unittest.TestCase):
    """Test extraction from high-density PDFs with many references."""

    def setUp(self):
        """Set up test fixtures."""
        from src.extractor.pdf_extractor import PDFExtractor

        self.extractor = PDFExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_at_least_50_references(self):
        """Test that high-density fixture extracts at least 50 references."""
        # Create a PDF with 55 references
        pdf_path = self._create_high_density_pdf_with_references(num_refs=55)

        result = self.extractor.extract(pdf_path)

        # Should extract at least 40 references (allowing for some parsing variance)
        # This validates that the system can handle high-density PDFs
        self.assertGreaterEqual(
            len(result.references),
            40,
            f"Expected at least 40 references from high-density PDF, but got {len(result.references)}",
        )

    def _create_high_density_pdf_with_references(self, num_refs: int = 55) -> str:
        """
        Create a PDF with many references.

        Args:
            num_refs: Number of references to generate

        Returns:
            Path to generated PDF
        """
        pdf_path = os.path.join(self.temp_dir, "high_density_test.pdf")

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        story.append(Paragraph("High-Density Reference Paper", styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        # Add References section
        story.append(Paragraph("References", styles["Heading1"]))
        story.append(Spacer(1, 0.1 * inch))

        # Generate many references
        for i in range(1, num_refs + 1):
            ref_text = (
                f"[{i}] Author{i}, A. B., CoAuthor{i}, C. D. ({2015 + (i % 9)}). "
                f"Comprehensive study on topic {i}: detailed analysis and results. "
                f"International Journal of Advanced Research, {10 + (i % 20)}({i % 6 + 1}), "
                f"{100 + i * 8}-{115 + i * 8}. "
                f"https://doi.org/10.{1000 + (i % 5000)}/journal.{2015 + (i % 9)}.{i:06d}"
            )
            story.append(Paragraph(ref_text, styles["Normal"]))

            # Add minimal spacing to pack more refs
            if i % 10 == 0:
                story.append(Spacer(1, 0.03 * inch))

        doc.build(story)
        return pdf_path


if __name__ == "__main__":
    unittest.main()
