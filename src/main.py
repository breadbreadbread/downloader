"""Main entry point for the reference downloader."""

import argparse
import logging
import sys
from pathlib import Path

from src.extractor import PDFExtractor, WebExtractor
from src.downloader import DownloadCoordinator
from src.report import ReportGenerator
from src.models import DownloadSummary, DownloadResult, DownloadStatus, DownloadSource
from src.utils import setup_logging
from src.config import settings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract references and download papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract references from PDF and download papers
  python -m src.main --pdf /path/to/paper.pdf --output ./downloads
  
  # Extract references from a web page
  python -m src.main --url https://example.com/paper --output ./downloads
        """
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to PDF file to extract references from"
    )
    
    parser.add_argument(
        "--url",
        type=str,
        help="URL of web page to extract references from"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./downloads",
        help="Output directory for downloaded papers (default: ./downloads)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Only extract references, don't download papers"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    settings.LOG_LEVEL = args.log_level
    logger = setup_logging()
    
    # Validate input
    if not args.pdf and not args.url:
        parser.print_help()
        print("\nError: Either --pdf or --url must be specified", file=sys.stderr)
        return 1
    
    if args.pdf and args.url:
        print("Error: Cannot specify both --pdf and --url", file=sys.stderr)
        return 1
    
    try:
        logger.info("Starting reference extraction and download")
        
        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract references
        logger.info("=" * 80)
        logger.info("PHASE 1: EXTRACTING REFERENCES")
        logger.info("=" * 80)
        
        if args.pdf:
            logger.info(f"Extracting references from PDF: {args.pdf}")
            pdf_path = Path(args.pdf)
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {args.pdf}")
                return 1
            
            extractor = PDFExtractor()
            extraction_result = extractor.extract(str(pdf_path))
        
        else:  # args.url
            logger.info(f"Extracting references from URL: {args.url}")
            extractor = WebExtractor()
            extraction_result = extractor.extract(args.url)
        
        if extraction_result.extraction_errors:
            for error in extraction_result.extraction_errors:
                logger.error(f"Extraction error: {error}")
        
        logger.info(f"Extracted {extraction_result.total_references} references")
        
        if extraction_result.total_references == 0:
            logger.warning("No references found. Exiting.")
            if args.skip_download:
                summary = DownloadSummary()
                summary.calculate_stats()
                report_gen = ReportGenerator(output_dir)
                report_gen.generate_reports(summary)
            return 0
        
        # Download papers
        if args.skip_download:
            logger.info("Skipping download phase (--skip-download specified)")
            summary = DownloadSummary()
            for reference in extraction_result.references:
                folder_name = reference.get_output_folder_name()
                ref_dir = output_dir / folder_name
                ref_dir.mkdir(parents=True, exist_ok=True)
                summary.results.append(
                    DownloadResult(
                        reference=reference,
                        status=DownloadStatus.SKIPPED,
                        source=DownloadSource.UNKNOWN,
                        file_path=None,
                        error_message="Download skipped via --skip-download flag"
                    )
                )
            summary.calculate_stats()
        
            logger.info("=" * 80)
            logger.info("PHASE 3: GENERATING REPORTS")
            logger.info("=" * 80)
        
            report_gen = ReportGenerator(output_dir)
            report_gen.generate_reports(summary)
            logger.info("Reports generated in %s", output_dir)
            return 0
        
        logger.info("=" * 80)
        logger.info("PHASE 2: DOWNLOADING PAPERS")
        logger.info("=" * 80)
        
        coordinator = DownloadCoordinator(output_dir)
        summary = coordinator.download_references(extraction_result.references)
        
        logger.info("=" * 80)
        logger.info("PHASE 3: GENERATING REPORTS")
        logger.info("=" * 80)
        
        report_gen = ReportGenerator(output_dir)
        report_gen.generate_reports(summary)
        
        logger.info("=" * 80)
        logger.info("DOWNLOAD COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Results summary:")
        logger.info(f"  Total: {summary.total_references}")
        logger.info(f"  Successful: {summary.successful}")
        logger.info(f"  Failed: {summary.failed}")
        logger.info(f"  Skipped: {summary.skipped}")
        logger.info(f"  Success Rate: {summary.success_rate:.1f}%")
        logger.info(f"  Output directory: {output_dir}")
        
        return 0
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
