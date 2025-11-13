"""Report generation for download results."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.models import DownloadSummary, DownloadStatus
from src.config import settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate reports for download results."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.output_dir = Path(self.output_dir)
    
    def generate_reports(
        self,
        summary: DownloadSummary,
        report_name: str = "download_report"
    ) -> None:
        """
        Generate all report formats.
        
        Args:
            summary: DownloadSummary to report on
            report_name: Base name for report files
        """
        self.generate_text_report(summary, report_name)
        self.generate_json_report(summary, report_name)
        self._generate_pdf_report(summary, report_name)
    
    def generate_text_report(
        self,
        summary: DownloadSummary,
        report_name: str = "download_report"
    ) -> Path:
        """Generate text report."""
        report_path = self.output_dir / f"{report_name}.txt"
        
        try:
            content = self._format_text_report(summary)
            with open(report_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Text report saved to {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating text report: {str(e)}")
            raise
    
    def generate_json_report(
        self,
        summary: DownloadSummary,
        report_name: str = "download_report"
    ) -> Path:
        """Generate JSON report for machine reading."""
        report_path = self.output_dir / f"{report_name}.json"
        
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_references": summary.total_references,
                    "successful": summary.successful,
                    "failed": summary.failed,
                    "skipped": summary.skipped,
                    "success_rate": summary.success_rate,
                },
                "results": []
            }
            
            for result in summary.results:
                result_dict = {
                    "reference": {
                        "authors": result.reference.authors,
                        "title": result.reference.title,
                        "year": result.reference.year,
                        "journal": result.reference.journal,
                        "doi": result.reference.doi,
                        "pmid": result.reference.pmid,
                        "arxiv_id": result.reference.arxiv_id,
                    },
                    "status": result.status.value,
                    "source": result.source.value if result.source else None,
                    "file_path": result.file_path,
                    "file_size": result.file_size,
                    "error_message": result.error_message,
                }
                data["results"].append(result_dict)
            
            with open(report_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"JSON report saved to {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            raise
    
    def _format_text_report(self, summary: DownloadSummary) -> str:
        """Format text report content."""
        lines = []
        
        lines.append("=" * 80)
        lines.append("PAPER DOWNLOAD SUMMARY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Timestamp
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary statistics
        lines.append("SUMMARY STATISTICS")
        lines.append("-" * 80)
        lines.append(f"Total References:    {summary.total_references}")
        lines.append(f"Successfully Downloaded: {summary.successful}")
        lines.append(f"Failed Downloads:    {summary.failed}")
        lines.append(f"Skipped:             {summary.skipped}")
        lines.append(f"Success Rate:        {summary.success_rate:.1f}%")
        lines.append("")
        
        # Successful downloads
        successful_results = [r for r in summary.results if r.status == DownloadStatus.SUCCESS]
        if successful_results:
            lines.append("SUCCESSFULLY DOWNLOADED PAPERS")
            lines.append("-" * 80)
            for idx, result in enumerate(successful_results, 1):
                ref = result.reference
                lines.append(f"\n{idx}. {ref.title or 'Unknown Title'}")
                if ref.authors:
                    authors_str = ", ".join(ref.authors[:3])
                    if len(ref.authors) > 3:
                        authors_str += ", et al."
                    lines.append(f"   Authors: {authors_str}")
                if ref.year:
                    lines.append(f"   Year: {ref.year}")
                if ref.journal:
                    lines.append(f"   Journal: {ref.journal}")
                if ref.doi:
                    lines.append(f"   DOI: {ref.doi}")
                if result.file_path:
                    lines.append(f"   Saved to: {result.file_path}")
                if result.file_size:
                    size_mb = result.file_size / (1024 * 1024)
                    lines.append(f"   File Size: {size_mb:.2f} MB")
                lines.append(f"   Source: {result.source.value if result.source else 'Unknown'}")
        
        lines.append("")
        lines.append("")
        
        # Failed downloads
        failed_results = [r for r in summary.results if r.status == DownloadStatus.FAILED]
        if failed_results:
            lines.append("FAILED DOWNLOADS")
            lines.append("-" * 80)
            for idx, result in enumerate(failed_results, 1):
                ref = result.reference
                lines.append(f"\n{idx}. {ref.title or 'Unknown Title'}")
                if ref.authors:
                    authors_str = ", ".join(ref.authors[:3])
                    if len(ref.authors) > 3:
                        authors_str += ", et al."
                    lines.append(f"   Authors: {authors_str}")
                if ref.year:
                    lines.append(f"   Year: {ref.year}")
                if ref.doi:
                    lines.append(f"   DOI: {ref.doi}")
                if result.error_message:
                    lines.append(f"   Error: {result.error_message}")
        
        lines.append("")
        lines.append("")
        
        # Skipped
        skipped_results = [r for r in summary.results if r.status == DownloadStatus.SKIPPED]
        if skipped_results:
            lines.append("SKIPPED")
            lines.append("-" * 80)
            for idx, result in enumerate(skipped_results, 1):
                ref = result.reference
                lines.append(f"{idx}. {ref.title or 'Unknown Title'}")
                if result.error_message:
                    lines.append(f"   Reason: {result.error_message}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_pdf_report(
        self,
        summary: DownloadSummary,
        report_name: str = "download_report"
    ) -> Optional[Path]:
        """
        Generate PDF report.
        
        This is a placeholder for PDF generation using reportlab.
        For now, we generate text reports which can be converted to PDF separately.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib import colors
            
            report_path = self.output_dir / f"{report_name}.pdf"
            
            # Create PDF
            doc = SimpleDocTemplate(str(report_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=1,  # Center
            )
            story.append(Paragraph("Paper Download Summary Report", title_style))
            story.append(Spacer(1, 0.3 * inch))
            
            # Summary statistics table
            summary_data = [
                ['Metric', 'Value'],
                ['Total References', str(summary.total_references)],
                ['Successful', str(summary.successful)],
                ['Failed', str(summary.failed)],
                ['Skipped', str(summary.skipped)],
                ['Success Rate', f"{summary.success_rate:.1f}%"],
            ]
            
            summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.5 * inch))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report saved to {report_path}")
            return report_path
        
        except ImportError:
            logger.warning("reportlab not available, skipping PDF generation")
            return None
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return None
