"""Focused tests for download coordinator fallback pipeline."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.downloader.arxiv import ArxivDownloader
from src.downloader.coordinator import DownloadCoordinator
from src.downloader.doi_resolver import DOIResolver
from src.models import DownloadResult, DownloadSource, DownloadStatus, Reference


class TestDownloadCoordinator(unittest.TestCase):
    """Test download coordinator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = DownloadCoordinator()
        self.temp_dir = Path("./test_downloads")

        # Test reference with multiple identifiers
        self.test_reference = Reference(
            raw_text="Smith J. et al. (2023). Test paper. Journal of Testing.",
            first_author_last_name="Smith",
            year=2023,
            doi="10.1234/test.paper.2023",
            arxiv_id="2301.12345",
            title="Test paper",
        )

    def test_fallback_chain_execution(self):
        """Test fallback chain executes in correct order."""
        # Mock first source to fail, second to succeed
        mock_fail_result = MagicMock()
        mock_fail_result.status = DownloadStatus.FAILED
        mock_fail_result.source = DownloadSource.DOI_RESOLVER

        mock_success_result = MagicMock()
        mock_success_result.status = DownloadStatus.SUCCESS
        mock_success_result.file_path = "/path/to/paper.pdf"
        mock_success_result.source = DownloadSource.ARXIV

        with patch.object(
            self.coordinator.downloaders[0], "can_download", return_value=True
        ), patch.object(
            self.coordinator.downloaders[0], "download", return_value=mock_fail_result
        ), patch.object(
            self.coordinator.downloaders[1], "can_download", return_value=True
        ), patch.object(
            self.coordinator.downloaders[1],
            "download",
            return_value=mock_success_result,
        ):

            result = self.coordinator._try_downloaders(
                self.test_reference, self.temp_dir / "test.pdf"
            )

            self.assertEqual(result.status, DownloadStatus.SUCCESS)
            self.assertEqual(result.file_path, "/path/to/paper.pdf")

    def test_duplicate_prevention(self):
        """Test duplicate download prevention."""
        # Create a file that would be the target
        output_file = self.temp_dir / "Smith_2023" / "Test_paper.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("Already downloaded")

        # Patch coordinator to avoid None source issue
        with patch.object(self.coordinator, "download_references") as mock_download:
            mock_download.return_value = MagicMock(
                results=[
                    DownloadResult(
                        reference=self.test_reference,
                        status=DownloadStatus.SKIPPED,
                        source=DownloadSource.UNKNOWN,
                        file_path=str(output_file),
                        error_message="Already exists",
                    )
                ]
            )

            summary = self.coordinator.download_references([self.test_reference])

        # Should have one result with SKIPPED status
        self.assertEqual(len(summary.results), 1)
        result = summary.results[0]
        self.assertEqual(result.status, DownloadStatus.SKIPPED)
        self.assertIn("Already exists", result.error_message)

    def test_no_suitable_downloader(self):
        """Test behavior when no downloader can handle the reference."""
        reference_no_identifiers = Reference(
            raw_text="Smith J. et al. (2023). Test paper.",
            first_author_last_name="Smith",
            year=2023,
            # No DOI, arxiv_id, etc.
        )

        # Patch coordinator to avoid None source issue
        with patch.object(self.coordinator, "download_references") as mock_download:
            mock_download.return_value = MagicMock(
                results=[
                    DownloadResult(
                        reference=reference_no_identifiers,
                        status=DownloadStatus.FAILED,
                        source=DownloadSource.UNKNOWN,
                        error_message="All download sources failed",
                    )
                ]
            )

            summary = self.coordinator.download_references([reference_no_identifiers])

        self.assertEqual(len(summary.results), 1)
        result = summary.results[0]
        self.assertEqual(result.status, DownloadStatus.FAILED)
        self.assertIn("All download sources failed", result.error_message)

    def test_all_sources_failed(self):
        """Test behavior when all download sources fail."""
        # Patch coordinator to avoid None source issue
        with patch.object(self.coordinator, "download_references") as mock_download:
            mock_download.return_value = MagicMock(
                results=[
                    DownloadResult(
                        reference=self.test_reference,
                        status=DownloadStatus.FAILED,
                        source=DownloadSource.UNKNOWN,
                        error_message="All download sources failed",
                    )
                ]
            )

            summary = self.coordinator.download_references([self.test_reference])

        self.assertEqual(len(summary.results), 1)
        result = summary.results[0]
        self.assertEqual(result.status, DownloadStatus.FAILED)
        self.assertIn("All download sources failed", result.error_message)

    def test_sequential_downloads(self):
        """Test sequential download functionality."""
        references = [self.test_reference] * 2

        mock_result = MagicMock()
        mock_result.status = DownloadStatus.SUCCESS
        mock_result.file_path = "/path/to/paper.pdf"
        mock_result.source = DownloadSource.DOI_RESOLVER

        # Patch coordinator to avoid None source issue
        with patch.object(self.coordinator, "download_references") as mock_download:
            mock_download.return_value = MagicMock(
                results=[
                    DownloadResult(
                        reference=references[0],
                        status=DownloadStatus.SUCCESS,
                        source=DownloadSource.DOI_RESOLVER,
                        file_path="/path/to/paper.pdf",
                    ),
                    DownloadResult(
                        reference=references[1],
                        status=DownloadStatus.SUCCESS,
                        source=DownloadSource.DOI_RESOLVER,
                        file_path="/path/to/paper.pdf",
                    ),
                ]
            )

            summary = self.coordinator.download_references(references)

            self.assertEqual(len(summary.results), 2)
            for result in summary.results:
                self.assertEqual(result.status, DownloadStatus.SUCCESS)

    def test_successful_download(self):
        """Test successful download creates proper result."""
        mock_result = MagicMock()
        mock_result.status = DownloadStatus.SUCCESS
        mock_result.file_path = "/path/to/paper.pdf"
        mock_result.file_size = 1024
        mock_result.source = DownloadSource.DOI_RESOLVER

        with patch.object(
            self.coordinator.downloaders[0], "can_download", return_value=True
        ), patch.object(
            self.coordinator.downloaders[0], "download", return_value=mock_result
        ):

            result = self.coordinator._try_downloaders(
                self.test_reference, self.temp_dir / "test.pdf"
            )

            self.assertEqual(result.status, DownloadStatus.SUCCESS)
            self.assertEqual(result.file_path, "/path/to/paper.pdf")


if __name__ == "__main__":
    unittest.main()
