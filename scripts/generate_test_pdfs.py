#!/usr/bin/env python3
"""
Generate synthetic test PDFs for validation testing.

Usage:
    python scripts/generate_test_pdfs.py

Dependencies:
    - reportlab (part of requirements.txt)

Output:
    Creates synthetic PDFs in tests/fixtures/synthetic/:
    - single_column_20_refs.pdf
    - single_column_50_refs.pdf
    - two_column_20_refs.pdf
    - two_column_50_refs.pdf
    - three_column_20_refs.pdf
    - three_column_50_refs.pdf
    - pdf_with_captions.pdf
"""

import tempfile
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY


def generate_single_column_pdf(num_references: int = 20) -> str:
    """Generate a single-column academic paper with references."""
    temp_file = tempfile.mktemp(suffix=".pdf")
    
    doc = SimpleDocTemplate(temp_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    story.append(Paragraph("Test Paper: Single Column Layout", title_style))
    story.append(Spacer(1, 12))
    
    # Abstract
    story.append(Paragraph("Abstract", styles['Heading2']))
    abstract_text = """
    This is a test paper generated for validation purposes. It demonstrates the layout-aware 
    PDF extraction capabilities with a single column format. The paper includes various 
    reference formats to test the robustness of the reference parser.
    """
    story.append(Paragraph(abstract_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Main content
    story.append(Paragraph("Introduction", styles['Heading2']))
    intro_text = """
    Reference extraction from academic papers is a challenging task that requires sophisticated 
    layout analysis. Different journals use various formatting styles for their reference 
    sections, making automated extraction difficult [1]. Our approach uses layout-aware 
    parsing to handle these variations effectively [2, 3].
    """
    story.append(Paragraph(intro_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # References
    story.append(Paragraph("References", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Generate references
    reference_style = ParagraphStyle(
        'Reference',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=6
    )
    
    for i in range(1, num_references + 1):
        if i % 4 == 1:
            # Standard journal reference
            ref = f"[{i}] Smith, J., Johnson, A., & Williams, B. (2023). Layout-aware PDF extraction for scientific papers. Journal of Computational Linguistics, 45(3), 234-251. https://doi.org/10.1234/jcl.2023.{i:03d}"
        elif i % 4 == 2:
            # arXiv reference
            ref = f"[{i}] Davis, R. & Miller, K. (2023). Machine learning approaches to reference parsing. arXiv:2301.{i:05d}."
        elif i % 4 == 3:
            # Conference reference
            ref = f"[{i}] Thompson, L., Anderson, M., & Wilson, S. (2023). Extracting citations from multi-column layouts. Proceedings of the International Conference on Document Analysis, 156-163."
        else:
            # Book reference
            ref = f"[{i}] Brown, C. (2023). The Complete Guide to Bibliographic Extraction. Academic Press, New York, 2nd edition."
        
        story.append(Paragraph(ref, reference_style))
    
    # Build PDF
    doc.build(story)
    return temp_file


def generate_two_column_pdf(num_references: int = 50) -> str:
    """Generate a two-column IEEE-style paper with references."""
    temp_file = tempfile.mktemp(suffix=".pdf")
    
    doc = SimpleDocTemplate(temp_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=20,
        alignment=1  # Center
    )
    story.append(Paragraph("A Two-Column Test Paper for Reference Extraction", title_style))
    story.append(Spacer(1, 12))
    
    # Authors
    authors_style = ParagraphStyle(
        'Authors',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Center
        spaceAfter=20
    )
    story.append(Paragraph("John Smith¹, Jane Johnson², Robert Williams¹", authors_style))
    story.append(Paragraph("¹Department of Computer Science, Test University  ²Department of Linguistics, Research Institute", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Abstract
    story.append(Paragraph("Abstract", styles['Heading2']))
    abstract_text = """
    This paper presents a comprehensive test dataset for validating PDF reference extraction 
    systems. The two-column format is common in engineering and computer science 
    publications, posing unique challenges for automated extraction systems [1]. We demonstrate 
    how layout-aware parsing can achieve high accuracy rates [2, 3, 4].
    """
    story.append(Paragraph(abstract_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # References section
    story.append(Paragraph("References", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Generate references in IEEE format
    reference_style = ParagraphStyle(
        'Reference',
        parent=styles['Normal'],
        fontSize=9,
        leftIndent=0,
        spaceAfter=3,
        alignment=TA_JUSTIFY
    )
    
    for i in range(1, num_references + 1):
        if i % 5 == 1:
            # IEEE journal format
            ref = f"[{i}] J. Smith and A. Johnson, "Advanced techniques for PDF layout analysis," IEEE Transactions on Pattern Analysis, vol. 45, no. 3, pp. 234-245, Mar. 2023. doi: 10.1109/TPAMI.2023.{i:06d}"
        elif i % 5 == 2:
            # ACM format
            ref = f"[{i}] R. Davis, K. Miller, and L. Wilson, "Automated reference parsing using machine learning," in Proceedings of the ACM SIGIR Conference, 2023, pp. 123-132."
        elif i % 5 == 3:
            # arXiv
            ref = f"[{i}] M. Thompson and C. Anderson, "Deep learning for citation extraction," arXiv preprint arXiv:2301.{i:05d}, Jan. 2023."
        elif i % 5 == 4:
            # Nature format
            ref = f"[{i}] Williams, B. et al. "Layout-aware parsing of academic documents." Nature 615, 123–129 (2023). https://doi.org/10.1038/s41586-023-{i:04d}"
        else:
            # Science format
            ref = f"[{i}] Brown, C. D. et al., "Reference extraction in multi-column layouts." Science 379, 456-462 (2023)."
        
        story.append(Paragraph(ref, reference_style))
    
    # Build PDF
    doc.build(story)
    return temp_file


def generate_three_column_pdf(num_references: int = 50) -> str:
    """Generate a three-column Nature-style paper with references."""
    temp_file = tempfile.mktemp(suffix=".pdf")
    
    doc = SimpleDocTemplate(temp_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=15,
        alignment=1  # Center
    )
    story.append(Paragraph("Three-Column Layout Test for Reference Extraction", title_style))
    story.append(Spacer(1, 10))
    
    # Authors and affiliations
    authors_style = ParagraphStyle(
        'Authors',
        parent=styles['Normal'],
        fontSize=11,
        alignment=1,  # Center
        spaceAfter=15
    )
    story.append(Paragraph("John Smith¹, Jane Johnson², Robert Williams¹ & Sarah Davis³", authors_style))
    story.append(Paragraph("¹Computer Science Department, Tech University  ²Linguistics Institute, Research Center  ³Data Science Lab, Innovation Corp", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Abstract
    story.append(Paragraph("Abstract", styles['Heading2']))
    abstract_text = """
    Three-column layouts present unique challenges for automated reference extraction 
    systems [1]. The compact format requires sophisticated text flow analysis 
    to maintain reading order [2, 3]. Our approach demonstrates high accuracy 
    across various journal styles [4, 5].
    """
    story.append(Paragraph(abstract_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # References
    story.append(Paragraph("References", styles['Heading2']))
    story.append(Spacer(1, 8))
    
    # Generate references in Nature/Science style
    reference_style = ParagraphStyle(
        'Reference',
        parent=styles['Normal'],
        fontSize=8,
        leftIndent=0,
        spaceAfter=2,
        alignment=TA_JUSTIFY
    )
    
    for i in range(1, num_references + 1):
        if i % 4 == 1:
            # Nature style
            ref = f"{i}. Smith, J. & Johnson, A. Layout-aware parsing of academic documents. Nature 615, 123–129 (2023)."
        elif i % 4 == 2:
            # Science style
            ref = f"{i}. Williams, R. et al. Automated reference extraction using machine learning. Science 379, 456-462 (2023)."
        elif i % 4 == 3:
            # Cell style
            ref = f"{i}. Davis, M. & Thompson, L. Deep learning for citation extraction. Cell 185, 1123-1135 (2023)."
        else:
            # PNAS style
            ref = f"{i}. Brown, C. D. et al. Reference extraction in multi-column layouts. Proc. Natl. Acad. Sci. USA 120, e2201234 (2023)."
        
        story.append(Paragraph(ref, reference_style))
    
    # Build PDF
    doc.build(story)
    return temp_file


def generate_pdf_with_captions() -> str:
    """Generate PDF with figure/table captions mixed with references."""
    temp_file = tempfile.mktemp(suffix=".pdf")
    
    doc = SimpleDocTemplate(temp_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Test Paper with Captions and References", styles['Heading1']))
    story.append(Spacer(1, 12))
    
    # Content with figure references
    story.append(Paragraph("Introduction", styles['Heading2']))
    content_text = """
    Our analysis of reference extraction techniques is shown in Figure 1. The performance 
    comparison is presented in Table 1. These results demonstrate the effectiveness 
    of our approach [1]. Additional experiments are shown in Figure 2.
    """
    story.append(Paragraph(content_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Figure and table captions (should be filtered out)
    caption_style = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontSize=10,
        fontStyle='Italic',
        alignment=1  # Center
    )
    
    story.append(Paragraph("Figure 1: Architecture of the reference extraction system.", caption_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Table 1: Performance comparison of extraction methods.", caption_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Figure 2: Accuracy results on test dataset.", caption_style))
    story.append(Spacer(1, 12))
    
    # References
    story.append(Paragraph("References", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    reference_style = ParagraphStyle(
        'Reference',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=6
    )
    
    references = [
        "[1] Smith, J. & Johnson, A. (2023). Advanced reference extraction techniques. Journal of AI Research, 15(3), 234-251.",
        "[2] Williams, R. et al. (2023). Machine learning for citation parsing. Proceedings of ICML, 456-463.",
        "[3] Davis, M. & Thompson, L. (2023). Deep learning approaches to document analysis. Nature Machine Intelligence, 5, 112-123.",
        "[4] Brown, C. (2023). Layout-aware parsing for academic papers. IEEE Transactions on PAMI, 45(4), 567-589.",
        "[5] Anderson, S. & Wilson, K. (2023). Reference extraction in multi-column layouts. Science, 379, 1234-1245."
    ]
    
    for ref in references:
        story.append(Paragraph(ref, reference_style))
    
    # Build PDF
    doc.build(story)
    return temp_file


def main():
    """Generate all test PDFs."""
    output_dir = Path("tests/fixtures/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating synthetic test PDFs...")
    
    # Generate different types of PDFs
    pdf_generators = [
        ("single_column_20_refs.pdf", lambda: generate_single_column_pdf(20)),
        ("single_column_50_refs.pdf", lambda: generate_single_column_pdf(50)),
        ("two_column_20_refs.pdf", lambda: generate_two_column_pdf(20)),
        ("two_column_50_refs.pdf", lambda: generate_two_column_pdf(50)),
        ("three_column_20_refs.pdf", lambda: generate_three_column_pdf(20)),
        ("three_column_50_refs.pdf", lambda: generate_three_column_pdf(50)),
        ("pdf_with_captions.pdf", generate_pdf_with_captions)
    ]
    
    for filename, generator in pdf_generators:
        print(f"Generating {filename}...")
        temp_path = generator()
        
        # Move to fixtures directory
        output_path = output_dir / filename
        os.rename(temp_path, output_path)
        print(f"  Saved to {output_path}")
    
    print(f"\nGenerated {len(pdf_generators)} test PDFs in {output_dir}")


if __name__ == "__main__":
    main()