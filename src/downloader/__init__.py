"""Paper downloader module."""

from .base import BaseDownloader
from .coordinator import DownloadCoordinator

__all__ = [
    "BaseDownloader",
    "DownloadCoordinator",
]
