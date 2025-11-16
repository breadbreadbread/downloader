"""Generate test fixtures for extraction fallback testing."""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_with_table_references(output_path: str, num_refs: int = 15) -> str:
    """
    Generate a PDF with references in a table format.

    Args:
        output_path: Path to save the PDF
        num_refs: Number of references to generate

    Returns:
        Path to generated PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph("Research Paper with Tabular References", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    # Add some body content
    story.append(Paragraph("Abstract", styles["Heading1"]))
    story.append(
        Paragraph(
            "This paper demonstrates reference extraction from tables. "
            "References are organized in tabular format below.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Add References section with table
    story.append(Paragraph("References", styles["Heading1"]))
    story.append(Spacer(1, 0.1 * inch))

    # Create table data
    table_data = [["No.", "Reference"]]

    for i in range(1, num_refs + 1):
        ref_text = (
            f"Author{i}, A. B. et al. ({2020 + (i % 4)}). "
            f"Study on topic {i}. Journal of Research, "
            f"{10 + i}({i % 5 + 1}), {100 + i * 10}-{110 + i * 10}. "
            f"doi: 10.{1000 + i}/ref.{i:04d}"
        )
        table_data.append([str(i), ref_text])

    # Create table with styling
    table = Table(table_data, colWidths=[0.5 * inch, 6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(table)

    doc.build(story)
    return output_path


def generate_pdf_with_bibtex(output_path: str, num_refs: int = 10) -> str:
    """
    Generate a PDF with BibTeX entries.

    Args:
        output_path: Path to save the PDF
        num_refs: Number of BibTeX entries to generate

    Returns:
        Path to generated PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph("Paper with BibTeX References", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    # Add content
    story.append(Paragraph("Introduction", styles["Heading1"]))
    story.append(
        Paragraph(
            "This document includes BibTeX formatted references.", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Add BibTeX section
    story.append(Paragraph("BibTeX References", styles["Heading1"]))
    story.append(Spacer(1, 0.1 * inch))

    # Generate BibTeX entries
    for i in range(1, num_refs + 1):
        bibtex_entry = f"""@article{{key{i},
  author = {{Author{i}, First and CoAuthor{i}, Second}},
  title = {{Title of Paper {i}: A Comprehensive Study}},
  journal = {{Journal of Science}},
  year = {{{2020 + (i % 4)}}},
  volume = {{{10 + i}}},
  number = {{{i % 5 + 1}}},
  pages = {{{100 + i * 10}--{110 + i * 10}}},
  doi = {{10.{1000 + i}/journal.{i:04d}}}
}}"""
        story.append(Paragraph(bibtex_entry.replace("\n", "<br/>"), styles["Code"]))
        story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return output_path


def generate_three_column_pdf(output_path: str, num_refs: int = 60) -> str:
    """
    Generate a three-column PDF with many references.

    Args:
        output_path: Path to save the PDF
        num_refs: Number of references to generate

    Returns:
        Path to generated PDF
    """
    from reportlab.platypus import Frame, PageTemplate

    doc = SimpleDocTemplate(output_path, pagesize=letter)

    # Define three-column frame template
    frame_width = doc.width / 3 - 8
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, frame_width, doc.height, id="col1")
    frame2 = Frame(
        doc.leftMargin + frame_width + 12,
        doc.bottomMargin,
        frame_width,
        doc.height,
        id="col2",
    )
    frame3 = Frame(
        doc.leftMargin + 2 * (frame_width + 12),
        doc.bottomMargin,
        frame_width,
        doc.height,
        id="col3",
    )

    template = PageTemplate(id="ThreeCol", frames=[frame1, frame2, frame3])
    doc.addPageTemplates([template])

    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph("Three-Column Research Paper", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    # Add References section
    story.append(Paragraph("References", styles["Heading2"]))
    story.append(Spacer(1, 0.05 * inch))

    # Generate references
    for i in range(1, num_refs + 1):
        ref_text = (
            f"[{i}] Author{i}, X., Smith, Y. ({2018 + (i % 6)}). "
            f"Research topic {i}. Science Journal, {15 + (i % 20)}({i % 6 + 1}), "
            f"{200 + i * 3}-{208 + i * 3}. doi: 10.{3000 + i}/sci.{i:05d}"
        )
        story.append(Paragraph(ref_text, styles["BodyText"]))
        if i % 15 == 0:
            story.append(Spacer(1, 0.02 * inch))

    doc.build(story)
    return output_path


def generate_pdf_without_ref_header(output_path: str, num_refs: int = 25) -> str:
    """
    Generate a PDF without explicit reference section header.

    This tests the fallback extraction when header detection fails.

    Args:
        output_path: Path to save the PDF
        num_refs: Number of references to generate

    Returns:
        Path to generated PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph("Paper Without Reference Header", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    # Add body content
    story.append(Paragraph("Conclusion", styles["Heading1"]))
    story.append(
        Paragraph("This concludes our study. See citations below.", styles["Normal"])
    )
    story.append(Spacer(1, 0.3 * inch))

    # Add references WITHOUT a clear header (to test fallback)
    # Just start listing them
    for i in range(1, num_refs + 1):
        ref_text = (
            f"[{i}] Researcher{i}, A. B. ({2019 + (i % 5)}). "
            f"Investigation of phenomenon {i}. "
            f"Nature, {20 + i}(3), {150 + i * 5}-{160 + i * 5}. "
            f"https://doi.org/10.{2000 + i}/nature.{i}"
        )
        story.append(Paragraph(ref_text, styles["Normal"]))
        story.append(Spacer(1, 0.05 * inch))

    doc.build(story)
    return output_path


def generate_html_with_references() -> str:
    """
    Generate HTML content with references in various formats.

    Returns:
        HTML string
    """
    html = """
    <html>
    <head><title>Research Paper</title></head>
    <body>
        <h1>Research Paper Title</h1>
        <p>This is the main content of the paper.</p>
        
        <h2 id="references">References</h2>
        <ol>
            <li>Smith, J., Jones, M. (2021). First study on topic. Journal of Research, 10(2), 100-110. doi: 10.1234/ref1</li>
            <li>Brown, A. et al. (2022). Second investigation. Nature, 15(3), 200-215. https://doi.org/10.5678/ref2</li>
            <li>Taylor, R., White, S. (2020). Third analysis. Science, 8(1), 50-65. doi: 10.9012/ref3</li>
            <li>Green, P. (2023). Fourth paper on methodology. Methods, 12(4), 300-320. doi: 10.3456/ref4</li>
            <li>Black, K., Blue, L. (2019). Fifth contribution. Proceedings, 5(2), 75-85. doi: 10.7890/ref5</li>
        </ol>
        
        <h2>Additional References (BibTeX)</h2>
        <pre>
@article{johnson2021,
  author = {Johnson, Mark and Davis, Sarah},
  title = {Advanced Techniques in Research},
  journal = {Advanced Journal},
  year = {2021},
  volume = {25},
  pages = {400-420},
  doi = {10.1111/adv.2021.001}
}

@inproceedings{wilson2022,
  author = {Wilson, Tom},
  title = {Conference Presentation on Topics},
  booktitle = {Proceedings of Conference},
  year = {2022},
  pages = {50-55},
  doi = {10.2222/conf.2022.002}
}
        </pre>
    </body>
    </html>
    """
    return html


def generate_all_fixtures(output_dir: str = None):
    """
    Generate all test fixtures.

    Args:
        output_dir: Directory to save fixtures (defaults to tests/fixtures)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating test fixtures...")

    # Generate PDF fixtures
    generate_pdf_with_table_references(
        str(output_dir / "pdf_with_table_refs.pdf"), num_refs=15
    )
    print("✓ Generated PDF with table references")

    generate_pdf_with_bibtex(str(output_dir / "pdf_with_bibtex.pdf"), num_refs=10)
    print("✓ Generated PDF with BibTeX")

    generate_three_column_pdf(str(output_dir / "three_column_refs.pdf"), num_refs=60)
    print("✓ Generated three-column PDF")

    generate_pdf_without_ref_header(
        str(output_dir / "pdf_no_ref_header.pdf"), num_refs=25
    )
    print("✓ Generated PDF without reference header")

    # Generate HTML fixture
    html_content = generate_html_with_references()
    with open(output_dir / "html_with_refs.html", "w") as f:
        f.write(html_content)
    print("✓ Generated HTML with references")

    print(f"\nAll fixtures generated in: {output_dir}")


if __name__ == "__main__":
    generate_all_fixtures()
