"""arXiv, bioRxiv, and chemRxiv downloader."""

import logging
import time
from pathlib import Path
from typing import Optional

from src.config import settings
from src.downloader.base import BaseDownloader
from src.http_client import HTTPClient, HTTPClientError
from src.models import Reference, DownloadResult, DownloadStatus, DownloadSource

logger = logging.getLogger(__name__)


class ArxivDownloader(BaseDownloader):
    """Download papers from arXiv, bioRxiv, and chemRxiv."""
    
    def __init__(self, http_client: Optional[HTTPClient] = None):
        super().__init__(http_client=http_client)
    
    def can_download(self, reference: Reference) -> bool:
        """Check if reference is from arXiv or related preprint server."""
        if reference.arxiv_id:
            return True
        
        # Check if URL is from preprint servers
        if reference.url:
            return any(x in reference.url for x in [
                'arxiv.org',
                'biorxiv.org',
                'chemrxiv.org'
            ])
        
        return False
    
    def download(
        self,
        reference: Reference,
        output_path: Path
    ) -> Optional[DownloadResult]:
        """Download from arXiv or related preprint servers."""
        try:
            # Try arXiv first if we have an ID
            if reference.arxiv_id:
                result = self._download_from_arxiv(reference, output_path)
                if result and result.status == DownloadStatus.SUCCESS:
                    return result
            
            # Try from URL if available
            if reference.url:
                result = self._download_from_url(reference, output_path)
                if result and result.status == DownloadStatus.SUCCESS:
                    return result
            
            return self._create_result(
                reference,
                DownloadStatus.NOT_FOUND,
                error_message="Could not find preprint"
            )
        
        except Exception as e:
            logger.error(f"Error downloading preprint: {str(e)}")
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"Preprint download failed: {str(e)}"
            )
    
    def get_source(self) -> DownloadSource:
        """Get source type."""
        return DownloadSource.ARXIV
    
    def _download_from_arxiv(
        self,
        reference: Reference,
        output_path: Path
    ) -> Optional[DownloadResult]:
        """Download from arXiv using arxiv ID."""
        try:
            arxiv_id = reference.arxiv_id
            
            # Construct PDF URL
            # Old format: YYMM.NNNNN -> arxiv/pdf/YYMM.NNNNN.pdf
            # New format: YYMM.NNNNN -> arxiv/pdf/YYMM.NNNNN.pdf
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            logger.info(f"Downloading from arXiv: {pdf_url}")
            
            response = self.http_client.get(
                pdf_url,
                timeout=self.timeout,
                allow_redirects=True,
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
            logger.warning("Error downloading arXiv paper: %s", exc)
            return None
        except Exception as e:
            logger.warning(f"Error downloading arXiv paper: {str(e)}")
            return None
    
    def _download_from_url(
        self,
        reference: Reference,
        output_path: Path
    ) -> Optional[DownloadResult]:
        """Download from preprint server URL."""
        if not reference.url:
            return None
        
        try:
            # Normalize URL to PDF
            url = reference.url
            
            # Handle different preprint servers
            if 'arxiv.org' in url:
                # Convert abstract URL to PDF URL
                if '/abs/' in url:
                    url = url.replace('/abs/', '/pdf/') + '.pdf'
                elif not url.endswith('.pdf'):
                    url = url + '.pdf'
            
            elif 'biorxiv.org' in url or 'medrxiv.org' in url:
                # bioRxiv/medRxiv format: add /download at end
                if not url.endswith('.full.pdf'):
                    url = url.rstrip('/') + '.full.pdf'
            
            elif 'chemrxiv.org' in url:
                # chemRxiv format
                if 'download' not in url:
                    url = url + '/download'
            
            logger.info(f"Downloading from URL: {url}")
            
            # Rate limiting for preprint servers
            time.sleep(settings.ARXIV_DELAY)
            
            response = self.http_client.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
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
            logger.warning("Error downloading from preprint URL: %s", exc)
            return None
        except Exception as e:
            logger.warning(f"Error downloading from preprint URL: {str(e)}")
            return None
