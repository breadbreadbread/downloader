from setuptools import setup, find_packages

setup(
    name="reference-downloader",
    version="0.1.0",
    description="Extract references from PDFs/websites and download the referenced papers",
    author="Development Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0,<2.33.0",
        "pdfplumber>=0.10.0,<0.12.0",
        "beautifulsoup4>=4.12.0,<4.15.0",
        "lxml>=4.9.0,<4.10.0",
        "pydantic>=2.0.0,<2.13.0",
        "reportlab>=4.0.0,<4.5.0",
        "Pillow>=10.0.0,<11.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0,<8.0.0",
            "pytest-cov>=4.1.0,<5.0.0",
            "black>=23.10.0,<24.0.0",
            "isort>=5.12.0,<6.0.0",
            "flake8>=6.1.0,<7.0.0",
            "mypy>=1.6.0,<2.0.0",
            "pylint>=3.0.0,<4.0.0",
            "pip-audit>=2.6.0,<3.0.0",
            "responses>=0.24.0,<0.25.0",
            "faker>=20.0.0,<21.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ref-downloader=src.main:main",
        ],
    },
)
