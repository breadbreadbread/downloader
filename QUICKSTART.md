# Quick Start Guide

Get up and running with the Reference Extractor and Paper Downloader in 5 minutes.

## Installation

### 1. Clone or Download the Repository

```bash
cd reference-downloader
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

That's it! No complex setup required.

## Your First Extract and Download

### Basic Command

```bash
python -m src.main --pdf your_paper.pdf --output ./my_downloads
```

This will:
- Extract all references from your PDF
- Attempt to download each referenced paper
- Save papers to organized folders
- Generate a summary report

### What You'll See

```
INFO - Starting reference extraction and download
INFO - PHASE 1: EXTRACTING REFERENCES
INFO - Extracted 24 references
INFO - PHASE 2: DOWNLOADING PAPERS
INFO - Downloaded 18 papers successfully
INFO - PHASE 3: GENERATING REPORTS
INFO - Results: 18 successful, 2 failed, 4 skipped
```

## Check Your Results

### Output Folder Structure

```
my_downloads/
├── Smith_2023/
│   ├── Smith_2023_Deep_Learning.pdf
│   └── Smith_2023_Neural_Networks.pdf
├── Johnson_2022/
│   └── Johnson_2022_Computer_Vision.pdf
├── download_report.txt         # Human readable
├── download_report.json        # Machine readable
└── download_report.pdf         # PDF report
```

### View the Report

```bash
cat my_downloads/download_report.txt
```

## Common Tasks

### Extract Only (No Download)

If you just want to see what references were found:

```bash
python -m src.main --pdf paper.pdf --skip-download
```

### From a Website

```bash
python -m src.main --url https://example.com/research --output ./downloads
```

### Verbose Logging

Get detailed information about what's happening:

```bash
python -m src.main --pdf paper.pdf --log-level DEBUG
```

## Python API

Want to use it in your own code?

### Simple Example

```python
from src.extractor import PDFExtractor
from src.downloader import DownloadCoordinator
from pathlib import Path

# Step 1: Extract references
extractor = PDFExtractor()
result = extractor.extract("paper.pdf")
print(f"Found {result.total_references} references")

# Step 2: Download papers
coordinator = DownloadCoordinator(output_dir=Path("./downloads"))
summary = coordinator.download_references(result.references)

# Step 3: Check results
print(f"Downloaded: {summary.successful}")
print(f"Failed: {summary.failed}")
```

## Troubleshooting

### No references found?

The PDF might not have a references section, or it might be formatted unusually. Try:

```bash
python -m src.main --pdf paper.pdf --log-level DEBUG --skip-download
```

Check the logs for details about what was extracted.

### Downloads failing?

This is normal - not all papers are freely available online. The tool tries multiple sources but some may require institutional access. Check the report to see which sources were attempted.

### Network errors?

Check your internet connection and try again. The tool has built-in retry logic.

## Next Steps

- Read [API.md](API.md) for detailed API documentation
- Check [EXAMPLES.md](EXAMPLES.md) for more advanced usage patterns
- Review [README.md](README.md) for full documentation
- Look at [PLAN.md](PLAN.md) for architecture details

## Tips for Better Results

1. **Provide complete references** - The more information in the reference, the better chance of finding the paper
2. **Use DOIs when available** - Papers with DOI identifiers download fastest
3. **Check for special characters** - Some PDFs have encoding issues that affect extraction
4. **Be patient** - Downloads can take a while depending on sources and network speed

## Configuration

### Disable Slower Sources

If downloads are taking too long, you can disable sources:

Create a file `config_override.py`:

```python
from src.config import settings

settings.ENABLE_SCIHUB = False      # Disable Sci-Hub
settings.REQUEST_DELAY = 0.1        # Speed up requests
settings.TIMEOUT = 15               # Shorter timeout
```

Then use it:

```python
import config_override  # Import before running
from src.main import main
main()
```

## Environment Variables

Create a `.env` file for custom settings:

```
PUBMED_API_KEY=your_key
CROSSREF_EMAIL=your.email@example.com
```

## Getting Help

1. Check the logs: Look at `ref_downloader.log`
2. Enable debug mode: `--log-level DEBUG`
3. Review the error messages in the report
4. Check [README.md](README.md) troubleshooting section

## Need More?

- Want to process multiple papers? See [EXAMPLES.md](EXAMPLES.md)
- Need advanced customization? See [API.md](API.md)
- Want to understand the system? See [PLAN.md](PLAN.md)

## Supported Reference Formats

The system automatically handles:
- ✓ Harvard style: `Author (Year). Title. Journal.`
- ✓ APA style: `Author, A. A., & Author, B. B. (Year).`
- ✓ Chicago style: `Author, First. "Title." Journal, Year.`
- ✓ Numbered references: `[1] Author. Title. Journal, Year.`
- ✓ DOIs: Automatically extracted and used for faster downloads
- ✓ arXiv IDs: Automatically detected for preprints

## Supported Download Sources

The system tries these sources in order:
1. DOI Resolver (CrossRef) - Fastest
2. arXiv/bioRxiv/chemRxiv - For preprints
3. PubMed Central - For biomedical papers
4. Sci-Hub - Alternative source
5. Direct journal access

## Performance

On a typical machine:
- PDF extraction: ~1-5 seconds per page
- Download: Varies (5-30 seconds per paper on average)
- Full batch: 10 references ≈ 1-2 minutes

Your mileage may vary based on network speed and PDF complexity.

## One More Thing...

Don't forget to cite your sources! The tool helps you organize papers, but proper attribution is important for academic integrity.

Happy researching! 📚
