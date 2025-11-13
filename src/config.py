"""Configuration settings for the reference downloader."""

from pathlib import Path
from typing import Optional


class Settings:
    """Application settings."""
    
    # Paths
    OUTPUT_DIR: Path = Path("./downloads")
    CACHE_DIR: Path = Path("./.cache")
    LOG_FILE: Optional[Path] = Path("./ref_downloader.log")
    
    # Download settings
    TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # seconds
    
    # Rate limiting
    REQUEST_DELAY: float = 0.5  # seconds between requests
    ARXIV_DELAY: float = 3  # seconds between arXiv requests (API requirement)
    
    # File settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
    
    # API keys (optional)
    PUBMED_API_KEY: Optional[str] = None
    CROSSREF_EMAIL: str = "user@example.com"  # Required by Crossref API
    
    # User agent
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Feature flags
    ENABLE_SCIHUB: bool = True
    ENABLE_PUBMED: bool = True
    ENABLE_ARXIV: bool = True
    ENABLE_BIORXIV: bool = True
    ENABLE_CHEMRXIV: bool = True
    ENABLE_OPEN_ACCESS: bool = True
    
    # Sci-Hub settings
    SCIHUB_URLS: list = [
        "https://www.sci-hub.se",
        "https://sci-hub.ren",
        "https://sci-hub.ru",
    ]
    
    # arXiv settings
    ARXIV_MIRRORS: list = [
        "https://arxiv.org",
        "https://arxiv-export-lb.library.cornell.edu/oai2",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False


# Global settings instance
settings = Settings()
