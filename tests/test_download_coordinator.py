"""Focused tests for download coordinator fallback pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.downloader.coordinator import DownloadCoordinator
from src.models import DownloadResult, DownloadSource, DownloadStatus, Reference


@pytest.fixture(name="test_reference")
def fixture_test_reference() -> Reference:
    """Create a test reference with multiple identifiers."""
    return Reference(
        raw_text="Smith J. et al. (2023). Test paper. Journal of Testing.",
        first_author_last_name="Smith",
        year=2023,
        doi="10.1234/test.paper.2023",
        arxiv_id="2301.12345",
        title="Test paper",
    )


def test_fallback_chain_executes_in_order(tmp_path: Path, test_reference: Reference) -> None:
    """Test that fallback chain proceeds when first source fails."""
    coordinator = DownloadCoordinator(tmp_path)

    mock_fail_result = DownloadResult(
        reference=test_reference,
        status=DownloadStatus.FAILED,
        source=DownloadSource.DOI_RESOLVER,
        error_message="DOI resolution failed",
    )

    mock_success_result = DownloadResult(
        reference=test_reference,
        status=DownloadStatus.SUCCESS,
        source=DownloadSource.ARXIV,
        file_path=str(tmp_path / "paper.pdf"),
        file_size=1024,
    )

    with (
        patch.object(coordinator.downloaders[0], "can_download", return_value=True),
        patch.object(coordinator.downloaders[0], "download", return_value=mock_fail_result),
        patch.object(coordinator.downloaders[1], "can_download", return_value=True),
        patch.object(coordinator.downloaders[1], "download", return_value=mock_success_result),
    ):
        result = coordinator._try_downloaders(test_reference, tmp_path / "test.pdf")

    assert result.status == DownloadStatus.SUCCESS
    assert result.file_path == str(tmp_path / "paper.pdf")
    assert result.source == DownloadSource.ARXIV


def test_skip_existing_files(tmp_path: Path, test_reference: Reference) -> None:
    """Test that already-downloaded files are skipped."""
    coordinator = DownloadCoordinator(tmp_path)
    output_folder = tmp_path / f"{test_reference.first_author_last_name}_{test_reference.year}"
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / f"{test_reference.get_filename()}.pdf"
    output_file.write_text("already downloaded", encoding="utf-8")

    summary = coordinator.download_references([test_reference])
    summary.calculate_stats()

    assert summary.total_references == 1
    assert summary.skipped == 1
    assert len(summary.results) == 1
    result = summary.results[0]
    assert result.status == DownloadStatus.SKIPPED
    assert result.file_path == str(output_file)


def test_no_suitable_downloader(tmp_path: Path) -> None:
    """Test behavior when no downloader can handle the reference."""
    coordinator = DownloadCoordinator(tmp_path)
    reference_no_ids = Reference(
        raw_text="Smith J. et al. (2023). Test paper.",
        first_author_last_name="Smith",
        year=2023,
    )

    with patch.object(coordinator, "_try_downloaders") as mock_try:
        mock_try.return_value = DownloadResult(
            reference=reference_no_ids,
            status=DownloadStatus.FAILED,
            source=DownloadSource.UNKNOWN,
            error_message="All download sources failed",
        )
        summary = coordinator.download_references([reference_no_ids])

    summary.calculate_stats()
    assert summary.total_references == 1
    assert summary.failed == 1
    result = summary.results[0]
    assert result.status == DownloadStatus.FAILED
    assert "All download sources failed" in result.error_message


def test_all_sources_fail(tmp_path: Path, test_reference: Reference) -> None:
    """Test behavior when all download sources fail."""
    coordinator = DownloadCoordinator(tmp_path)

    # Stub all downloaders to fail
    for downloader in coordinator.downloaders:
        downloader.can_download = MagicMock(return_value=True)
        downloader.download = MagicMock(
            return_value=DownloadResult(
                reference=test_reference,
                status=DownloadStatus.FAILED,
                source=downloader.get_source(),
                error_message="Downloader failed",
            )
        )

    result = coordinator._try_downloaders(test_reference, tmp_path / "test.pdf")

    assert result.status == DownloadStatus.FAILED
    assert "All download sources failed" in result.error_message


def test_sequential_downloads_processes_all(tmp_path: Path, test_reference: Reference) -> None:
    """Test that sequential downloads process all references."""
    coordinator = DownloadCoordinator(tmp_path)
    references = [test_reference, test_reference]

    with patch.object(coordinator, "_try_downloaders") as mock_try:
        mock_try.return_value = DownloadResult(
            reference=test_reference,
            status=DownloadStatus.SUCCESS,
            source=DownloadSource.DOI_RESOLVER,
            file_path=str(tmp_path / "paper.pdf"),
            file_size=1024,
        )
        summary = coordinator.download_references(references)

    summary.calculate_stats()
    assert len(summary.results) == 2
    for result in summary.results:
        assert result.status == DownloadStatus.SUCCESS


def test_successful_download_result_structure(tmp_path: Path, test_reference: Reference) -> None:
    """Test that successful downloads produce correct result structure."""
    coordinator = DownloadCoordinator(tmp_path)

    mock_result = DownloadResult(
        reference=test_reference,
        status=DownloadStatus.SUCCESS,
        source=DownloadSource.DOI_RESOLVER,
        file_path=str(tmp_path / "paper.pdf"),
        file_size=2048,
    )

    with (
        patch.object(coordinator.downloaders[0], "can_download", return_value=True),
        patch.object(coordinator.downloaders[0], "download", return_value=mock_result),
    ):
        result = coordinator._try_downloaders(test_reference, tmp_path / "test.pdf")

    assert result.status == DownloadStatus.SUCCESS
    assert result.file_path == str(tmp_path / "paper.pdf")
    assert result.file_size == 2048
    assert result.source == DownloadSource.DOI_RESOLVER
