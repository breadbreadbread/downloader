"""Tests for reference parser."""

import unittest

from src.extractor.parser import ReferenceParser
from src.models import Reference


class TestReferenceParser(unittest.TestCase):
    """Test reference parsing functionality."""

    def setUp(self):
        self.parser = ReferenceParser()

    def test_parse_reference_with_doi(self):
        """Test parsing reference with DOI."""
        text = (
            "Smith, J., Johnson, A. (2023). Machine Learning Applications. "
            "Journal of AI Research, 15(3), 123-145. "
            "https://doi.org/10.1234/example.2023"
        )

        ref = self.parser.parse_reference(text)

        self.assertIsNotNone(ref)
        self.assertIsNotNone(ref.doi)
        self.assertIn("2023", str(ref.year))
        self.assertIsNotNone(ref.title)

    def test_parse_reference_extract_authors(self):
        """Test author extraction."""
        text = "Smith, J. and Johnson, A. (2023). Paper Title."

        ref = self.parser.parse_reference(text)

        self.assertIsNotNone(ref)
        self.assertTrue(len(ref.authors) > 0)
        self.assertIsNotNone(ref.first_author_last_name)

    def test_parse_reference_extract_year(self):
        """Test year extraction."""
        text = "Author Name. Title of Paper. " "Nature, Vol 15, 2022."

        ref = self.parser.parse_reference(text)

        self.assertIsNotNone(ref)
        self.assertEqual(ref.year, 2022)

    def test_extract_arxiv_id(self):
        """Test arXiv ID extraction."""
        text = "arXiv:2301.12345 - Quantum Computing Paper"

        arxiv_id = self.parser._extract_arxiv_id(text)

        self.assertIsNotNone(arxiv_id)
        self.assertEqual(arxiv_id, "2301.12345")

    def test_extract_page_range(self):
        """Test page range extraction."""
        text = "pp. 123-145"

        from src.utils import extract_page_range

        pages = extract_page_range(text)

        self.assertEqual(pages, "123-145")

    def test_minimum_text_length(self):
        """Test that very short text returns None."""
        text = "Too short"

        ref = self.parser.parse_reference(text)

        self.assertIsNone(ref)


class TestReferenceDataModel(unittest.TestCase):
    """Test Reference data model."""

    def test_get_output_folder_name(self):
        """Test output folder name generation."""
        ref = Reference(raw_text="test", first_author_last_name="Smith", year=2023)

        folder_name = ref.get_output_folder_name()

        self.assertEqual(folder_name, "Smith_2023")

    def test_get_filename(self):
        """Test filename generation."""
        ref = Reference(
            raw_text="test",
            first_author_last_name="Smith",
            year=2023,
            title="Example Paper Title",
        )

        filename = ref.get_filename()

        self.assertIn("Smith", filename)
        self.assertIn("2023", filename)


if __name__ == "__main__":
    unittest.main()
