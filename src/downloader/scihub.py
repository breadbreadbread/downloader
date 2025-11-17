"""Sci-Hub downloader."""

import logging
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.config import settings
from src.downloader.base import BaseDownloader
from src.models import DownloadResult, DownloadSource, DownloadStatus, Reference
from src.network.http_client import HTTPClient

logger = logging.getLogger(__name__)


class SciHubDownloader(BaseDownloader):
    """Download papers from Sci-Hub."""

    def __init__(self):
        super().__init__()
        self.http_client = HTTPClient()
        self.scihub_urls = settings.SCIHUB_URLS

    def can_download(self, reference: Reference) -> bool:
        """Check if reference has enough info for Sci-Hub search."""
        return (reference.doi or reference.title) is not None

    def download(
        self, reference: Reference, output_path: Path
    ) -> Optional[DownloadResult]:
        """Download from Sci-Hub."""
        if not settings.ENABLE_SCIHUB:
            return self._create_result(
                reference,
                DownloadStatus.SKIPPED,
                error_message="Sci-Hub disabled in settings",
            )

        try:
            # Try each Sci-Hub mirror
            for scihub_url in self.scihub_urls:
                result = self._try_scihub_mirror(reference, scihub_url, output_path)
                if result and result.status == DownloadStatus.SUCCESS:
                    return result

                # Rate limiting between mirrors
                time.sleep(settings.REQUEST_DELAY)

            return self._create_result(
                reference,
                DownloadStatus.NOT_FOUND,
                error_message="Not found in Sci-Hub mirrors",
            )

        except Exception as e:
            logger.error(f"Error accessing Sci-Hub: {str(e)}")
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"Sci-Hub download failed: {str(e)}",
            )

    def get_source(self) -> DownloadSource:
        """Get source type."""
        return DownloadSource.SCIHUB

    def _try_scihub_mirror(
        self, reference: Reference, scihub_url: str, output_path: Path
    ) -> Optional[DownloadResult]:
        """Try to download from a specific Sci-Hub mirror."""
        try:
            # Prepare search query
            query = None
            if reference.doi:
                query = reference.doi
            elif reference.title:
                query = reference.title
            else:
                return None

            # Search on Sci-Hub
            search_url = f"{scihub_url}/?q={query}"
            logger.info(f"Searching Sci-Hub mirror {scihub_url} for: {query}")

            response = self.http_client.get(search_url, allow_redirects=True)

            # Parse response to find PDF link
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for PDF links
            pdf_link = self._extract_pdf_link(soup, scihub_url)

            if pdf_link:
                logger.info(f"Found PDF link: {pdf_link}")
                return self._download_pdf(reference, pdf_link, output_path)

            return None

        except requests.RequestException as e:
            logger.debug(f"Error with Sci-Hub mirror {scihub_url}: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing Sci-Hub response: {str(e)}")
            return None

    def _extract_pdf_link(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract PDF link from Sci-Hub page."""
        # Common patterns in Sci-Hub response

        # Look for iframe with PDF
        iframe = soup.find("iframe", {"id": "pdfDocument"})
        if iframe and iframe.get("src"):
            pdf_url = iframe["src"]
            if pdf_url.startswith("http"):
                return pdf_url
            else:
                return base_url.rstrip("/") + pdf_url

        # Look for direct PDF link
        pdf_links = soup.find_all("a", href=lambda x: x and ".pdf" in x.lower())
        if pdf_links:
            pdf_url = pdf_links[0]["href"]
            if pdf_url.startswith("http"):
                return pdf_url
            else:
                return base_url.rstrip("/") + pdf_url

        # Look for download button
        download_btn = soup.find("a", {"id": "pdf"})
        if download_btn and download_btn.get("href"):
            pdf_url = download_btn["href"]
            if pdf_url.startswith("http"):
                return pdf_url
            else:
                return base_url.rstrip("/") + pdf_url

        return None

    def _download_pdf(
        self, reference: Reference, pdf_url: str, output_path: Path
    ) -> Optional[DownloadResult]:
        """Download PDF from URL."""
        try:
            response = self.http_client.get(pdf_url, allow_redirects=True)

            content = response.content
            file_size = self._save_pdf(content, output_path)

            if file_size:
                return self._create_result(
                    reference,
                    DownloadStatus.SUCCESS,
                    file_path=str(output_path),
                    file_size=file_size,
                )
            else:
                return self._create_result(
                    reference,
                    DownloadStatus.FAILED,
                    error_message="Invalid PDF content",
                )

        except Exception as e:
            logger.warning(f"Error downloading PDF from {pdf_url}: {str(e)}")
            return None
