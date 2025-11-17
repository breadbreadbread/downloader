"""Data models for references and download results."""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class DownloadSource(str, Enum):
    """Supported download sources."""
    OPEN_ACCESS = "open_access"
    DOI_RESOLVER = "doi_resolver"
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    CHEMRXIV = "chemrxiv"
    PUBMED = "pubmed"
    PUBMED_CENTRAL = "pubmed_central"
    SCIHUB = "scihub"
    JOURNAL = "journal"
    UNKNOWN = "unknown"


class DownloadStatus(str, Enum):
    """Status of download attempt."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_FOUND = "not_found"


class Reference(BaseModel):
    """Represents a bibliographic reference."""
    
    raw_text: str = Field(..., description="Raw extracted text")
    
    # Core fields
    authors: List[str] = Field(default_factory=list, description="List of author names")
    first_author_last_name: Optional[str] = Field(None, description="Last name of first author")
    title: Optional[str] = Field(None, description="Paper/article title")
    year: Optional[int] = Field(None, description="Publication year")
    
    # Publication details
    journal: Optional[str] = Field(None, description="Journal/venue name")
    volume: Optional[str] = Field(None, description="Journal volume")
    issue: Optional[str] = Field(None, description="Journal issue")
    pages: Optional[str] = Field(None, description="Page range (e.g., '123-145')")
    
    # Identifiers
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    arxiv_id: Optional[str] = Field(None, description="arXiv identifier")
    url: Optional[str] = Field(None, description="URL to paper")
    
    # Additional metadata
    publisher: Optional[str] = Field(None, description="Publisher name")
    publication_type: Optional[str] = Field(None, description="Type (journal, conference, book, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (e.g., extraction method)")
    
    def get_output_folder_name(self) -> str:
        """Get the output folder name based on first author and year."""
        if self.first_author_last_name and self.year:
            return f"{self.first_author_last_name}_{self.year}"
        elif self.first_author_last_name:
            return self.first_author_last_name
        else:
            return "Unknown"
    
    def get_filename(self) -> str:
        """Get a reasonable filename for the paper."""
        parts = []
        if self.first_author_last_name:
            parts.append(self.first_author_last_name)
        if self.year:
            parts.append(str(self.year))
        if self.title:
            # Sanitize title for filename
            sanitized_title = "".join(c for c in self.title if c.isalnum() or c in (' ', '-', '_')).strip()
            sanitized_title = sanitized_title[:50]  # Limit length
            parts.append(sanitized_title)
        
        return "_".join(parts) if parts else "paper"


class DownloadResult(BaseModel):
    """Result of a download attempt."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    reference: Reference
    status: DownloadStatus
    source: DownloadSource
    file_path: Optional[str] = Field(None, description="Path to downloaded file")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    file_size: Optional[int] = Field(None, description="Size of downloaded file in bytes")


class ExtractionResult(BaseModel):
    """Result of reference extraction."""
    
    source: str = Field(..., description="Source (file path or URL)")
    references: List[Reference] = Field(default_factory=list, description="Extracted references")
    total_references: int = Field(0, description="Total references found")
    extraction_errors: List[str] = Field(default_factory=list, description="Extraction errors")


class DownloadSummary(BaseModel):
    """Summary of download results."""
    
    results: List[DownloadResult] = Field(default_factory=list, description="All download results")
    total_references: int = Field(0, description="Total references attempted")
    successful: int = Field(0, description="Successfully downloaded")
    failed: int = Field(0, description="Failed to download")
    skipped: int = Field(0, description="Skipped")
    success_rate: float = Field(0.0, description="Success rate percentage")
    
    def calculate_stats(self) -> None:
        """Calculate summary statistics."""
        self.total_references = len(self.results)
        self.successful = len([r for r in self.results if r.status == DownloadStatus.SUCCESS])
        self.failed = len([r for r in self.results if r.status == DownloadStatus.FAILED])
        self.skipped = len([r for r in self.results if r.status == DownloadStatus.SKIPPED])
        
        if self.total_references > 0:
            self.success_rate = (self.successful / self.total_references) * 100
        else:
            self.success_rate = 0.0
