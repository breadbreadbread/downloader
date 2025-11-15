"""Pytest suite covering HTTP resilience and user-agent rotation."""

from __future__ import annotations

from pathlib import Path
from typing import List

import requests
import responses

from src.config import settings
from src.downloader.doi_resolver import DOIResolver
from src.downloader.scihub import SciHubDownloader
from src.extractor.web_extractor import WebExtractor
from src.http_client import HTTPClient
from src.models import DownloadSource, DownloadStatus, Reference

@responses.activate
def test_http_client_retries_with_backoff(monkeypatch):
    url = "https://example.com/resource"

    monkeypatch.setattr(settings, "MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "RETRY_DELAY", 0.1)
    monkeypatch.setattr(settings, "RETRY_BACKOFF_FACTOR", 2.0)
    monkeypatch.setattr(settings, "USER_AGENTS", ["agent-a", "agent-b", "agent-c"])

    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=503)
    responses.add(responses.GET, url, json={"ok": True}, status=200)

    sleep_calls: List[float] = []

    monkeypatch.setattr("src.http_client.time.sleep", lambda seconds: sleep_calls.append(seconds))

    client = HTTPClient()
    response = client.get(url)

    assert response.status_code == 200
    assert len(responses.calls) == 3
    assert sleep_calls == [0.1, 0.2]
    # Ensure user agent rotation occurred during retries
    assert responses.calls[0].request.headers["User-Agent"] == "agent-a"
    assert responses.calls[1].request.headers["User-Agent"] == "agent-b"
    assert responses.calls[2].request.headers["User-Agent"] == "agent-c"


@responses.activate
def test_web_extractor_rotates_user_agent_and_succeeds(monkeypatch):
    url = "https://example.com/paper"

    monkeypatch.setattr(settings, "MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "RETRY_DELAY", 0.0)
    monkeypatch.setattr(settings, "USER_AGENTS", ["agent-1", "agent-2", "agent-3"])

    responses.add(responses.GET, url, status=403)
    responses.add(responses.GET, url, body="<html><body>Reference [1] Example.</body></html>", status=200)

    monkeypatch.setattr("src.http_client.time.sleep", lambda _: None)

    extractor = WebExtractor()
    result = extractor.extract(url)

    assert not result.extraction_errors
    assert len(responses.calls) == 2
    assert responses.calls[0].request.headers["User-Agent"] == "agent-1"
    assert responses.calls[1].request.headers["User-Agent"] == "agent-2"


@responses.activate
def test_web_extractor_reports_error_after_retry_exhaustion(monkeypatch):
    url = "https://example.com/failure"
    monkeypatch.setattr(settings, "MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "RETRY_DELAY", 0.0)
    monkeypatch.setattr(settings, "USER_AGENTS", ["ua-a", "ua-b", "ua-c"])

    for _ in range(settings.MAX_RETRIES):
        responses.add(responses.GET, url, status=403)

    monkeypatch.setattr("src.http_client.time.sleep", lambda _: None)

    extractor = WebExtractor()
    result = extractor.extract(url)

    assert result.extraction_errors, "Expected extraction error when all retries fail"
    message = result.extraction_errors[0]
    assert "status 403" in message
    assert "failed after" in message
    assert len(responses.calls) == settings.MAX_RETRIES
    user_agents = [call.request.headers["User-Agent"] for call in responses.calls]
    assert user_agents == ["ua-a", "ua-b", "ua-c"]


@responses.activate
def test_doi_resolver_bubbles_up_http_errors(monkeypatch, tmp_path):
    doi = "10.1234/example.doi"
    url = f"https://api.crossref.org/works/{doi}"

    monkeypatch.setattr(settings, "MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "RETRY_DELAY", 0.0)
    monkeypatch.setattr(settings, "USER_AGENTS", ["agent-x", "agent-y"])

    for _ in range(settings.MAX_RETRIES):
        responses.add(responses.GET, url, status=403)

    monkeypatch.setattr("src.http_client.time.sleep", lambda _: None)

    resolver = DOIResolver()
    reference = Reference(raw_text="Example", doi=doi)
    result = resolver.download(reference, tmp_path / "paper.pdf")

    assert result.status == DownloadStatus.FAILED
    assert result.source == DownloadSource.DOI_RESOLVER
    assert result.error_message is not None
    assert "403" in result.error_message
    assert len(responses.calls) == settings.MAX_RETRIES

    user_agents = [call.request.headers["User-Agent"] for call in responses.calls]
    assert user_agents == ["agent-x", "agent-y", "agent-x"]


@responses.activate
def test_scihub_downloader_rotates_user_agent_and_succeeds(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "RETRY_DELAY", 0.0)
    monkeypatch.setattr(settings, "USER_AGENTS", ["ua-one", "ua-two"])
    monkeypatch.setattr(settings, "SCIHUB_URLS", ["https://sci-hub.test"])
    monkeypatch.setattr(settings, "REQUEST_DELAY", 0.0)

    query_url = "https://sci-hub.test/?q=10.4321/abc"
    pdf_url = "https://sci-hub.test/download.pdf"

    responses.add(responses.GET, query_url, status=403)
    responses.add(
        responses.GET,
        query_url,
        body='<html><body><iframe id="pdfDocument" src="https://sci-hub.test/download.pdf"></iframe></body></html>',
        status=200,
    )
    responses.add(responses.GET, pdf_url, body=b"%PDF-1.7 sample", status=200)

    monkeypatch.setattr("src.http_client.time.sleep", lambda _: None)
    monkeypatch.setattr("src.downloader.scihub.time.sleep", lambda _: None)

    downloader = SciHubDownloader()
    reference = Reference(raw_text="ref", doi="10.4321/abc")
    output_path = tmp_path / "paper.pdf"

    result = downloader.download(reference, output_path)

    assert result.status == DownloadStatus.SUCCESS
    assert Path(result.file_path).exists()
    assert len(responses.calls) == 3
    assert responses.calls[0].request.headers["User-Agent"] == "ua-one"
    assert responses.calls[1].request.headers["User-Agent"] == "ua-two"
    assert responses.calls[2].request.headers["User-Agent"] == "ua-two"


def test_http_client_preserves_tls_verification(monkeypatch):
    captured_verify = {}

    def fake_request(self, method, url, **kwargs):  # type: ignore[override]
        captured_verify["verify"] = kwargs.get("verify")
        response = requests.Response()
        response.status_code = 200
        response._content = b"{}"
        response.url = url
        response.reason = "OK"
        return response

    monkeypatch.setattr(requests.Session, "request", fake_request, raising=False)

    client = HTTPClient()
    response = client.get("https://secure.test")

    assert response.status_code == 200
    assert captured_verify["verify"] is True

