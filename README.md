# Reference Extractor and Paper Downloader

A comprehensive Python application that extracts bibliographic references from PDF documents or web pages and automatically downloads the referenced papers from multiple sources.

## Features

- **Reference Extraction**
  - Extract references from PDF documents using layout-aware parsing
  - Support for multi-column PDF layouts (1-3 columns)
  - Intelligent filtering of figure captions, tables, and non-reference content
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
- Python 3.8+ (recommended: 3.10+)
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

# (Optional) Install development/testing dependencies
pip install -r requirements-dev.txt
# Or: pip install -e .[dev]
```

### Dependencies

The project uses carefully versioned dependencies to ensure compatibility and security:

**Core Runtime Dependencies:**
- `requests>=2.31.0,<2.33.0` - HTTP requests
- `pdfplumber>=0.10.0,<0.12.0` - PDF extraction
- `beautifulsoup4>=4.12.0,<4.15.0` - HTML parsing
- `lxml>=4.9.0,<4.10.0` - XML/HTML backend
- `pydantic>=2.0.0,<2.13.0` - Data validation
- `reportlab>=4.0.0,<4.5.0` - PDF generation
- `Pillow>=10.0.0,<11.0.0` - Image support

**Development Dependencies (optional):**
- pytest, black, isort, flake8, mypy, pylint for development
- pytest-cov for coverage reporting and enforcement
- pip-audit for security scanning
- responses for HTTP mocking in tests

See `requirements.txt` and `requirements-dev.txt` for complete lists.

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
                        Use DEBUG for detailed extraction logging
--skip-download         Only extract references, don't download papers
```

**Note:** Use `--log-level DEBUG` to see detailed information about the PDF extraction process, including column detection, reference section identification, and filtering decisions.

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
- `RETRY_DELAY`: Base delay between retries in seconds (default: 2)
- `REQUEST_DELAY`: Delay between requests to respect rate limits (default: 0.5)
- `USER_AGENT_POOL`: List of User-Agent strings to rotate through (default: 6 browser variants)
- `ENABLE_SCIHUB`: Enable/disable Sci-Hub access (default: True)
- `ENABLE_PUBMED`: Enable/disable PubMed access (default: True)
- `ENABLE_ARXIV`: Enable/disable arXiv access (default: True)

### Environment Variables

Create a `.env` file to override settings:

```
PUBMED_API_KEY=your_key_here
CROSSREF_EMAIL=your.email@example.com
```

**Advanced: Custom User-Agent Pool**
You can customize the User-Agent pool in `src/config.py` by modifying `USER_AGENT_POOL`.
The client will randomly select and rotate through these agents on 403 errors.

## Architecture

### Components

- **Network Module** (`src/network/`)
  - `HTTPClient`: Centralized HTTP client with retry logic and header rotation
    - Automatic retry on 429, 500, 502, 503, 504, 403 errors
    - User-Agent rotation from configurable pool
    - Exponential backoff with respect for Retry-After headers
    - Desktop browser headers (Accept, Accept-Language, etc.)
    - Request/response logging at DEBUG level

- **Extractor Module** (`src/extractor/`)
  - `PDFExtractor`: Extract text and references from PDFs with layout awareness
  - `LayoutAwareExtractor`: Layout-aware PDF parsing with column detection
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
- **Network errors with robust retry logic**
  - Automatic retry on 403, 429, 500, 502, 503, 504 status codes
  - User-Agent rotation on 403 Forbidden errors
  - Exponential backoff between retry attempts
  - Respects Retry-After headers from servers
- Invalid PDF format detection
- Missing or incomplete reference information
- Download failures with detailed error messages (status code + response snippet)
- Automatic fallback to alternative download sources
- Sanitized logging to avoid leaking sensitive data (tokens, keys)

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

## Development Workflow

This project includes comprehensive automation for dependency management, testing, and quality assurance.

### Quick Start for Developers

```bash
# Install all dependencies (including dev tools)
make install-dev

# Run the full validation suite (recommended before commits)
make validate

# Run individual checks
make test-coverage    # Tests with 80% coverage enforcement
make security-check   # pip check + pip-audit
make lint            # Code quality checks
```

### Available Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install runtime dependencies only |
| `make install-dev` | Install all dependencies including dev tools |
| `make test` | Run unit tests |
| `make test-coverage` | Run tests with coverage (enforces 80% minimum) |
| `make validate` | Run full validation (pip check + pip-audit + coverage) |
| `make security-check` | Run security checks only (pip check + pip-audit) |
| `make lint` | Run linting tools (black, isort, flake8, mypy) |
| `make format` | Format code (black, isort) |
| `make clean` | Clean temporary files and artifacts |
| `make ci` | Run full CI pipeline locally |

### Dependency Validation

The project includes automated dependency validation that checks:

1. **pip check** - Ensures no broken requirements or version conflicts
2. **pip-audit** - Scans for known security vulnerabilities
   - Automatically allows the known pdfminer.six vulnerability (GHSA-f83h-ghpp-7wcc)
   - Fails on any unapproved vulnerabilities
3. **Coverage** - Enforces 80% minimum test coverage

```bash
# Run validation manually
python scripts/validate_dependencies.py --coverage --verbose

# Or use the Makefile target
make validate
```

### Test Coverage

- **Minimum requirement**: 80% line coverage
- **Reports**: Generated in XML (for CI) and terminal formats
- **Configuration**: See `pytest.ini` for settings

```bash
# Run coverage check
pytest --cov=src --cov-report=xml --cov-fail-under=80

# Or use the Makefile target
make test-coverage
```

### Security Auditing

```bash
# Quick security check
pip-audit

# Detailed validation with allowlist handling
python scripts/validate_dependencies.py --verbose
```

### CI/CD Integration

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

- Tests on Python 3.8 (minimum) and 3.12 (current)
- Runs linting, formatting checks, and security validation
- Enforces 80% test coverage
- Uploads coverage reports to Codecov
- Fails builds on dependency conflicts or unapproved vulnerabilities
- Comments pull requests with validation results

### Validation Results

Validation results are saved to `validation-results.json` for CI/CD integration:

```json
{
  "pip_check": {
    "status": "passed",
    "output": "No broken requirements found",
    "error": ""
  },
  "pip_audit": {
    "status": "passed_with_allowed",
    "vulnerabilities": [...],
    "output": "",
    "error": ""
  },
  "coverage": {
    "status": "passed",
    "percentage": 85.2,
    "output": "",
    "error": ""
  }
}
```

## Contributing

Contributions are welcome! Please ensure:

1. **Code Quality**: Run `make lint` and `make format` before submitting
2. **Tests**: Maintain >80% test coverage (`make test-coverage`)
3. **Dependencies**: Run `make validate` to check for security issues
4. **Documentation**: Update relevant documentation

Areas for improvement:
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

### Dependency Issues

**"No module named requests/pdfplumber/..."**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install in a clean virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

**Version conflict errors**
```bash
# Check for dependency issues
pip check

# Verify versions match requirements
pip list | grep -E "requests|pdfplumber|pydantic"

# Run security audit
pip install pip-audit
pip-audit
```

### No references found
- Ensure the PDF/website has a references section
- Try a different source
- Check the logs for parsing errors

### Download fails for all papers
- Check your internet connection
- Verify DOI format if using DOI search
- Try disabling problematic sources in settings

### 403 Forbidden errors on --url mode
The application now includes robust retry logic with User-Agent rotation:
- Automatic retry with fresh browser headers on 403 errors
- Rotating User-Agent pool to mimic different browsers
- Exponential backoff with configurable retries

If you still get 403 errors:
- Some websites may block automated access entirely
- Try copying the page content manually
- Check if the site requires authentication

**Debug mode for HTTP requests:**
```bash
# Enable DEBUG logging to see detailed HTTP diagnostics
python -m src.main --url https://example.com --log-level DEBUG
```

You'll see:
- Request attempts with User-Agent rotation
- Status codes and retry attempts
- Final error messages with response snippets

### Very slow downloads
- Network latency is normal
- Sci-Hub mirrors may be slower
- Consider reducing rate limiting if you own the source

### PDF Processing Issues
**pdfminer.six vulnerability warning**
- The application uses pdfplumber which depends on pdfminer.six
- There is a known vulnerability (GHSA-f83h-ghpp-7wcc) in insecure deserialization
- **Mitigation**: Only process trusted PDF files from reliable sources
- This vulnerability requires write access to CMap directories (unlikely in normal use)

## API Dependencies

The application uses the following free APIs:
- **CrossRef API** - DOI metadata and PDF links
- **NCBI E-utilities** - PubMed search and PMID conversion
- **arXiv API** - Preprint metadata and downloads
- **Sci-Hub** - Alternative paper access

No API keys required for basic functionality.

## Testing and Validation

### Running Tests
```bash
# Run all tests
python -m unittest discover tests/ -v

# Run with coverage
pip install coverage
coverage run -m unittest discover tests/
coverage report
```

### Current Test Coverage
- **18 unit tests** covering core functionality
- PDF extraction with layout-aware parsing
- Reference parsing and validation
- Error handling and edge cases

### Validation Plan
For comprehensive testing strategy, quality assurance procedures, and validation guidelines, see:
- **[Testing and Validation Plan](docs/testing/validation_plan.md)** - Complete validation framework
- **[Dependency Audit](DEPENDENCIES_AUDIT.md)** - Security and compatibility audit
- **[PDF Extraction Improvements](PDF_EXTRACTION_IMPROVEMENTS.md)** - Layout-aware extraction details

### Performance Benchmarks
- Single-column PDF (20 refs): <2 seconds
- Two-column PDF (50 refs): <3 seconds  
- Three-column PDF (50 refs): <4 seconds
- Download rate: ~3-5 seconds per paper (varies by source)

## Contributing

When contributing to this project:
1. Ensure all tests pass: `python -m unittest discover tests/`
2. Maintain >80% test coverage for new code
3. Follow existing code style and patterns
4. Update documentation for new features
5. Run security audit: `pip-audit`

For detailed development guidelines, see the [validation plan](docs/testing/validation_plan.md).
