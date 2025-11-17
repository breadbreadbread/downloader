"""Focused smoke tests for CLI interface and command-line functionality."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.e2e.test_cli_modes import make_test_pdf, run_cli


@pytest.fixture(name="project_root")
def fixture_project_root() -> Path:
    """Return the repository root used for PYTHONPATH wiring."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(name="cli_env")
def fixture_cli_env(project_root: Path) -> dict[str, str]:
    """Build a deterministic environment for invoking the CLI."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    paths: list[str] = [str(project_root)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _invoke_cli(tmp_path: Path, cli_env: dict[str, str], *args: str) -> str:
    """Run the CLI and return combined stdout/stderr for assertions."""
    result = run_cli(tmp_path, cli_env, *args)
    combined = (result.stdout + result.stderr).lower()
    returncode_msg = f"return code {result.returncode}: {combined}"
    return combined, result.returncode, returncode_msg


def test_cli_help_displays_usage(tmp_path: Path, cli_env: dict[str, str]) -> None:
    combined, return_code, _ = _invoke_cli(tmp_path, cli_env, "--help")
    assert return_code == 0
    assert "extract references" in combined
    assert "--pdf" in combined
    assert "--url" in combined


def test_cli_requires_input_source(tmp_path: Path, cli_env: dict[str, str]) -> None:
    combined, return_code, _ = _invoke_cli(tmp_path, cli_env)
    assert return_code == 1
    assert "either --pdf or --url must be specified" in combined


def test_cli_pdf_and_url_are_mutually_exclusive(tmp_path: Path, cli_env: dict[str, str]) -> None:
    pdf_path = tmp_path / "inputs" / "test.pdf"
    make_test_pdf(pdf_path, num_refs=1)

    combined, return_code, message = _invoke_cli(
        tmp_path,
        cli_env,
        "--pdf",
        str(pdf_path),
        "--url",
        "https://example.com/paper",
        "--output",
        str(tmp_path / "outputs"),
        "--skip-download",
    )

    assert return_code == 1, message
    assert "cannot specify both --pdf and --url" in combined


def test_cli_reports_missing_pdf(tmp_path: Path, cli_env: dict[str, str]) -> None:
    missing_pdf = tmp_path / "inputs" / "missing.pdf"

    combined, return_code, message = _invoke_cli(
        tmp_path,
        cli_env,
        "--pdf",
        str(missing_pdf),
        "--output",
        str(tmp_path / "outputs"),
        "--skip-download",
    )

    assert return_code == 1, message
    assert "pdf file not found" in combined


def test_cli_creates_output_directory(tmp_path: Path, cli_env: dict[str, str]) -> None:
    pdf_path = tmp_path / "inputs" / "test.pdf"
    make_test_pdf(pdf_path, num_refs=2)
    output_dir = tmp_path / "nested" / "reports"

    combined, return_code, message = _invoke_cli(
        tmp_path,
        cli_env,
        "--pdf",
        str(pdf_path),
        "--output",
        str(output_dir),
        "--skip-download",
    )

    assert return_code == 0, message
    assert output_dir.exists()
    report = output_dir / "download_report.json"
    assert report.exists(), combined


def test_cli_accepts_log_level(tmp_path: Path, cli_env: dict[str, str]) -> None:
    pdf_path = tmp_path / "inputs" / "test.pdf"
    make_test_pdf(pdf_path, num_refs=1)

    combined, return_code, message = _invoke_cli(
        tmp_path,
        cli_env,
        "--pdf",
        str(pdf_path),
        "--output",
        str(tmp_path / "outputs"),
        "--skip-download",
        "--log-level",
        "DEBUG",
    )

    assert return_code == 0, message
    assert "extracting references" in combined
