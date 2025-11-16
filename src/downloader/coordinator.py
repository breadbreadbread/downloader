"""Download coordinator that orchestrates paper downloads from multiple sources."""

import logging
import time
from pathlib import Path
from typing import List

from src.config import settings
from src.downloader.arxiv import ArxivDownloader
from src.downloader.base import BaseDownloader
from src.downloader.doi_resolver import DOIResolver
from src.downloader.pubmed import PubMedDownloader
from src.downloader.scihub import SciHubDownloader
from src.models import DownloadResult, DownloadStatus, DownloadSummary, Reference

logger = logging.getLogger(__name__)


class DownloadCoordinator:
    """Coordinate downloads from multiple sources with fallback strategy."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize downloaders in priority order
        self.downloaders: List[BaseDownloader] = [
            DOIResolver(),
            ArxivDownloader(),
            PubMedDownloader(),
            SciHubDownloader(),
        ]

    def download_references(self, references: List[Reference]) -> DownloadSummary:
        """
        Download papers for all references.

        Args:
            references: List of references to download

        Returns:
            DownloadSummary with results
        """
        summary = DownloadSummary()

        for idx, reference in enumerate(references, 1):
            logger.info(f"Processing reference {idx}/{len(references)}")

            # Get output folder for this reference
            folder_name = reference.get_output_folder_name()
            output_folder = self.output_dir / folder_name
            output_folder.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = reference.get_filename()
            output_path = output_folder / f"{filename}.pdf"

            # Skip if already downloaded
            if output_path.exists():
                logger.info(f"File already exists: {output_path}")
                result = DownloadResult(
                    reference=reference,
                    status=DownloadStatus.SKIPPED,
                    source=None,
                    file_path=str(output_path),
                    file_size=output_path.stat().st_size,
                )
                summary.results.append(result)
                continue

            # Try each downloader
            result = self._try_downloaders(reference, output_path)
            summary.results.append(result)

            # Rate limiting
            time.sleep(settings.REQUEST_DELAY)

        # Calculate statistics
        summary.calculate_stats()

        return summary

    def _try_downloaders(
        self, reference: Reference, output_path: Path
    ) -> DownloadResult:
        """Try downloading with each downloader in priority order."""

        for downloader in self.downloaders:
            try:
                if not downloader.can_download(reference):
                    logger.debug(
                        f"Downloader {downloader.__class__.__name__} "
                        f"cannot handle this reference"
                    )
                    continue

                logger.info(f"Attempting download with {downloader.__class__.__name__}")

                result = downloader.download(reference, output_path)

                if result:
                    if result.status == DownloadStatus.SUCCESS:
                        logger.info(f"Successfully downloaded: {output_path}")
                        return result
                    elif result.status == DownloadStatus.FAILED:
                        logger.warning(f"Download failed: {result.error_message}")
                        continue
                    elif result.status == DownloadStatus.NOT_FOUND:
                        logger.debug(f"Not found: {result.error_message}")
                        continue

            except Exception as e:
                logger.error(f"Error with {downloader.__class__.__name__}: {str(e)}")
                continue

        # All downloaders failed
        logger.warning(f"Failed to download paper for reference: {reference.title}")

        return DownloadResult(
            reference=reference,
            status=DownloadStatus.FAILED,
            source=None,
            error_message="All download sources failed",
        )
