# Usage Examples

This document provides practical examples of how to use the Reference Extractor and Paper Downloader.

## Basic Examples

### 1. Extract from PDF and Download Papers

```bash
python -m src.main --pdf paper.pdf --output ./downloads
```

This will:
1. Extract references from `paper.pdf`
2. Attempt to download each referenced paper from multiple sources
3. Save papers to `./downloads/[FirstAuthor]_[Year]/`
4. Generate summary reports

### 2. Extract from Web Page

```bash
python -m src.main --url https://example.com/research-paper --output ./papers
```

### 3. Only Extract References (No Download)

```bash
python -m src.main --pdf research.pdf --skip-download --output ./refs
```

This is useful if you only want to see what references are found without downloading.

## Advanced Usage

### Using from Python Code

```python
from src.extractor import PDFExtractor
from src.downloader import DownloadCoordinator
from src.report import ReportGenerator
from pathlib import Path

# Extract references
extractor = PDFExtractor()
result = extractor.extract("paper.pdf")

print(f"Found {result.total_references} references")

# Download papers
coordinator = DownloadCoordinator(output_dir=Path("./downloads"))
summary = coordinator.download_references(result.references)

# Generate reports
reporter = ReportGenerator(output_dir=Path("./downloads"))
reporter.generate_reports(summary)

# Access results
print(f"Downloaded: {summary.successful}")
print(f"Failed: {summary.failed}")
print(f"Success rate: {summary.success_rate:.1f}%")
```

### Working with Reference Objects

```python
from src.models import Reference

# Create a reference
ref = Reference(
    raw_text="Smith, J. et al. (2023). Paper Title. Journal, 10(5), 1-20.",
    authors=["Smith, J."],
    title="Paper Title",
    year=2023,
    journal="Journal",
    doi="10.1234/example"
)

# Access properties
print(ref.first_author_last_name)  # "Smith"
print(ref.get_output_folder_name())  # "Smith_2023"
print(ref.get_filename())  # "Smith_2023_Paper_Title.pdf"
```

### Customizing Download Sources

```python
from src.downloader.coordinator import DownloadCoordinator
from src.downloader.arxiv import ArxivDownloader
from src.downloader.doi_resolver import DOIResolver

# Create coordinator with specific downloaders
coordinator = DownloadCoordinator()

# You can modify the downloaders list to change priority
coordinator.downloaders = [
    DOIResolver(),          # Try DOI first
    ArxivDownloader(),      # Then arXiv
    # SciHubDownloader(),   # Commented out for now
]

# Download with custom configuration
summary = coordinator.download_references(references)
```

## Example Workflow

### Comprehensive Research Paper Analysis

```python
import logging
from pathlib import Path
from src.extractor import PDFExtractor
from src.downloader import DownloadCoordinator
from src.report import ReportGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Extract from a research paper
logger.info("Step 1: Extracting references from paper...")
extractor = PDFExtractor()
extraction_result = extractor.extract("literature_review.pdf")

logger.info(f"Found {extraction_result.total_references} references")

# 2. Filter references (optional)
# Only download papers from 2020 onwards
recent_refs = [
    ref for ref in extraction_result.references
    if ref.year and ref.year >= 2020
]
logger.info(f"Filtering to {len(recent_refs)} papers from 2020+")

# 3. Download papers
logger.info("Step 2: Downloading papers...")
coordinator = DownloadCoordinator(output_dir=Path("./downloaded_papers"))
summary = coordinator.download_references(recent_refs)

# 4. Generate report
logger.info("Step 3: Generating reports...")
reporter = ReportGenerator(output_dir=Path("./downloaded_papers"))
reporter.generate_reports(summary, report_name="literature_review_summary")

# 5. Summary
logger.info("=" * 60)
logger.info(f"Total references: {summary.total_references}")
logger.info(f"Successfully downloaded: {summary.successful}")
logger.info(f"Failed: {summary.failed}")
logger.info(f"Success rate: {summary.success_rate:.1f}%")
logger.info("=" * 60)
```

## Output Examples

### Directory Structure

After running the downloader, your output directory will look like:

```
downloads/
├── Smith_2022/
│   ├── Smith_2022_Deep_Learning.pdf
│   └── Smith_2022_Neural_Networks.pdf
├── Johnson_2023/
│   ├── Johnson_2023_Computer_Vision.pdf
│   └── Johnson_2023_Image_Processing.pdf
├── Brown_2021/
│   └── Brown_2021_Machine_Learning.pdf
├── download_report.txt
├── download_report.json
└── download_report.pdf
```

### Sample Report Output

```
================================================================================
PAPER DOWNLOAD SUMMARY REPORT
================================================================================

Generated: 2023-11-13 14:06:53

SUMMARY STATISTICS
--------------------------------------------------------------------------------
Total References:    15
Successfully Downloaded: 12
Failed Downloads:    2
Skipped:             1
Success Rate:        80.0%

SUCCESSFULLY DOWNLOADED PAPERS
--------------------------------------------------------------------------------

1. Deep Learning Fundamentals
   Authors: Smith, J., Doe, J., et al.
   Year: 2022
   Journal: Journal of AI Research
   DOI: 10.1234/example.2022
   Saved to: ./downloads/Smith_2022/Smith_2022_Deep_Learning.pdf
   File Size: 2.45 MB
   Source: doi_resolver

...
```

### JSON Report Example

```json
{
  "timestamp": "2023-11-13T14:06:53",
  "summary": {
    "total_references": 15,
    "successful": 12,
    "failed": 2,
    "skipped": 1,
    "success_rate": 80.0
  },
  "results": [
    {
      "reference": {
        "authors": ["Smith, J.", "Doe, J."],
        "title": "Deep Learning Fundamentals",
        "year": 2022,
        "journal": "Journal of AI Research",
        "doi": "10.1234/example.2022"
      },
      "status": "success",
      "source": "doi_resolver",
      "file_path": "./downloads/Smith_2022/Smith_2022_Deep_Learning.pdf",
      "file_size": 2566144,
      "error_message": null
    }
  ]
}
```

## Troubleshooting Examples

### Issue: No references found

```python
# Check what was extracted
if extraction_result.total_references == 0:
    print("Extraction errors:", extraction_result.extraction_errors)
    
    # Try checking the PDF content directly
    import pdfplumber
    with pdfplumber.open("paper.pdf") as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        print("First page text:", pdf.pages[0].extract_text()[:200])
```

### Issue: Downloads failing silently

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug output
coordinator = DownloadCoordinator()
summary = coordinator.download_references(references)

# Check detailed error messages
for result in summary.results:
    if result.status == "failed":
        print(f"Failed: {result.reference.title}")
        print(f"Error: {result.error_message}")
```

### Issue: Slow downloads

```python
# Adjust timeout settings
from src.config import settings

settings.TIMEOUT = 60  # Increase to 60 seconds
settings.REQUEST_DELAY = 1.0  # Increase delay between requests

# Disable slower sources
settings.ENABLE_SCIHUB = False  # Skip Sci-Hub if it's slow

coordinator = DownloadCoordinator()
summary = coordinator.download_references(references)
```

## Performance Tips

1. **Filter references** before downloading to only target relevant papers
2. **Disable unnecessary sources** in `src/config.py` to speed up searches
3. **Increase timeout** for slow network connections
4. **Use bulk operations** - process multiple papers at once
5. **Check DOI metadata** first - it's usually the fastest source

## Integration Examples

### With Zotero Export

```python
# If you export references as BibTeX from Zotero
import bibtexparser

def load_bibtex_references(bibtex_file):
    """Load references from BibTeX file."""
    with open(bibtex_file) as f:
        bibtex_str = f.read()
    
    db = bibtexparser.loads(bibtex_str)
    
    references = []
    for entry in db.entries:
        ref = Reference(
            raw_text=str(entry),
            authors=entry.get('author', '').split(' and '),
            title=entry.get('title', ''),
            year=int(entry.get('year', 0)) if entry.get('year') else None,
            journal=entry.get('journal', ''),
            doi=entry.get('doi', ''),
        )
        references.append(ref)
    
    return references

# Use it
refs = load_bibtex_references("references.bib")
coordinator = DownloadCoordinator()
summary = coordinator.download_references(refs)
```

### Batch Processing Multiple Papers

```python
from pathlib import Path

def process_all_pdfs(directory, output_base):
    """Process all PDFs in a directory."""
    pdf_files = Path(directory).glob("*.pdf")
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        
        output_dir = Path(output_base) / pdf_file.stem
        
        # Extract
        extractor = PDFExtractor()
        result = extractor.extract(str(pdf_file))
        
        # Download
        coordinator = DownloadCoordinator(output_dir)
        summary = coordinator.download_references(result.references)
        
        # Report
        reporter = ReportGenerator(output_dir)
        reporter.generate_reports(summary, f"{pdf_file.stem}_report")
        
        print(f"  ✓ Downloaded {summary.successful}/{summary.total_references}")

# Process all papers in a folder
process_all_pdfs("./papers", "./downloaded_papers")
```

## Configuration Examples

### Set Up for Academic Research

```python
from src.config import settings

# Prioritize open access and preprints
settings.ENABLE_ARXIV = True
settings.ENABLE_BIORXIV = True
settings.ENABLE_OPEN_ACCESS = True
settings.ENABLE_SCIHUB = False  # Respect legal boundaries

# Optimize for academic sources
settings.TIMEOUT = 30
settings.REQUEST_DELAY = 0.5
```

### Set Up for Speed

```python
from src.config import settings

# Faster, but less comprehensive
settings.ENABLE_SCIHUB = False  # Skip slow sources
settings.ENABLE_BIORXIV = False
settings.TIMEOUT = 15  # Shorter timeout
settings.REQUEST_DELAY = 0.1  # Faster requests
```
