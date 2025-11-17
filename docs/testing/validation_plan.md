# Validation Plan

A pragmatic validation strategy for the Reference Extractor & Downloader that reflects the
current architecture: an HTTPClient with retry/backoff logic, a layout-aware PDF extractor with
caption filtering, and the staged rollout of structured fallbacks (BibTeX, table, and HTML
pipelines). The goal is to keep validation lightweight, repeatable, and aligned with the
implementation that ships in `main`.

---

## 1. Architecture Context

| Subsystem | Key Components | Validation Focus |
|-----------|----------------|------------------|
| **Network layer** | `src/network/http_client.HTTPClient` (retry, UA rotation, rate limiting) | Deterministic handling of timeouts, 403/429 responses, SSL enforcement |
| **PDF extraction** | `src/extractor/pdf/layout.py` + `PDFExtractor` orchestrator | Multi-column accuracy, caption filtering, provenance metadata |
| **Fallback roadmap** | `BibTeXParser`, `TableExtractor`, `HTMLFallbackExtractor` (enabled behind `PDFExtractor(enable_fallbacks=True)`) | Activation order, duplicate prevention, provenance tagging |
| **Download pipeline** | `DownloadCoordinator`, `DOIResolver`, `ArxivDownloader`, `PubMedDownloader`, `SciHubDownloader` | Correct fallbacks, file deduplication, skip semantics |
| **CLI & reporting** | `src/main.py`, `ReportGenerator` | Error messaging, `--skip-download`, deterministic artifacts |

Each test layer listed below maps back to these components.

---

## 2. Objectives & Success Metrics

| Objective | Target | Measurement |
|-----------|--------|-------------|
| Test coverage | ≥ 80% line coverage | `pytest --cov=src --cov-fail-under=80` (enforced in `pytest.ini`) |
| Extraction fidelity | ≥ 70% references recovered on synthetic multi-column PDFs | `PDFExtractor` fixtures + manual spot checks |
| HTTP robustness | All downloaders gracefully handle timeout/403/connection errors | Unit tests in `tests/test_http_hardening.py` |
| Download coordination | Fallback chain succeeds or reports actionable failure | `tests/test_download_coordinator.py` |
| CLI stability | Success & error flows work without external I/O | `tests/test_cli.py`, `tests/e2e/test_cli_modes.py` with `--skip-download` |
| Performance guardrail | Baseline extraction < 6s for 50 refs, memory delta < 120 MB | `python scripts/measure_performance.py` |

---

## 3. Validation Workflow

1. **Prepare the environment** (Python 3.8–3.12, `requirements-dev.txt`).
2. **Generate or refresh synthetic PDFs** using `scripts/generate_test_pdfs.py`.
3. **Run automated suites** (unit → integration → CLI/e2e).
4. **Collect performance metrics** with `scripts/measure_performance.py` when required.
5. **Complete the release checklist** in `docs/validation-results/validation_checklist_template.md`.
6. **Capture evidence** (reports, logs, baseline JSON, checklist) under `docs/validation-results/`.

---

## 4. Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # pytest, psutil, responses, etc.

# Optional: install package in editable mode
pip install -e .
```

Health checks:

```bash
pip check
pip-audit || true  # pdfminer.six advisory documented in DEPENDENCIES_AUDIT.md
pytest --maxfail=1  # Smoke the test suite
```

---

## 5. Test Matrix

| Layer | Tests | Command | Notes |
|-------|-------|---------|-------|
| **Unit – Extractors** | `tests/test_pdf_extractor.py`, `tests/test_extraction_fallbacks.py` | `pytest tests/test_pdf_extractor.py tests/test_extraction_fallbacks.py` | Validates layout-aware parser, BibTeX/table fallbacks, provenance metadata |
| **Unit – Network** | `tests/test_http_hardening.py` | `pytest tests/test_http_hardening.py` | Mocks `HTTPClient.get` to simulate timeout/403/SSL scenarios |
| **Unit – Coordinator** | `tests/test_download_coordinator.py` | `pytest tests/test_download_coordinator.py` | Confirms fallback order, duplicate skipping, error propagation |
| **CLI smoke** | `tests/test_cli.py` | `pytest tests/test_cli.py` | Uses shared `run_cli` helper, `--skip-download` to avoid real downloads |
| **E2E (fast)** | `tests/e2e/test_cli_modes.py` | `pytest tests/e2e/test_cli_modes.py` | Generates PDFs on the fly, verifies reports/logs |
| **Planned slow/optional** | Performance script | `python scripts/measure_performance.py` | Uses psutil; mark as `@pytest.mark.slow` if converted to pytest |

All tests are compatible with plain `pytest`; the default configuration enforces coverage and strict marker usage. When adding longer-running cases, annotate them with `@pytest.mark.slow` and update `pytest.ini` markers accordingly.

---

## 6. Test Data Strategy

- **Synthetic fixtures** – Generated via `scripts/generate_test_pdfs.py` into `tests/fixtures/synthetic/` (single/two/three-column layouts plus caption noise).
- **HTML fixtures** – Inline within tests for deterministic HTTP parsing scenarios.
- **Real-world PDFs (optional)** – Store sanitized copies under `tests/fixtures/real-world/`; document provenance in the checklist if used.
- **Mock HTTP responses** – Use `responses` or manual patching to avoid live network calls across tests.

Refresh cadence: regenerate synthetic PDFs whenever layout heuristics change, update baseline metrics after significant extractor or HTTPClient modifications.

---

## 7. Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/generate_test_pdfs.py` | Produce canonical synthetic PDFs for extractor regression testing | `python scripts/generate_test_pdfs.py` |
| `scripts/measure_performance.py` | Measure extraction & coordinator overhead; writes baseline JSON | `python scripts/measure_performance.py` |
| `scripts/validate_dependencies.py` | (Existing) Combined dependency + coverage guard | `python scripts/validate_dependencies.py --coverage` |

Both helper scripts ship with module guards and rely only on dependencies already pinned in `requirements.txt`/`requirements-dev.txt`.

Document their outputs in the validation checklist when executed.

---

## 8. Manual & Exploratory Validation

Use the checklist template to track:

- CLI exploratory runs against representative PDFs (`--log-level DEBUG --skip-download`).
- Web extraction smoke tests using local HTTP servers or stored HTML fixtures.
- Visual review of generated reports (`download_report.json` and `.txt`).
- Fallback toggling: run `PDFExtractor(enable_fallbacks=False)` to compare results when diagnosing regressions.

When new fallback modules are introduced, add targeted manual cases (e.g., BibTeX blocks, table-based references) and record outcomes.

---

## 9. Performance & Regression Guards

1. Run `python scripts/measure_performance.py` after major extractor or HTTP changes.
2. Capture `docs/validation-results/performance/baseline.json` in source control when baseline shifts.
3. Compare `time_seconds` and `memory_mb` against the targets defined inside the script (≤ 6s / ≤ 120 MB for 50-reference PDFs).
4. Investigate deviations >20% before releasing.

---

## 10. Evidence & Reporting

- **Checklist** – Fill `docs/validation-results/validation_checklist_template.md` (one copy per release).
- **Reports** – Archive CLI output (`download_report.json/.txt`) for smoke runs.
- **Logs** – Store `ref_downloader.log` from representative executions when diagnosing issues.
- **Summary** – Update `VALIDATION_IMPLEMENTATION_SUMMARY.md` with notable changes or coverage deltas.

---

## 11. Maintenance Rhythm

- Re-run the full plan for every tagged release or whenever extractor/network stack changes.
- Quarterly: refresh dependency audit notes (`DEPENDENCIES_AUDIT.md`) and rerun performance baselines.
- Keep this plan synchronized with architectural documents (`FALLBACK_EXTRACTORS.md`, `PDF_EXTRACTION_IMPROVEMENTS.md`).

By following this plan the team can assert, with reproducible evidence, that the HTTP client, layout-aware extractor, and fallback roadmap continue to meet their quality bar without relying on flaky external services.
