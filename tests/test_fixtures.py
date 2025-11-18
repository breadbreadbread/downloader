"""Test fixtures for fallback extraction testing."""

import os
import tempfile
from pathlib import Path


def create_sample_pdf_with_table():
    """Create a sample PDF with reference table for testing."""
    # This would require PDF creation - for now, return a path to a mock file
    # In a real implementation, you might use reportlab to create test PDFs
    return None


def create_sample_pdf_with_bibtex():
    """Create a sample PDF with embedded BibTeX for testing."""
    # This would require PDF creation
    return None


def create_sample_html_with_lists():
    """Create sample HTML with reference lists for testing."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sample Paper with References</title>
</head>
<body>
    <h1>Sample Paper</h1>
    <p>This is a sample paper with references in list format.</p>
    
    <h2>References</h2>
    <ol>
        <li>Smith, J. and Johnson, A. (2023). Machine Learning Advances in Modern Systems. 
            Journal of Artificial Intelligence Research, 45(2), 123-145. 
            doi:10.1234/jair.2023</li>
        <li>Brown, K., Davis, L., and Wilson, E. (2022). Deep Learning Methods for 
            Computer Vision Applications. Neural Networks, 98(3), 45-67.</li>
        <li>Anderson, M. and Taylor, S. (2021). Pattern Recognition Using 
            Convolutional Networks. Computer Vision and Image Understanding, 
            203, 103-120. doi:10.1016/j.cviu.2021.103120</li>
        <li>Thomas, R. and Martinez, C. (2020). Natural Language Processing 
            with Transformer Models. Computational Linguistics, 46(4), 789-815.</li>
        <li>Lee, J., Park, S., and Kim, H. (2019). Reinforcement Learning 
            for Robotics Applications. IEEE Transactions on Robotics, 
            35(6), 1342-1358. doi:10.1109/TRO.2019.2931456</li>
    </ol>
    
    <h2>Additional Reading</h2>
    <ul>
        <li>Garcia, F. (2023). Introduction to Statistical Learning. 
            Academic Press, 2nd Edition.</li>
        <li>White, A. and Black, B. (2022). Data Science Fundamentals. 
            Technical Publishers, pp. 1-450.</li>
    </ul>
</body>
</html>"""
    return html_content


def create_sample_html_with_citations():
    """Create sample HTML with citation elements for testing."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sample Paper with Citations</title>
</head>
<body>
    <h1>Research Paper</h1>
    
    <div class="abstract">
        <p>This paper discusses various aspects of machine learning and its applications.</p>
    </div>
    
    <div class="content">
        <p>Recent advances in machine learning have been significant <cite>Smith et al., 2023</cite>.</p>
        <p>Deep learning approaches have shown remarkable results <cite>Brown and Davis, 2022</cite>.</p>
    </div>
    
    <div class="references">
        <h2>References</h2>
        <div class="reference-list">
            <cite>Smith, J., Johnson, A., and Williams, K. (2023). Comprehensive Survey of Machine Learning Techniques. 
                ACM Computing Surveys, 55(1), 1-35. doi:10.1145/3568455</cite>
            
            <cite>Brown, K. and Davis, L. (2022). Deep Learning: Theory and Practice. 
                MIT Press, Cambridge, MA, pp. 100-250.</cite>
            
            <cite>Anderson, M., Taylor, S., and Roberts, P. (2021). Neural Networks in Computer Vision. 
                IEEE Transactions on Pattern Analysis and Machine Intelligence, 43(8), 2673-2685. 
                doi:10.1109/TPAMI.2020.3045678</cite>
            
            <cite>Lee, J. and Chen, H. (2020). Natural Language Processing with Deep Learning. 
                Foundations and Trends in Information Retrieval, 14(2-3), 103-297.</cite>
            
            <cite>Garcia, F., Martinez, C., and Rodriguez, A. (2019). Statistical Learning Theory: 
                A Modern Perspective. Journal of Machine Learning Research, 20(125), 1-65.</cite>
        </div>
    </div>
    
    <div id="bibliography">
        <h3>Additional Bibliography</h3>
        <p>White, A. (2023). Introduction to Data Science. Oxford University Press.</p>
        <p>Black, B. and Green, C. (2022). Advanced Algorithms. Cambridge University Press.</p>
    </div>
</body>
</html>"""
    return html_content


def create_sample_text_with_bibtex():
    """Create sample text with embedded BibTeX entries."""
    text_content = """
    This paper discusses various aspects of machine learning research.
    
    Below are some references in BibTeX format:
    
    @article{smith2023comprehensive,
        title={A Comprehensive Survey of Machine Learning Techniques},
        author={Smith, John and Johnson, Alice and Williams, Karen},
        journal={ACM Computing Surveys},
        volume={55},
        number={1},
        pages={1--35},
        year={2023},
        doi={10.1145/3568455},
        publisher={ACM New York, NY, USA}
    }
    
    @inproceedings{brown2022deep,
        title={Deep Learning: Theory and Practice},
        author={Brown, Kevin and Davis, Lisa},
        booktitle={Proceedings of the International Conference on Machine Learning},
        pages={1234--1245},
        year={2022},
        organization={PMLR},
        address={Baltimore, Maryland, USA}
    }
    
    @book{anderson2021neural,
        title={Neural Networks in Computer Vision: A Complete Guide},
        author={Anderson, Michael and Taylor, Sarah and Roberts, Paul},
        publisher={MIT Press},
        address={Cambridge, MA},
        year={2021},
        pages={100--350},
        isbn={978-0-262-02345-6}
    }
    
    @misc{lee2020natural,
        title={Natural Language Processing with Deep Learning: Foundations and Applications},
        author={Lee, Jennifer and Chen, Hannah},
        year={2020},
        eprint={arXiv:2001.12345},
        howpublished={arXiv preprint arXiv:2001.12345}
    }
    
    @phdthesis{garcia2019statistical,
        title={Statistical Learning Theory: A Modern Perspective},
        author={Garcia, Francisco},
        school={Stanford University},
        year={2019},
        address={Stanford, CA},
        type={PhD Thesis}
    }
    
    The references above cover various aspects of modern machine learning research.
    """
    return text_content


def create_sample_table_text():
    """Create sample text representing reference table content."""
    table_content = """
    Smith, J. and Johnson, A. (2023). Machine Learning Advances in Modern Systems. 
    Journal of Artificial Intelligence Research, 45(2), 123-145. doi:10.1234/jair.2023
    
    Brown, K., Davis, L., and Wilson, E. (2022). Deep Learning Methods for 
    Computer Vision Applications. Neural Networks, 98(3), 45-67. vol 98
    
    Anderson, M. and Taylor, S. (2021). Pattern Recognition Using 
    Convolutional Networks. Computer Vision and Image Understanding, 
    203, 103-120. doi:10.1016/j.cviu.2021.103120 pp 103-120
    
    Thomas, R. and Martinez, C. (2020). Natural Language Processing 
    with Transformer Models. Computational Linguistics, 46(4), 789-815.
    
    Lee, J., Park, S., and Kim, H. (2019). Reinforcement Learning 
    for Robotics Applications. IEEE Transactions on Robotics, 
    35(6), 1342-1358. doi:10.1109/TRO.2019.2931456
    """
    return table_content


def save_test_fixtures():
    """Save test fixtures to temporary files for testing."""
    fixtures = {}

    # Create temporary directory for fixtures
    temp_dir = tempfile.mkdtemp(prefix="ref_downloader_test_")

    # Save HTML fixtures
    html_lists = create_sample_html_with_lists()
    html_lists_path = Path(temp_dir) / "test_html_lists.html"
    with open(html_lists_path, "w", encoding="utf-8") as f:
        f.write(html_lists)
    fixtures["html_lists"] = str(html_lists_path)

    html_citations = create_sample_html_with_citations()
    html_citations_path = Path(temp_dir) / "test_html_citations.html"
    with open(html_citations_path, "w", encoding="utf-8") as f:
        f.write(html_citations)
    fixtures["html_citations"] = str(html_citations_path)

    # Save text fixtures
    bibtex_text = create_sample_text_with_bibtex()
    bibtex_path = Path(temp_dir) / "test_bibtex.txt"
    with open(bibtex_path, "w", encoding="utf-8") as f:
        f.write(bibtex_text)
    fixtures["bibtex_text"] = str(bibtex_path)

    table_text = create_sample_table_text()
    table_path = Path(temp_dir) / "test_table.txt"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write(table_text)
    fixtures["table_text"] = str(table_path)

    return fixtures, temp_dir


if __name__ == "__main__":
    fixtures, temp_dir = save_test_fixtures()
    print(f"Test fixtures saved to: {temp_dir}")
    for name, path in fixtures.items():
        print(f"  {name}: {path}")
