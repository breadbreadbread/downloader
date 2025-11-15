"""DOI resolver for fetching papers via DOI."""

import logging
from pathlib import Path
from typing import Optional

from src.downloader.base import BaseDownloader
from src.http_client import HTTPClient, HTTPClientError
from src.models import Reference, DownloadResult, DownloadStatus, DownloadSource

logger = logging.getLogger(__name__)


class DOIResolver(BaseDownloader):
    """Resolve and download papers using DOI."""
    
    def __init__(self, http_client: Optional[HTTPClient] = None):
        super().__init__(http_client=http_client)
    
    def can_download(self, reference: Reference) -> bool:
        """Check if reference has a DOI."""
        return reference.doi is not None
    
    def download(
        self,
        reference: Reference,
        output_path: Path
    ) -> Optional[DownloadResult]:
        """Download using DOI resolution."""
        if not reference.doi:
            return self._create_result(
                reference,
                DownloadStatus.SKIPPED,
                error_message="No DOI available"
            )
        
        try:
            pdf_url = self._get_pdf_url_from_doi(reference.doi)
        except HTTPClientError as exc:
            logger.error("Error resolving DOI %s: %s", reference.doi, exc)
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"DOI resolution failed: {exc}"
            )
        except Exception as exc:
            logger.error("Error resolving DOI %s: %s", reference.doi, exc)
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"DOI resolution failed: {str(exc)}"
            )

        if pdf_url:
            logger.info(f"Found PDF URL for DOI {reference.doi}: {pdf_url}")
            return self._download_from_url(reference, pdf_url, output_path)

        return self._create_result(
            reference,
            DownloadStatus.NOT_FOUND,
            error_message="No direct PDF URL found in DOI metadata"
        )
    
    def get_source(self) -> DownloadSource:
        """Get source type."""
        return DownloadSource.DOI_RESOLVER
    
    def _get_pdf_url_from_doi(self, doi: str) -> Optional[str]:
        """
        Get PDF URL from DOI metadata via CrossRef.
        
        Args:
            doi: DOI identifier
            
        Returns:
            PDF URL if found, None otherwise
        """
        url = f"https://api.crossref.org/works/{doi}"
        response = self.http_client.get(url, timeout=self.timeout, verify=True)

        try:
            data = response.json()
        except ValueError as exc:
            logger.debug("Invalid JSON from CrossRef for DOI %s: %s", doi, exc)
            return None

        if data.get('status') != 'ok':
            return None

        message = data.get('message', {})

        # Check for direct link to PDF
        if 'link' in message:
            for link in message['link']:
                if link.get('content-type', '').lower() == 'application/pdf':
                    return link.get('URL')

        # Check publisher information
        if 'publisher' in message:
            logger.debug(f"Publisher: {message['publisher']}")

        # Some publishers provide content-urls
        if 'URL' in message:
            return message['URL']

        return None
    
    def _download_from_url(
        self,
        reference: Reference,
        url: str,
        output_path: Path
    ) -> DownloadResult:
        """Download PDF from URL."""
        try:
            response = self.http_client.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
                verify=True,
            )

            content = response.content
            file_size = self._save_pdf(content, output_path)
            
            if file_size:
                return self._create_result(
                    reference,
                    DownloadStatus.SUCCESS,
                    file_path=str(output_path),
                    file_size=file_size
                )
            else:
                return self._create_result(
                    reference,
                    DownloadStatus.FAILED,
                    error_message="Invalid PDF content"
                )
        
        except HTTPClientError as exc:
            logger.error("Error downloading from %s: %s", url, exc)
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"Download failed: {exc}"
            )
        except Exception as e:
            logger.error(f"Error downloading from {url}: {str(e)}")
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"Download failed: {str(e)}"
            )
