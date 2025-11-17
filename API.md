# API Reference

## Overview

This document describes the Python API for the Reference Extractor and Paper Downloader.

## Core Models

### Reference

Represents a bibliographic reference.

```python
from src.models import Reference

ref = Reference(
    raw_text: str,
    authors: List[str] = [],
    first_author_last_name: Optional[str] = None,
    title: Optional[str] = None,
    year: Optional[int] = None,
    journal: Optional[str] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    pages: Optional[str] = None,
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
    arxiv_id: Optional[str] = None,
    url: Optional[str] = None,
    publisher: Optional[str] = None,
    publication_type: Optional[str] = None,
)
```

**Methods:**

- `get_output_folder_name() -> str`: Returns folder name as `{FirstAuthorLastName}_{Year}`
- `get_filename() -> str`: Returns a sanitized filename for the paper

**Example:**
```python
ref = Reference(
    raw_text="Smith, J. et al. (2023). Paper Title.",
    authors=["Smith, J."],
    title="Paper Title",
    year=2023,
    doi="10.1234/example"
)

print(ref.get_output_folder_name())  # "Smith_2023"
print(ref.get_filename())  # "Smith_2023_Paper_Title"
```

### DownloadResult

Represents the result of a download attempt.

```python
from src.models import DownloadResult, DownloadStatus, DownloadSource

result = DownloadResult(
    reference: Reference,
    status: DownloadStatus,
    source: DownloadSource,
    file_path: Optional[str] = None,
    error_message: Optional[str] = None,
    file_size: Optional[int] = None,
)
```

**Status values:**
- `DownloadStatus.SUCCESS`: Paper downloaded successfully
- `DownloadStatus.FAILED`: Download failed
- `DownloadStatus.SKIPPED`: Download skipped (e.g., already exists)
- `DownloadStatus.NOT_FOUND`: Paper not found

**Source values:**
- `DownloadSource.DOI_RESOLVER`
- `DownloadSource.ARXIV`
- `DownloadSource.BIORXIV`
- `DownloadSource.CHEMRXIV`
- `DownloadSource.PUBMED`
- `DownloadSource.PUBMED_CENTRAL`
- `DownloadSource.SCIHUB`
- `DownloadSource.JOURNAL`

### DownloadSummary

Summary of download results.

```python
from src.models import DownloadSummary

summary = DownloadSummary(
    results: List[DownloadResult] = [],
    total_references: int = 0,
    successful: int = 0,
    failed: int = 0,
    skipped: int = 0,
    success_rate: float = 0.0,
)
```

**Methods:**

- `calculate_stats() -> None`: Calculate summary statistics

### ExtractionResult

Result of reference extraction.

```python
from src.models import ExtractionResult

result = ExtractionResult(
    source: str,
    references: List[Reference] = [],
    total_references: int = 0,
    extraction_errors: List[str] = [],
)
```

## Network Module

### HTTPClient

Centralized HTTP client with retry logic and User-Agent rotation.

```python
from src.network import HTTPClient

# Create HTTP client
client = HTTPClient(timeout=30)

# Perform GET request with automatic retry
response = client.get("https://example.com/page")
print(response.status_code)
print(response.text)

# With custom headers
response = client.get(
    "https://api.example.com/endpoint",
    headers={"X-API-Key": "your-key"}
)

# POST request
response = client.post(
    "https://api.example.com/submit",
    json={"key": "value"}
)

# Use as context manager
with HTTPClient() as client:
    response = client.get("https://example.com")
    print(response.text)
```

**Features:**

- **Automatic retry logic**: Retries on 403, 429, 500, 502, 503, 504 errors
- **User-Agent rotation**: Rotates through pool of browser User-Agents on 403 errors
- **Exponential backoff**: Increases delay between retries
- **Browser headers**: Sends realistic browser headers (Accept, Accept-Language, etc.)
- **Retry-After respect**: Honors Retry-After headers from servers
- **Debug logging**: Logs request attempts and responses at DEBUG level

**Parameters:**

- `timeout` (int, optional): Request timeout in seconds (defaults to `settings.TIMEOUT`)

**Methods:**

- `get(url, headers=None, allow_redirects=True, stream=False, **kwargs) -> requests.Response`: 
  - Perform GET request with retry logic
  - Automatically rotates User-Agent on 403 errors
  - Raises `requests.RequestException` on failure after all retries

- `post(url, data=None, json=None, headers=None, **kwargs) -> requests.Response`:
  - Perform POST request
  - Raises `requests.RequestException` on failure

- `close()`: Close the session (automatically called when used as context manager)

**Configuration (in `src/config.py`):**

- `MAX_RETRIES`: Number of retry attempts (default: 3)
- `RETRY_DELAY`: Base delay between retries in seconds (default: 2)
- `REQUEST_DELAY`: Delay between requests (default: 0.5)
- `USER_AGENT_POOL`: List of User-Agent strings to rotate (default: 6 browser variants)

**Example with 403 recovery:**

```python
from src.network import HTTPClient
import logging

# Enable debug logging to see retry attempts
logging.basicConfig(level=logging.DEBUG)

client = HTTPClient()

# This will automatically retry with fresh User-Agent if 403 is received
try:
    response = client.get("https://example.com/protected-page")
    print("Success!", response.status_code)
except Exception as e:
    print(f"Failed after retries: {e}")
```

## Extractor Module

### PDFExtractor

Extract references from PDF files with layout-aware parsing and configurable fallbacks.

```python
from src.extractor import PDFExtractor

# Enable fallbacks (default, uses settings.ENABLE_PDF_FALLBACKS)
extractor = PDFExtractor()

# Or explicitly control fallbacks
extractor = PDFExtractor(enable_fallbacks=True)  # Enable fallbacks
extractor = PDFExtractor(enable_fallbacks=False) # Disable fallbacks

# Extract references from a PDF
result = extractor.extract("paper.pdf")

print(f"Found {result.total_references} references")
for ref in result.references:
    print(f"  - {ref.title} ({ref.year})")
    if ref.doi:
        print(f"    DOI: {ref.doi}")
    if ref.metadata and 'extraction_method' in ref.metadata:
        print(f"    Source: {ref.metadata['extraction_method']}")
```

**Methods:**

- `extract(source: str) -> ExtractionResult`: Extract references from PDF file
- `__init__(enable_fallbacks: Optional[bool] = None)`: Initialize with optional fallback control

**Fallback Features:**
- **BibTeX Parser**: Extracts embedded BibTeX entries when detected
- **Table Extractor**: Handles tabular reference layouts  
- **Deduplication**: Prevents duplicate references across methods
- **Provenance Tracking**: Adds metadata to identify extraction method

**Configuration:**
Fallback behavior can be controlled via settings:
```python
# In src/config.py
ENABLE_PDF_FALLBACKS = True   # Master switch for PDF fallbacks
ENABLE_BIBTEX_FALLBACK = True # BibTeX parser
ENABLE_TABLE_FALLBACK = True  # Table extractor
```

### WebExtractor

Extract references from web pages with configurable HTML fallback.

```python
from src.extractor import WebExtractor

# Enable fallbacks (default, uses settings.ENABLE_WEB_FALLBACKS)
extractor = WebExtractor()

# Or explicitly control fallbacks
extractor = WebExtractor(enable_fallbacks=True)  # Enable fallbacks
extractor = WebExtractor(enable_fallbacks=False) # Disable fallbacks

# Extract references from a web page
result = extractor.extract("https://example.com/paper")

for ref in result.references:
    print(f"  - {ref.title}")
    if ref.metadata and 'extraction_method' in ref.metadata:
        print(f"    Source: {ref.metadata['extraction_method']}")
```

**Methods:**

- `extract(source: str) -> ExtractionResult`: Extract references from URL
- `__init__(enable_fallbacks: Optional[bool] = None)`: Initialize with optional fallback control

**Fallback Features:**
- **HTML Structure Parser**: Extracts from structured HTML (lists, divs, sections)
- **Reference Section Detection**: Finds reference sections by ID/class/heading
- **Deduplication**: Merges primary and fallback results without duplicates
- **Provenance Tracking**: Adds metadata to identify extraction method

**Configuration:**
Fallback behavior can be controlled via settings:
```python
# In src/config.py
ENABLE_WEB_FALLBACKS = True    # Master switch for web fallbacks
ENABLE_HTML_FALLBACK = True   # HTML structure parser
```

### ReferenceParser

Parse individual reference strings into structured Reference objects.

```python
from src.extractor import ReferenceParser

parser = ReferenceParser()

ref_text = "Smith, J., & Doe, J. (2023). Machine Learning Basics. AI Journal, 10(5), 1-20. DOI: 10.1234/example"

ref = parser.parse_reference(ref_text)

print(ref.authors)  # ["Smith, J.", "Doe, J."]
print(ref.title)    # "Machine Learning Basics"
print(ref.year)     # 2023
print(ref.doi)      # "10.1234/example"
```

**Methods:**

- `parse_reference(text: str) -> Optional[Reference]`: Parse a single reference string

## Downloader Module

### DownloadCoordinator

Orchestrate paper downloads with fallback strategy.

```python
from src.downloader import DownloadCoordinator
from pathlib import Path

coordinator = DownloadCoordinator(output_dir=Path("./downloads"))

# Download all references
summary = coordinator.download_references(references)

print(f"Downloaded: {summary.successful}/{summary.total_references}")
print(f"Success rate: {summary.success_rate:.1f}%")
```

**Methods:**

- `download_references(references: List[Reference]) -> DownloadSummary`: Download papers for all references

### Individual Downloaders

Each downloader can be used independently:

```python
from src.downloader.doi_resolver import DOIResolver
from src.downloader.arxiv import ArxivDownloader
from src.downloader.pubmed import PubMedDownloader
from src.downloader.scihub import SciHubDownloader
from pathlib import Path

# Create downloader
downloader = DOIResolver()

# Check if it can handle this reference
if downloader.can_download(reference):
    # Download
    result = downloader.download(reference, Path("output.pdf"))
    
    if result.status == "success":
        print(f"Downloaded to {result.file_path}")
```

**Common Methods:**

- `can_download(reference: Reference) -> bool`: Check if downloader can handle this reference
- `download(reference: Reference, output_path: Path) -> Optional[DownloadResult]`: Download the paper

## Report Module

### ReportGenerator

Generate summary reports for download results.

```python
from src.report import ReportGenerator
from pathlib import Path

reporter = ReportGenerator(output_dir=Path("./downloads"))

# Generate all report formats
reporter.generate_reports(summary, report_name="my_report")

# Or generate specific formats
text_path = reporter.generate_text_report(summary)
json_path = reporter.generate_json_report(summary)
```

**Methods:**

- `generate_reports(summary: DownloadSummary, report_name: str) -> None`: Generate all report formats
- `generate_text_report(summary: DownloadSummary, report_name: str) -> Path`: Generate text report
- `generate_json_report(summary: DownloadSummary, report_name: str) -> Path`: Generate JSON report

## Utility Functions

### Reference Extraction Utilities

```python
from src.utils import (
    extract_doi,
    extract_pmid,
    extract_year,
    extract_urls,
    extract_page_range,
)

text = "Smith et al. (2023). DOI: 10.1234/example. Pages 123-145."

doi = extract_doi(text)           # "10.1234/example"
year = extract_year(text)         # 2023
pages = extract_page_range(text)  # "123-145"
urls = extract_urls(text)         # []
```

### Author Utilities

```python
from src.utils import (
    parse_author_string,
    extract_last_name,
)

author_str = "Smith, J. and Doe, J. and Brown, M."
authors = parse_author_string(author_str)  # ["Smith, J.", "Doe, J.", "Brown, M."]

last_name = extract_last_name("Smith, John")  # "Smith"
```

### File Utilities

```python
from src.utils import (
    sanitize_filename,
    ensure_dir,
    get_file_size,
    is_valid_pdf,
)
from pathlib import Path

# Sanitize filename for filesystem
clean_name = sanitize_filename("My:Paper|Name")  # "My_Paper_Name"

# Ensure directory exists
path = ensure_dir(Path("./downloads/papers"))

# Check file
size = get_file_size(Path("paper.pdf"))  # bytes
is_pdf = is_valid_pdf(Path("paper.pdf"))  # True/False
```

### Logging

```python
from src.utils import setup_logging
from pathlib import Path

logger = setup_logging(log_file=Path("./app.log"))

logger.info("Application started")
logger.warning("This is a warning")
logger.error("An error occurred")
```

## Configuration

### Settings

Access and modify settings:

```python
from src.config import settings

# View settings
print(settings.TIMEOUT)
print(settings.OUTPUT_DIR)
print(settings.ENABLE_SCIHUB)

# Modify settings
settings.TIMEOUT = 60
settings.ENABLE_SCIHUB = False
settings.REQUEST_DELAY = 1.0
```

**Available Settings:**

- `OUTPUT_DIR`: Output directory for downloads (default: `./downloads`)
- `TIMEOUT`: HTTP request timeout in seconds (default: 30)
- `MAX_RETRIES`: Number of retry attempts (default: 3)
- `REQUEST_DELAY`: Delay between requests in seconds (default: 0.5)
- `ARXIV_DELAY`: Delay for arXiv requests in seconds (default: 3)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 100 MB)
- `USER_AGENT`: HTTP User-Agent header
- `ENABLE_SCIHUB`: Enable Sci-Hub downloads (default: True)
- `ENABLE_PUBMED`: Enable PubMed downloads (default: True)
- `ENABLE_ARXIV`: Enable arXiv downloads (default: True)
- `ENABLE_BIORXIV`: Enable bioRxiv downloads (default: True)
- `ENABLE_CHEMRXIV`: Enable chemRxiv downloads (default: True)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Examples

### Complete Workflow

```python
from src.extractor import PDFExtractor
from src.downloader import DownloadCoordinator
from src.report import ReportGenerator
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# 1. Extract
extractor = PDFExtractor()
extraction = extractor.extract("paper.pdf")

print(f"Extracted {extraction.total_references} references")

# 2. Download
output_dir = Path("./downloads")
coordinator = DownloadCoordinator(output_dir)
summary = coordinator.download_references(extraction.references)

# 3. Report
reporter = ReportGenerator(output_dir)
reporter.generate_reports(summary)

# 4. Results
print(f"Success: {summary.successful}")
print(f"Failed: {summary.failed}")
print(f"Success Rate: {summary.success_rate:.1f}%")
```

### Working with Individual References

```python
from src.models import Reference
from src.downloader.doi_resolver import DOIResolver
from pathlib import Path

# Create a reference
ref = Reference(
    raw_text="Test paper",
    title="Machine Learning Basics",
    year=2023,
    doi="10.1234/example"
)

# Download it
downloader = DOIResolver()
output_path = Path("paper.pdf")

result = downloader.download(ref, output_path)

if result.status == "success":
    print(f"Downloaded: {result.file_path}")
    print(f"Size: {result.file_size} bytes")
else:
    print(f"Error: {result.error_message}")
```

### Filtering References

```python
from src.extractor import PDFExtractor
from src.downloader import DownloadCoordinator
from pathlib import Path

extractor = PDFExtractor()
result = extractor.extract("paper.pdf")

# Filter: only papers from 2020+
recent = [r for r in result.references if r.year and r.year >= 2020]

# Filter: only papers with DOI
with_doi = [r for r in result.references if r.doi]

# Filter: only biomedical papers
biomedical_keywords = ["gene", "protein", "disease", "clinical", "medical"]
biomedical = [
    r for r in result.references
    if any(kw in (r.journal or "").lower() for kw in biomedical_keywords)
]

# Download filtered set
coordinator = DownloadCoordinator(Path("./downloads"))
summary = coordinator.download_references(biomedical)
```

## Error Handling

All methods are designed to handle errors gracefully:

```python
from src.extractor import PDFExtractor
from src.models import ExtractionResult

extractor = PDFExtractor()

# Errors are captured in result
result = extractor.extract("nonexistent.pdf")

if result.extraction_errors:
    for error in result.extraction_errors:
        print(f"Error: {error}")

if result.total_references == 0:
    print("No references were extracted")
else:
    for ref in result.references:
        print(f"  - {ref.title}")
```

## Performance Considerations

### Optimization Tips

1. **Use appropriate timeout**: Longer timeout for slow networks
2. **Batch processing**: Process multiple PDFs at once
3. **Filter references**: Download only needed papers
4. **Disable slow sources**: Skip Sci-Hub if speed is critical
5. **Cache results**: Store successful downloads to avoid re-downloading

### Rate Limiting

The application respects rate limits:

```python
from src.config import settings

# Adjust for your use case
settings.REQUEST_DELAY = 0.5      # Delay between requests
settings.ARXIV_DELAY = 3          # Delay for arXiv API
settings.TIMEOUT = 30             # Request timeout
```

## Thread Safety

The extractors and downloaders are **not** thread-safe. For parallel processing:

```python
from concurrent.futures import ThreadPoolExecutor
from src.extractor import PDFExtractor
import threading

lock = threading.Lock()

def extract_paper(pdf_path):
    extractor = PDFExtractor()  # Create new instance per thread
    with lock:  # Protect shared resources if needed
        return extractor.extract(pdf_path)

# Use with executor
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(extract_paper, pdf_files)
```
