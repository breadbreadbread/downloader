"""Tests for extraction fallback strategies."""

import unittest
from unittest.mock import Mock, patch

import pdfplumber
from bs4 import BeautifulSoup

from src.extractor.fallbacks import ExtractionFallbackManager
from src.models import ExtractionResult, Reference


class TestExtractionFallbackManager(unittest.TestCase):
    """Test fallback extraction strategies."""

    def setUp(self):
        self.fallback_manager = ExtractionFallbackManager()
        self.sample_result = ExtractionResult(source="test.pdf")
        self.sample_result.references = [
            Reference(raw_text="Smith J. (2023). First paper."),
            Reference(raw_text="Johnson A. (2022). Second paper."),
        ]

    def test_should_trigger_fallbacks_below_threshold(self):
        """Test that fallbacks trigger when reference count is below threshold."""
        # With only 2 references and threshold of 3, should trigger
        self.assertTrue(
            self.fallback_manager.should_trigger_fallbacks(self.sample_result)
        )

    def test_should_not_trigger_fallbacks_above_threshold(self):
        """Test that fallbacks don't trigger when reference count is above threshold."""
        # Add more references to exceed threshold
        self.sample_result.references.extend(
            [
                Reference(raw_text="Brown K. (2021). Third paper."),
                Reference(raw_text="Davis L. (2020). Fourth paper."),
            ]
        )
        self.assertFalse(
            self.fallback_manager.should_trigger_fallbacks(self.sample_result)
        )

    def test_extract_from_tables_with_reference_table(self):
        """Test table extraction with reference-like content."""
        # Mock PDF page with a reference table
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [
                [
                    "1",
                    "Smith J., Johnson A.",
                    "2023",
                    "Machine Learning Advances",
                    "J. AI Research",
                    "15(3)",
                    "123-145",
                ],
                [
                    "2",
                    "Brown K., Davis L.",
                    "2022",
                    "Deep Learning Methods",
                    "Neural Networks",
                    "12(2)",
                    "45-67",
                ],
            ]
        ]

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]

        references = self.fallback_manager._extract_from_tables(mock_pdf)

        self.assertGreater(len(references), 0)
        # Check that references contain expected information
        ref_texts = [ref.raw_text for ref in references]
        self.assertTrue(any("Smith J." in text for text in ref_texts))
        self.assertTrue(any("2023" in text for text in ref_texts))

    def test_extract_from_tables_with_non_reference_table(self):
        """Test table extraction with non-reference content."""
        # Mock PDF page with a non-reference table
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [
                ["Name", "Age", "City"],
                ["John", "25", "New York"],
                ["Jane", "30", "Boston"],
            ]
        ]

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]

        references = self.fallback_manager._extract_from_tables(mock_pdf)

        # Should extract very few or no references from non-reference table
        self.assertLessEqual(len(references), 1)

    def test_extract_from_bibtex_with_entries(self):
        """Test BibTeX extraction with valid entries."""
        bibtex_text = """
        @article{smith2023machine,
            title={Machine Learning Advances},
            author={Smith, John and Johnson, Alice},
            journal={Journal of AI Research},
            volume={15},
            number={3},
            pages={123--145},
            year={2023},
            doi={10.1234/example.2023}
        }
        
        @inproceedings{brown2022deep,
            title={Deep Learning Methods},
            author={Brown, Kevin and Davis, Lisa},
            booktitle={Neural Networks Conference},
            pages={45--67},
            year={2022}
        }
        """

        references = self.fallback_manager._extract_from_bibtex(bibtex_text)

        self.assertEqual(len(references), 2)

        # Check first reference
        ref1 = references[0]
        self.assertEqual(ref1.title, "Machine Learning Advances")
        self.assertEqual(ref1.year, 2023)
        self.assertEqual(ref1.doi, "10.1234/example.2023")
        self.assertEqual(ref1.publication_type, "journal")
        self.assertIn("Smith, John", ref1.authors)

        # Check second reference
        ref2 = references[1]
        self.assertEqual(ref2.title, "Deep Learning Methods")
        self.assertEqual(ref2.year, 2022)
        self.assertEqual(ref2.publication_type, "conference")

    def test_extract_from_bibtex_no_entries(self):
        """Test BibTeX extraction with no valid entries."""
        text = "This is just regular text without any BibTeX entries."

        references = self.fallback_manager._extract_from_bibtex(text)

        self.assertEqual(len(references), 0)

    def test_parse_bibtex_entry_complete(self):
        """Test parsing a complete BibTeX entry."""
        bibtex_entry = """
        @article{example2023,
            title={Example Paper Title},
            author={Smith, John and Doe, Jane},
            journal={Example Journal},
            volume={10},
            number={2},
            pages={100--120},
            year={2023},
            doi={10.1234/example.2023},
            publisher={Example Publisher}
        }
        """

        ref = self.fallback_manager._parse_bibtex_entry(bibtex_entry)

        self.assertIsNotNone(ref)
        self.assertEqual(ref.title, "Example Paper Title")
        self.assertEqual(ref.year, 2023)
        self.assertEqual(ref.journal, "Example Journal")
        self.assertEqual(ref.volume, "10")
        self.assertEqual(ref.issue, "2")
        self.assertEqual(ref.pages, "100--120")
        self.assertEqual(ref.doi, "10.1234/example.2023")
        self.assertEqual(ref.publisher, "Example Publisher")
        self.assertEqual(ref.publication_type, "journal")
        self.assertEqual(len(ref.authors), 2)
        self.assertIn("Smith, John", ref.authors)
        self.assertEqual(ref.first_author_last_name, "Smith")

    def test_parse_bibtex_entry_minimal(self):
        """Test parsing a minimal BibTeX entry."""
        bibtex_entry = """
        @misc{minimal2023,
            title={Minimal Entry},
            author={Author Name},
            year={2023}
        }
        """

        ref = self.fallback_manager._parse_bibtex_entry(bibtex_entry)

        self.assertIsNotNone(ref)
        self.assertEqual(ref.title, "Minimal Entry")
        self.assertEqual(ref.year, 2023)
        self.assertEqual(ref.publication_type, "other")
        self.assertIn("Author Name", ref.authors)

    def test_extract_from_html_structure_with_lists(self):
        """Test HTML structure extraction with ordered/unordered lists."""
        html_content = """
        <html>
        <body>
            <div>
                <h2>References</h2>
                <ol>
                    <li>Smith, J. (2023). Machine Learning Advances. J. AI Research, 15(3), 123-145.</li>
                    <li>Johnson, A. (2022). Deep Learning Methods. Neural Networks, 12(2), 45-67.</li>
                    <li>Brown, K. (2021). Pattern Recognition. Computer Vision, 8(1), 10-25.</li>
                </ol>
            </div>
        </body>
        </html>
        """

        references = self.fallback_manager._extract_from_html_structure(html_content)

        self.assertGreater(len(references), 0)
        ref_texts = [ref.raw_text for ref in references]
        self.assertTrue(any("Smith, J." in text for text in ref_texts))
        self.assertTrue(any("2023" in text for text in ref_texts))

    def test_extract_from_html_structure_with_citations(self):
        """Test HTML structure extraction with citation elements."""
        html_content = """
        <html>
        <body>
            <div class="references">
                <cite>Smith, J. (2023). Machine Learning Advances. J. AI Research, 15(3), 123-145.</cite>
                <cite>Johnson, A. (2022). Deep Learning Methods. Neural Networks, 12(2), 45-67.</cite>
            </div>
        </body>
        </html>
        """

        references = self.fallback_manager._extract_from_html_structure(html_content)

        self.assertGreater(len(references), 0)
        ref_texts = [ref.raw_text for ref in references]
        self.assertTrue(any("Smith, J." in text for text in ref_texts))

    def test_extract_from_html_structure_no_references(self):
        """Test HTML structure extraction with no reference-like content."""
        html_content = """
        <html>
        <body>
            <div>
                <h1>Welcome</h1>
                <p>This is a regular web page with no references.</p>
                <ul>
                    <li>First item</li>
                    <li>Second item</li>
                </ul>
            </div>
        </body>
        </html>
        """

        references = self.fallback_manager._extract_from_html_structure(html_content)

        # Should extract very few or no references
        self.assertLessEqual(len(references), 1)

    def test_looks_like_reference_positive(self):
        """Test reference detection with reference-like text."""
        reference_text = "Smith, J. (2023). Machine Learning Advances. Journal of AI Research, 15(3), 123-145."

        self.assertTrue(self.fallback_manager._looks_like_reference(reference_text))

    def test_looks_like_reference_negative(self):
        """Test reference detection with non-reference text."""
        non_reference_text = (
            "This is just a regular sentence about something completely different."
        )

        self.assertFalse(
            self.fallback_manager._looks_like_reference(non_reference_text)
        )

    def test_looks_like_reference_too_short(self):
        """Test reference detection with very short text."""
        short_text = "Too short"

        self.assertFalse(self.fallback_manager._looks_like_reference(short_text))

    def test_create_reference_fingerprint_set(self):
        """Test creation of reference fingerprint set for deduplication."""
        refs = [
            Reference(raw_text="ref1", doi="10.1234/example.2023"),
            Reference(raw_text="ref2", title="Paper Title", year=2023),
            Reference(raw_text="ref3"),  # Only raw text
        ]

        fingerprints = self.fallback_manager._create_reference_fingerprint_set(refs)

        self.assertEqual(len(fingerprints), 3)
        self.assertIn("doi:10.1234/example.2023", fingerprints)
        self.assertTrue(any("title_year:" in fp for fp in fingerprints))
        self.assertTrue(any("raw:" in fp for fp in fingerprints))

    def test_deduplicate_references(self):
        """Test reference deduplication."""
        existing_refs = [
            Reference(raw_text="ref1", doi="10.1234/example.2023"),
            Reference(raw_text="ref2", title="Paper Title", year=2023),
        ]
        existing_fingerprints = self.fallback_manager._create_reference_fingerprint_set(
            existing_refs
        )

        new_refs = [
            Reference(raw_text="ref3", doi="10.5678/new.2023"),  # New
            Reference(raw_text="ref4", doi="10.1234/example.2023"),  # Duplicate DOI
            Reference(
                raw_text="ref5", title="Paper Title", year=2023
            ),  # Duplicate title+year
            Reference(raw_text="ref6", title="Different Title", year=2023),  # New
        ]

        unique_refs = self.fallback_manager._deduplicate_references(
            new_refs, existing_fingerprints
        )

        # Should only return the truly new references
        self.assertEqual(len(unique_refs), 2)
        self.assertTrue(any(ref.doi == "10.5678/new.2023" for ref in unique_refs))
        self.assertTrue(any(ref.title == "Different Title" for ref in unique_refs))

    def test_apply_fallbacks_pdf_source(self):
        """Test applying fallbacks for PDF source."""
        # Create result with few references to trigger fallbacks
        result = ExtractionResult(source="test.pdf")
        result.references = [Reference(raw_text="Only one reference")]

        # Mock PDF object
        mock_pdf = Mock()

        with patch.object(
            self.fallback_manager, "_extract_from_tables", return_value=[]
        ), patch.object(self.fallback_manager, "_extract_from_bibtex", return_value=[]):

            enhanced_result = self.fallback_manager.apply_fallbacks(
                result=result,
                source_text="Sample text",
                source_type="pdf",
                pdf_object=mock_pdf,
            )

            # Should have error messages about failed fallbacks
            self.assertGreater(len(enhanced_result.extraction_errors), 0)
            self.assertTrue(
                any(
                    "Table fallback:" in error
                    for error in enhanced_result.extraction_errors
                )
            )
            self.assertTrue(
                any(
                    "BibTeX fallback:" in error
                    for error in enhanced_result.extraction_errors
                )
            )

    def test_apply_fallbacks_web_source(self):
        """Test applying fallbacks for web source."""
        # Create result with few references to trigger fallbacks
        result = ExtractionResult(source="http://example.com")
        result.references = [Reference(raw_text="Only one reference")]

        html_content = "<html><body>Sample HTML</body></html>"

        with patch.object(
            self.fallback_manager, "_extract_from_bibtex", return_value=[]
        ), patch.object(
            self.fallback_manager, "_extract_from_html_structure", return_value=[]
        ):

            enhanced_result = self.fallback_manager.apply_fallbacks(
                result=result,
                source_text="Sample text",
                source_type="web",
                html_content=html_content,
            )

            # Should have error messages about failed fallbacks
            self.assertGreater(len(enhanced_result.extraction_errors), 0)
            self.assertTrue(
                any(
                    "BibTeX fallback:" in error
                    for error in enhanced_result.extraction_errors
                )
            )
            self.assertTrue(
                any(
                    "HTML structure fallback:" in error
                    for error in enhanced_result.extraction_errors
                )
            )

    def test_apply_fallbacks_no_trigger(self):
        """Test that fallbacks are not applied when reference count is above threshold."""
        # Create result with many references to avoid triggering fallbacks
        result = ExtractionResult(source="test.pdf")
        result.references = [Reference(raw_text=f"Reference {i}") for i in range(10)]

        mock_pdf = Mock()

        with patch.object(
            self.fallback_manager, "_extract_from_tables"
        ) as mock_tables, patch.object(
            self.fallback_manager, "_extract_from_bibtex"
        ) as mock_bibtex:

            enhanced_result = self.fallback_manager.apply_fallbacks(
                result=result,
                source_text="Sample text",
                source_type="pdf",
                pdf_object=mock_pdf,
            )

            # Fallback methods should not be called
            mock_tables.assert_not_called()
            mock_bibtex.assert_not_called()

            # Result should be unchanged
            self.assertEqual(len(enhanced_result.references), 10)

    def test_apply_fallbacks_successful_extraction(self):
        """Test successful fallback extraction with new references."""
        # Create result with few references to trigger fallbacks
        result = ExtractionResult(source="test.pdf")
        result.references = [Reference(raw_text="Original reference")]

        # Mock successful fallback extraction
        fallback_refs = [
            Reference(raw_text="Fallback reference 1", doi="10.1234/fallback1"),
            Reference(
                raw_text="Fallback reference 2", title="Fallback Paper", year=2023
            ),
        ]

        mock_pdf = Mock()

        with patch.object(
            self.fallback_manager, "_extract_from_tables", return_value=[]
        ), patch.object(
            self.fallback_manager, "_extract_from_bibtex", return_value=fallback_refs
        ):

            enhanced_result = self.fallback_manager.apply_fallbacks(
                result=result,
                source_text="Sample text",
                source_type="pdf",
                pdf_object=mock_pdf,
            )

            # Should have added the fallback references
            self.assertEqual(
                len(enhanced_result.references), 3
            )  # 1 original + 2 fallback
            self.assertEqual(enhanced_result.total_references, 3)

            # Should not have error messages about failed fallbacks
            bibtex_errors = [
                e for e in enhanced_result.extraction_errors if "BibTeX fallback:" in e
            ]
            self.assertEqual(len(bibtex_errors), 0)


class TestTableExtractionHelpers(unittest.TestCase):
    """Test helper methods for table extraction."""

    def setUp(self):
        self.fallback_manager = ExtractionFallbackManager()

    def test_normalize_table_cells(self):
        """Test table cell normalization."""
        table = [
            [
                "1",
                "Smith, J.",
                "2023",
                "Paper Title",
                "Journal Name",
                "15(3)",
                "123-145",
            ],
            [
                "2",
                "Johnson, A.",
                "2022",
                "Another Paper",
                "Another Journal",
                "12(2)",
                "45-67",
            ],
            ["", "", "", "", "", "", ""],  # Empty row
            ["3", "Brown, K.", "", "Incomplete Paper", "", "", ""],  # Incomplete row
        ]

        normalized = self.fallback_manager._normalize_table_cells(table)

        lines = normalized.split("\n")
        self.assertEqual(len(lines), 3)  # Should skip empty row, include incomplete

        # Check that normalization worked correctly
        self.assertIn(
            "1 Smith, J. 2023 Paper Title Journal Name 15(3) 123-145", lines[0]
        )
        self.assertIn(
            "2 Johnson, A. 2022 Another Paper Another Journal 12(2) 45-67", lines[1]
        )
        self.assertIn("3 Brown, K. Incomplete Paper", lines[2])

    def test_looks_like_reference_table_positive(self):
        """Test reference table detection with reference-like content."""
        table_text = """
        Smith, J. (2023). Machine Learning Advances. Journal of AI Research, 15(3), 123-145. doi:10.1234/example
        Johnson, A. (2022). Deep Learning Methods. Neural Networks, vol 12, pp 45-67.
        """

        self.assertTrue(self.fallback_manager._looks_like_reference_table(table_text))

    def test_looks_like_reference_table_negative(self):
        """Test reference table detection with non-reference content."""
        table_text = """
        Name Age City
        John 25 New York
        Jane 30 Boston
        """

        self.assertFalse(self.fallback_manager._looks_like_reference_table(table_text))

    def test_looks_like_reference_table_too_short(self):
        """Test reference table detection with very short text."""
        short_text = "Too short"

        self.assertFalse(self.fallback_manager._looks_like_reference_table(short_text))


if __name__ == "__main__":
    unittest.main()
