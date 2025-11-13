"""Utility functions for the reference downloader."""

import logging
import re
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.config import settings


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Set up logging configuration."""
    if log_file is None:
        log_file = settings.LOG_FILE
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("ref_downloader")
    logger.setLevel(settings.LOG_LEVEL)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(settings.LOG_LEVEL)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(settings.LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger


def extract_doi(text: str) -> Optional[str]:
    """Extract DOI from text."""
    # Match patterns like 10.xxxx/xxxxx
    doi_pattern = r'10\.\d{4,}/\S+'
    match = re.search(doi_pattern, text)
    if match:
        doi = match.group(0).rstrip('.,;:)')
        return doi
    return None


def extract_pmid(text: str) -> Optional[str]:
    """Extract PubMed ID from text."""
    # Look for PMID: followed by digits
    pmid_pattern = r'PMID:\s*(\d+)'
    match = re.search(pmid_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_year(text: str) -> Optional[int]:
    """Extract year from text."""
    year_pattern = r'\b(19|20)\d{2}\b'
    match = re.search(year_pattern, text)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            return None
    return None


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)
    return [url.rstrip('.,;:)') for url in urls]


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize a string to be used as a filename."""
    # Replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    if file_path.exists():
        return file_path.stat().st_size
    return 0


def is_valid_pdf(file_path: Path) -> bool:
    """Check if file is a valid PDF."""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except Exception:
        return False


def parse_author_string(author_string: str) -> List[str]:
    """Parse a comma or 'and' separated author string into individual authors."""
    if not author_string:
        return []
    
    # First try to split by 'and'
    if ' and ' in author_string.lower():
        authors = re.split(r'\s+and\s+', author_string, flags=re.IGNORECASE)
    else:
        # Try comma separation
        authors = author_string.split(',')
    
    # Clean up each author
    authors = [a.strip() for a in authors if a.strip()]
    return authors


def extract_last_name(author_name: str) -> Optional[str]:
    """Extract last name from an author name."""
    if not author_name:
        return None
    
    # Simple heuristic: last word is usually the last name
    parts = author_name.strip().split()
    if parts:
        return parts[-1]
    return None


def format_page_range(start: Optional[int], end: Optional[int]) -> Optional[str]:
    """Format a page range."""
    if start is None:
        return None
    if end is None:
        return str(start)
    return f"{start}-{end}"


def extract_page_range(text: str) -> Optional[str]:
    """Extract page range from text."""
    # Look for patterns like "pp. 123-145" or "123-145"
    page_pattern = r'(?:pp\.\s*)?(\d+)\s*[-–]\s*(\d+)'
    match = re.search(page_pattern, text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # Single page
    single_pattern = r'(?:pp\.\s*)?(\d+)\b'
    match = re.search(single_pattern, text)
    if match:
        return match.group(1)
    
    return None


def get_timestamp_str() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
