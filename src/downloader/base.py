"""Base downloader class."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.models import Reference, DownloadResult, DownloadStatus, DownloadSource

logger = logging.getLogger(__name__)


class BaseDownloader(ABC):
    """Abstract base class for paper downloaders."""
    
    def __init__(self):
        self.timeout = 30
    
    @abstractmethod
    def can_download(self, reference: Reference) -> bool:
        """
        Check if this downloader can download the reference.
        
        Args:
            reference: Reference to check
            
        Returns:
            True if downloader can attempt to download
        """
        pass
    
    @abstractmethod
    def download(
        self,
        reference: Reference,
        output_path: Path
    ) -> Optional[DownloadResult]:
        """
        Download a paper for the given reference.
        
        Args:
            reference: Reference to download
            output_path: Path to save the PDF
            
        Returns:
            DownloadResult if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_source(self) -> DownloadSource:
        """Get the source type for this downloader."""
        pass
    
    def _save_pdf(self, content: bytes, output_path: Path) -> Optional[int]:
        """
        Save PDF content to file.
        
        Args:
            content: Binary content of PDF
            output_path: Path to save to
            
        Returns:
            File size if successful, None otherwise
        """
        try:
            # Verify it's a PDF
            if not content.startswith(b'%PDF'):
                logger.warning("Downloaded content is not a valid PDF")
                return None
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            logger.info(f"Saved PDF to {output_path} ({file_size} bytes)")
            return file_size
            
        except Exception as e:
            logger.error(f"Error saving PDF: {str(e)}")
            return None
    
    def _create_result(
        self,
        reference: Reference,
        status: DownloadStatus,
        file_path: Optional[str] = None,
        error_message: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> DownloadResult:
        """Create a DownloadResult object."""
        return DownloadResult(
            reference=reference,
            status=status,
            source=self.get_source(),
            file_path=file_path,
            error_message=error_message,
            file_size=file_size,
        )
