# Reference Extractor and Paper Downloader

A comprehensive Python application that extracts bibliographic references from PDF documents or web pages and automatically downloads the referenced papers from multiple sources.

## Features

- **Reference Extraction**
  - Extract references from PDF documents using advanced text parsing
  - Extract references from web pages
  - Support for multiple reference formats (Harvard, APA, Chicago, etc.)
  - Identification and extraction of DOI, URLs, PMID, and arXiv IDs
  - Author, title, journal, year, and page number extraction

- **Paper Download**
  - Multiple download sources with intelligent fallback strategy:
    - DOI resolution (via CrossRef API)
    - arXiv, bioRxiv, chemRxiv
    - PubMed Central
    - Sci-Hub
  - Organized output folders named by first author and year
  - Duplicate detection to avoid re-downloading

- **Reporting**
  - Comprehensive summary reports (Text, JSON, PDF)
  - Download statistics and success rates
  - Detailed results with error messages
  - Machine-readable JSON output for integration

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd reference-downloader

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Usage

### Basic Usage

```bash
# Extract references from a PDF and download papers
python -m src.main --pdf /path/to/paper.pdf --output ./downloads

# Extract references from a web page
python -m src.main --url https://example.com/paper --output ./downloads

# Only extract references without downloading
python -m src.main --pdf /path/to/paper.pdf --skip-download
```

### Command Line Options

```
--pdf FILE              Path to PDF file to extract references from
--url URL               URL of web page to extract references from
--output DIR            Output directory for downloaded papers (default: ./downloads)
--log-level LEVEL       Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
--skip-download         Only extract references, don't download papers
```

## Output Structure

```
downloads/
├── LastName_Year/
│   ├── Paper_1.pdf
│   ├── Paper_2.pdf
│   └── ...
├── download_report.txt          # Human-readable report
├── download_report.json         # Machine-readable report
└── download_report.pdf          # PDF report (if reportlab available)
```

## Configuration

Configuration can be customized in `src/config.py`. Key settings:

- `TIMEOUT`: HTTP request timeout (default: 30 seconds)
- `MAX_RETRIES`: Number of retry attempts (default: 3)
- `ENABLE_SCIHUB`: Enable/disable Sci-Hub access (default: True)
- `ENABLE_PUBMED`: Enable/disable PubMed access (default: True)
- `ENABLE_ARXIV`: Enable/disable arXiv access (default: True)

### Environment Variables

Create a `.env` file to override settings:

```
PUBMED_API_KEY=your_key_here
CROSSREF_EMAIL=your.email@example.com
```

## Architecture

### Components

- **Extractor Module** (`src/extractor/`)
  - `PDFExtractor`: Extract text and references from PDFs
  - `WebExtractor`: Extract content from web pages
  - `ReferenceParser`: Parse raw reference text into structured data

- **Downloader Module** (`src/downloader/`)
  - `DOIResolver`: Download via DOI resolution
  - `ArxivDownloader`: Download from arXiv/bioRxiv/chemRxiv
  - `PubMedDownloader`: Download from PubMed Central
  - `SciHubDownloader`: Download via Sci-Hub
  - `DownloadCoordinator`: Orchestrate downloads with fallback strategy

- **Report Module** (`src/report/`)
  - `ReportGenerator`: Generate text, JSON, and PDF reports

### Data Models

- `Reference`: Represents a bibliographic reference
- `DownloadResult`: Result of a download attempt
- `DownloadSummary`: Summary of all download results
- `ExtractionResult`: Result of reference extraction

## Download Strategy

The application attempts to download papers in the following priority order:

1. **DOI Resolution** - Fastest and most reliable
   - Uses CrossRef API to get metadata and direct PDF links
   
2. **arXiv/Preprints** - Often freely available
   - arXiv (physics, math, CS)
   - bioRxiv (biology)
   - chemRxiv (chemistry)
   
3. **PubMed Central** - Biomedical literature
   - Free full-text access for many articles
   
4. **Sci-Hub** - Alternative access
   - Comprehensive coverage but with legal considerations

## Limitations and Future Enhancements

### Current Limitations
- OCR not supported for scanned PDFs
- Some reference formats may not be parsed perfectly
- Network-dependent (requires internet access)
- Rate limited to respect server resources

### Planned Features
- GUI interface
- OCR support for scanned PDFs
- Integration with reference managers (Zotero, Mendeley)
- Machine learning-based reference extraction
- Duplicate detection across references
- Full-text indexing of downloaded papers
- CSV/BibTeX file input

## Error Handling

The application handles various error scenarios:
- Network errors with retry logic
- Invalid PDF format detection
- Missing or incomplete reference information
- Download failures with detailed error messages
- Automatic fallback to alternative sources

## Performance

Typical performance on a modern system:
- PDF extraction: ~1-5 seconds per page
- Reference extraction: ~100-200 references per minute
- Download time: Varies by source and file size (typically 5-30 seconds per paper)

## Legal and Ethical Considerations

- Respects robots.txt and rate limits
- Follows terms of service for each download source
- Uses appropriate User-Agent headers
- Sci-Hub access depends on your jurisdiction's regulations
- Citation of papers and sources is encouraged

## Contributing

Contributions are welcome! Areas for improvement:
- Additional download sources
- Better reference parsing
- Performance optimization
- New report formats

## License

[To be determined]

## Support

For issues, questions, or suggestions:
1. Check the troubleshooting section below
2. Review the detailed logs in `ref_downloader.log`
3. Open an issue with detailed information

## Troubleshooting

### No references found
- Ensure the PDF/website has a references section
- Try a different source
- Check the logs for parsing errors

### Download fails for all papers
- Check your internet connection
- Verify DOI format if using DOI search
- Try disabling problematic sources in settings

### Very slow downloads
- Network latency is normal
- Sci-Hub mirrors may be slower
- Consider reducing rate limiting if you own the source

## API Dependencies

The application uses the following free APIs:
- **CrossRef API** - DOI metadata and PDF links
- **NCBI E-utilities** - PubMed search and PMID conversion
- **arXiv API** - Preprint metadata and downloads
- **Sci-Hub** - Alternative paper access

No API keys required for basic functionality.
