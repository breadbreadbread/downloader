"""End-to-end CLI tests for ref-downloader."""

from __future__ import annotations

import io
import json
import logging
import os
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Iterator

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from src.models import DownloadResult, DownloadSource, DownloadStatus

DOWNLOAD_REPORT_JSON = "download_report.json"
DOWNLOAD_REPORT_TEXT = "download_report.txt"
LOG_FILENAME = "ref_downloader.log"


def _build_reference_text(index: int) -> str:
    year = 2020 + (index % 5)
    return (
        f"[{index}] TestAuthor{index}, A., CoAuthor, B. ({year}). "
        f"CLI Reference Example {index}. Journal of Testing, "
        f"{10 + index}(2), {100 + index}-{110 + index}. "
        f"https://doi.org/10.1234/test.{index:04d}"
    )


def make_test_pdf(pdf_path: Path, num_refs: int = 5) -> None:
    """Create a synthetic PDF containing a references section."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Synthetic Test Paper", styles["Title"]),
        Spacer(1, 0.2 * inch),
        Paragraph("References", styles["Heading1"]),
        Spacer(1, 0.1 * inch),
    ]

    for idx in range(1, num_refs + 1):
        story.append(Paragraph(_build_reference_text(idx), styles["Normal"]))
        story.append(Spacer(1, 0.05 * inch))

    doc.build(story)


def build_reference_html(num_refs: int = 5) -> str:
    references = "<br>".join(_build_reference_text(i) for i in range(1, num_refs + 1))
    return f"""
    <html>
      <head><title>CLI Test Page</title></head>
      <body>
        <h1>Research Article</h1>
        <section id="references">
          {references}
        </section>
      </body>
    </html>
    """


@contextmanager
def serve_html(html: str, status: int = 200) -> Iterator[str]:
    """Serve deterministic HTML content for URL-based CLI tests."""
    payload = html.encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # type: ignore[override]
            if self.path.rstrip("/") == "/paper":
                self.send_response(status)
                if status == 200:
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: D401
            """Silence test HTTP server logging."""
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/paper"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def run_cli(
    tmp_path: Path, env: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    """Execute the CLI via `python -m src.main` within a temporary workspace."""
    command = [sys.executable, "-m", "src.main", *args]
    return subprocess.run(
        command,
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def cli_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    paths = [str(project_root)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def test_pdf_mode_skip_download_generates_reports(
    tmp_path: Path, cli_env: dict[str, str]
) -> None:
    pdf_path = tmp_path / "inputs" / "test.pdf"
    output_dir = tmp_path / "artifacts"
    make_test_pdf(pdf_path, num_refs=6)

    result = run_cli(
        tmp_path,
        cli_env,
        "--pdf",
        str(pdf_path),
        "--output",
        str(output_dir),
        "--skip-download",
        "--log-level",
        "INFO",
    )

    assert result.returncode == 0, result.stderr
    combined = (result.stdout + result.stderr).lower()
    assert "extracting references" in combined
    assert "skipping download" in combined

    log_path = tmp_path / LOG_FILENAME
    assert log_path.exists(), "Log file should be emitted in working directory"

    json_report = output_dir / DOWNLOAD_REPORT_JSON
    text_report = output_dir / DOWNLOAD_REPORT_TEXT
    assert json_report.exists()
    assert text_report.exists()

    data = json.loads(json_report.read_text())
    total = data["summary"]["total_references"]
    assert total == len(data["results"]) > 0
    assert {entry["status"] for entry in data["results"]} == {"skipped"}

    reference_dirs = [p for p in output_dir.iterdir() if p.is_dir()]
    assert len(reference_dirs) == len(data["results"])


def test_url_mode_skip_download_uses_local_server(
    tmp_path: Path, cli_env: dict[str, str]
) -> None:
    html = build_reference_html(num_refs=4)
    output_dir = tmp_path / "url-artifacts"

    with serve_html(html) as url:
        result = run_cli(
            tmp_path,
            cli_env,
            "--url",
            url,
            "--output",
            str(output_dir),
            "--skip-download",
        )

    assert result.returncode == 0, result.stderr
    combined = (result.stdout + result.stderr).lower()
    assert "extracting references" in combined

    data = json.loads((output_dir / DOWNLOAD_REPORT_JSON).read_text())
    assert data["summary"]["total_references"] == len(data["results"]) > 0
    assert {entry["status"] for entry in data["results"]} == {"skipped"}


def test_invalid_url_reports_error(tmp_path: Path, cli_env: dict[str, str]) -> None:
    output_dir = tmp_path / "invalid-url"
    result = run_cli(
        tmp_path,
        cli_env,
        "--url",
        "not-a-valid-url",
        "--output",
        str(output_dir),
        "--skip-download",
    )

    assert result.returncode == 0, result.stderr
    combined = (result.stdout + result.stderr).lower()
    assert "invalid url format" in combined

    data = json.loads((output_dir / DOWNLOAD_REPORT_JSON).read_text())
    assert data["summary"]["total_references"] == 0
    assert data["results"] == []


def test_unreachable_url_is_logged(tmp_path: Path, cli_env: dict[str, str]) -> None:
    output_dir = tmp_path / "unreachable"
    result = run_cli(
        tmp_path,
        cli_env,
        "--url",
        "http://127.0.0.1:9/paper",
        "--output",
        str(output_dir),
        "--skip-download",
        "--log-level",
        "INFO",
    )

    assert result.returncode == 0
    combined = (result.stdout + result.stderr).lower()
    assert "error fetching url" in combined or "error" in combined

    data = json.loads((output_dir / DOWNLOAD_REPORT_JSON).read_text())
    assert data["summary"]["total_references"] == 0


def test_missing_pdf_returns_error(tmp_path: Path, cli_env: dict[str, str]) -> None:
    missing_pdf = tmp_path / "does-not-exist.pdf"
    output_dir = tmp_path / "pdf-error"
    result = run_cli(
        tmp_path,
        cli_env,
        "--pdf",
        str(missing_pdf),
        "--output",
        str(output_dir),
        "--skip-download",
    )

    assert result.returncode == 1
    combined = (result.stdout + result.stderr).lower()
    assert "pdf file not found" in combined


def test_cli_pipeline_smoke_with_stubbed_downloader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "pipeline.pdf"
    output_dir = tmp_path / "pipeline-output"
    make_test_pdf(pdf_path, num_refs=2)

    captured_references: list = []

    def fake_try_downloaders(self, reference, output_path):
        captured_references.append(reference)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("stub-pdf", encoding="utf-8")
        return DownloadResult(
            reference=reference,
            status=DownloadStatus.SUCCESS,
            source=DownloadSource.OPEN_ACCESS,
            file_path=str(output_path),
            file_size=len("stub-pdf"),
        )

    monkeypatch.setattr(
        "src.downloader.coordinator.DownloadCoordinator._try_downloaders",
        fake_try_downloaders,
    )

    from src.config import settings

    monkeypatch.setattr(settings, "LOG_FILE", tmp_path / "pipeline.log")
    monkeypatch.setattr(settings, "LOG_LEVEL", "INFO")

    def setup_logging_stub(log_file=None):
        logger = logging.getLogger(f"ref_downloader_e2e_{time.time()}")
        logger.setLevel(settings.LOG_LEVEL)
        logger.handlers.clear()
        handler = logging.StreamHandler(io.StringIO())
        handler.setLevel(settings.LOG_LEVEL)
        logger.addHandler(handler)
        logger.propagate = False
        return logger

    monkeypatch.setattr("src.main.setup_logging", setup_logging_stub)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ref-downloader",
            "--pdf",
            str(pdf_path),
            "--output",
            str(output_dir),
        ],
    )

    from src import main as cli_main

    exit_code = cli_main.main()
    assert exit_code == 0
    assert captured_references, "Download coordinator should process references"

    json_report = output_dir / DOWNLOAD_REPORT_JSON
    assert json_report.exists()

    data = json.loads(json_report.read_text())
    assert data["summary"]["successful"] == len(captured_references)
    assert {entry["status"] for entry in data["results"]} == {"success"}


if __name__ == "__main__":
    pytest.main([__file__])
