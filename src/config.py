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

    # User agent pool for rotation (reduces 403 errors)
    USER_AGENT_POOL: list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    # Feature flags
    ENABLE_SCIHUB: bool = True
    ENABLE_PUBMED: bool = True
    ENABLE_ARXIV: bool = True
    ENABLE_BIORXIV: bool = True
    ENABLE_CHEMRXIV: bool = True
    ENABLE_OPEN_ACCESS: bool = True

    # Fallback extraction settings
    ENABLE_PDF_FALLBACKS: bool = True
    ENABLE_TABLE_FALLBACK: bool = True
    ENABLE_BIBTEX_FALLBACK: bool = True
    ENABLE_HTML_STRUCTURE_FALLBACK: bool = True
    FALLBACK_MIN_REFERENCE_THRESHOLD: int = 3

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
