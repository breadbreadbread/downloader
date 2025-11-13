from setuptools import setup, find_packages

setup(
    name="reference-downloader",
    version="0.1.0",
    description="Extract references from PDFs/websites and download the referenced papers",
    author="Development Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pdfplumber>=0.9.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "bibtexparser>=1.4.0",
        "crossref-commons>=0.0.9",
        "pydantic>=2.0.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
        "arxiv>=1.4.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "httpx>=0.25.0",
    ],
    entry_points={
        "console_scripts": [
            "ref-downloader=src.main:main",
        ],
    },
)
