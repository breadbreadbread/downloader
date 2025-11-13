# Reference Extractor & Downloader - Comprehensive Plan

## Project Overview
A Python application that extracts bibliographic references from PDF documents or web pages and automatically downloads the referenced papers from multiple sources, with a summary report of success/failure.

## Architecture Overview

### **Phase 1: Reference Extraction**
Extract bibliographic references with high accuracy from:
- **PDF files**: Parse PDF content and identify reference sections
- **Web pages**: Scrape web content and extract reference sections

Key extraction requirements:
- Extract authors, title, year, journal, volume, pages
- Identify and prioritize DOI/URL links
- Handle various reference formats (Harvard, APA, Chicago, etc.)
- Normalize and validate extracted data

### **Phase 2: Reference Parsing & Normalization**
- Parse each reference into structured format
- Extract key fields: first_author_last_name, year, DOI, title, journal, volume, pages
- Validate DOI format and attempt lookups via Crossref API
- Create standardized Reference objects

### **Phase 3: Paper Downloading**
For each reference, attempt downloads in priority order:
1. **Open Access Sources** - Unpaywall, CORE, Directory of Open Access Journals
2. **Journal Website** - Direct access via DOI resolution
3. **PubMed Central** - Free full-text biomedical articles
4. **Sci-Hub** (sci-hub.se) - Alternative access
5. **Preprint Servers**:
   - arXiv (physics, math, CS)
   - bioRxiv (biology)
   - chemRxiv (chemistry)

Each source uses DOI lookup first, falling back to title/author searches.

Output folder structure: `[FirstAuthorLastName]_[Year]/[Paper_Reference].pdf`

### **Phase 4: Report Generation**
Generate a comprehensive summary PDF/text report:
- List of successfully downloaded papers with metadata
- List of failed downloads with failure reasons
- Download statistics (total, succeeded, failed)
- Execution time and metadata

## Project Structure

```
reference-downloader/
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   ├── config.py                  # Configuration constants and settings
│   ├── models.py                  # Pydantic models for data validation
│   ├── utils.py                   # Utility functions (logging, path handling)
│   ├── extractor/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base extractor class
│   │   ├── pdf_extractor.py       # PDF extraction implementation
│   │   ├── web_extractor.py       # Web extraction implementation
│   │   └── parser.py              # Reference parsing and normalization
│   ├── downloader/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base downloader class
│   │   ├── coordinator.py         # Orchestrate downloads
│   │   ├── open_access.py         # Open access source downloader
│   │   ├── journal.py             # Direct journal access
│   │   ├── pubmed.py              # PubMed/PubMed Central
│   │   ├── scihub.py              # Sci-Hub downloader
│   │   └── arxiv.py               # arXiv/bioRxiv/chemRxiv
│   └── report/
│       ├── __init__.py
│       └── generator.py           # Report generation
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   └── test_downloader.py
├── requirements.txt               # Dependencies
├── setup.py                       # Package setup
├── README.md                      # User documentation
├── PLAN.md                        # This file
└── .gitignore
```

## Key Dependencies

### Core Libraries
- `requests` - HTTP requests and web scraping
- `pdfplumber` - Advanced PDF text extraction
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parsing

### Data Processing
- `bibtexparser` - BibTeX parsing
- `crossref-commons` - DOI lookup and metadata
- `pydantic` - Data validation and settings management

### Reporting
- `reportlab` - PDF generation
- `Pillow` - Image handling for reports

### API Access
- `arxiv` - arXiv API client
- `biopython` - Optional, for biomedical data

### Utilities
- `python-dotenv` - Environment variable management
- `tqdm` - Progress bars

## Implementation Phases

### Phase 1: Setup & Infrastructure (Priority: HIGH)
- [ ] Create project structure
- [ ] Configure setup.py and requirements.txt
- [ ] Create configuration module
- [ ] Create data models (Reference, Paper, DownloadResult)
- [ ] Create utility functions (logging, file handling)

### Phase 2: Reference Extraction (Priority: CRITICAL)
- [ ] Implement PDF extractor (using pdfplumber)
- [ ] Implement web extractor (using BeautifulSoup)
- [ ] Implement reference parser (regex patterns for common formats)
- [ ] Create DOI validation and enrichment
- [ ] Handle edge cases and malformed references

### Phase 3: Paper Downloader (Priority: CRITICAL)
- [ ] Implement base downloader class
- [ ] Implement Open Access downloader (Unpaywall)
- [ ] Implement DOI resolver (doi.org)
- [ ] Implement Sci-Hub downloader
- [ ] Implement arXiv/bioRxiv/chemRxiv downloader
- [ ] Implement PubMed/PMC downloader
- [ ] Create download coordinator with fallback logic
- [ ] Handle file deduplication

### Phase 4: Reporting (Priority: HIGH)
- [ ] Implement report generator
- [ ] Create PDF report template
- [ ] Add statistics and metrics
- [ ] Handle report export

### Phase 5: CLI & Polish (Priority: MEDIUM)
- [ ] Create command-line interface (argparse or click)
- [ ] Add error handling and recovery
- [ ] Add logging throughout application
- [ ] Create user documentation
- [ ] Add basic tests

## Reference Extraction Strategy

### PDF Extraction
1. Use pdfplumber to extract text while preserving structure
2. Identify reference sections (look for "References", "Bibliography", etc.)
3. Use regex patterns to identify reference boundaries
4. Extract raw reference text

### Reference Parsing
1. **DOI Detection**: Look for DOI patterns (10.xxxx/xxx)
2. **URL Detection**: Capture URLs
3. **Author Extraction**: Parse author names from common patterns
4. **Year Extraction**: 4-digit patterns in reference
5. **Title Extraction**: Text between author and journal/year
6. **Journal/Venue**: Italicized or capitalized journal names

### Supported Reference Formats
- **BibTeX**: Parse directly using bibtexparser
- **Harvard**: [Author(s)] (Year). Title. Journal/Venue. Volume, pages.
- **APA**: Similar pattern with Author, A. A., & Author, B. B. (Year).
- **Chicago**: Similar variations
- **DOI-only**: Can enrich from DOI metadata

## Paper Download Strategy

### Priority Order
1. **DOI Resolution** (fastest, most reliable):
   - Use https://doi.org/{doi} to get metadata
   - Check for direct PDF links in CrossRef metadata

2. **Open Access APIs**:
   - Unpaywall: Lookup free full-text availability
   - CORE: Alternative OA discovery

3. **Preprint Servers** (often available freely):
   - Check arXiv, bioRxiv, chemRxiv by DOI or title/author
   
4. **Journal Direct Access**:
   - Attempt direct journal website access if credentials available
   
5. **PubMed Central**:
   - Free full-text biomedical literature
   - Use PMID or PMCID if available
   
6. **Sci-Hub**:
   - Alternative access route (legal/ethical considerations)
   
7. **Author Self-Archival**:
   - ResearchGate, Academia.edu profiles

## Error Handling

- Graceful handling of missing/invalid references
- Network error retry logic with exponential backoff
- Timeout handling for slow sources
- Invalid file format handling
- Log all failures with reasons

## Output Structure

```
output_folder/
├── LastName_Year/
│   ├── Paper_1.pdf
│   ├── Paper_2.pdf
│   └── ...
├── download_report.pdf
├── download_report.txt
└── download_summary.json  # Machine-readable summary
```

## Success Metrics

- Successfully extract 90%+ of references from PDFs
- Achieve 70%+ download success rate for references with DOI
- Achieve 50%+ download success rate overall
- Complete processing in reasonable time (<5 minutes for typical papers)

## Security & Ethics Considerations

- Respect rate limits of external services
- Use appropriate User-Agent headers
- Cache downloads to avoid re-downloading
- Follow terms of service for each download source
- Document all sources used

## Future Enhancements

- GUI interface using PyQt/Tkinter
- Support for more input formats (CSV, BibTeX files)
- Integration with reference managers (Zotero, Mendeley)
- OCR support for scanned PDFs
- Machine learning for better reference extraction
- Support for duplicate detection across references
- Full-text indexing and search of downloaded papers
