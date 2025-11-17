# Release Validation Checklist - v{VERSION}

**Date**: [填写日期]  
**Validator**: [填写验证人]  
**Environment**: [Python版本] on [操作系统]

## Environment Setup ✅
- [ ] Python 3.8+ environment created
- [ ] Dependencies installed without conflicts (`pip check` passes)
- [ ] All existing tests pass (`python -m unittest discover tests/`)
- [ ] CLI help accessible (`python -m src.main --help`)
- [ ] Virtual environment activated

## PDF Extraction Validation ✅
- [ ] Single-column extraction (20 refs) >70% accuracy
  - References extracted: ____ / 20
  - Accuracy: __%
  - Time: __s
- [ ] Two-column extraction (50 refs) >70% accuracy  
  - References extracted: ____ / 50
  - Accuracy: __%
  - Time: __s
- [ ] Three-column extraction (50 refs) >70% accuracy
  - References extracted: ____ / 50
  - Accuracy: __%
  - Time: __s
- [ ] Caption filtering working correctly
  - Figure captions filtered: ✅/❌
  - Table captions filtered: ✅/❌
  - Scheme captions filtered: ✅/❌
- [ ] Reference section detection robust
  - Header detection: ✅/❌
  - Fallback extraction: ✅/❌
  - Multi-page handling: ✅/❌
- [ ] Edge cases handled gracefully
  - No references PDF: ✅/❌
  - Corrupted PDF: ✅/❌
  - Single reference: ✅/❌

## Download Pipeline Validation ✅
- [ ] DOI resolution working (CrossRef API)
  - Success rate: __% (__ / __)
  - Graceful fallback when metadata lacks PDF URL: ✅/❌
  - Timeout handling captured in logs: ✅/❌
- [ ] arXiv / preprint downloads working with rate limiting
  - Success rate: __% (__ / __)
  - 3-second delay respected: ✅/❌
  - Abstract → PDF URL normalization verified: ✅/❌
- [ ] PubMed Central downloads smoke-tested (if enabled)
  - Success rate: __% (__ / __)
  - Metadata parsing validated: ✅/❌
- [ ] Sci-Hub fallback smoke-tested (if enabled/allowed)
  - Error handling documented: ✅/❌
  - Access restrictions respected: ✅/❌
- [ ] Error handling and logging appropriate
  - HTTP errors logged with context: ✅/❌
  - NOT_FOUND vs FAILED states differentiated: ✅/❌
  - User-facing error messages actionable: ✅/❌

## HTTP Hardening Validation ✅
- [ ] HTTPClient timeout handling (30s default) verified
  - DOI resolver: ✅/❌
  - arXiv downloader: ✅/❌
  - PubMed / Sci-Hub: ✅/❌
- [ ] Retry logic behaviour observed (max retries = __)
  - Exponential backoff applied: ✅/❌
  - 403 responses trigger User-Agent rotation: ✅/❌
  - Retry-After header respected: ✅/❌
- [ ] User-Agent management
  - Requests use pool entries (no default Python UA): ✅/❌
  - Host-specific rotation documented on failure: ✅/❌
- [ ] Rate limiting respected
  - arXiv delay (`settings.ARXIV_DELAY`): ✅/❌
  - Global request delay (`settings.REQUEST_DELAY`): ✅/❌
- [ ] SSL verification enabled (no `verify=False` overrides): ✅/❌

## CLI Interface Validation ✅
- [ ] PDF mode smoke run (`--skip-download`) passes
  - Single column PDF: ✅/❌
  - Two column PDF: ✅/❌
  - Three column PDF: ✅/❌
- [ ] URL mode smoke run (`--skip-download`) passes
  - Local HTML fixture: ✅/❌
  - Invalid URL error message: ✅/❌
- [ ] Output directory creation working
  - Nested directory creation: ✅/❌
  - Existing directory reuse: ✅/❌
- [ ] Log level configuration working
  - DEBUG logging surfaces extraction phases: ✅/❌
  - INFO logging remains concise: ✅/❌
- [ ] Help / error messaging
  - `--help` shows usage/examples: ✅/❌
  - Mutually exclusive PDF/URL error handled: ✅/❌
  - No raw tracebacks surfaced to users: ✅/❌

## Performance Validation ✅
- [ ] Extraction performance within targets
  - Single column (20 refs): ≤2s ✅/❌
  - Two column (50 refs): ≤5s ✅/❌
  - Three column (50 refs): ≤6s ✅/❌
- [ ] Memory usage reasonable (delta ≤120 MB): ✅/❌
- [ ] Baseline JSON updated (`docs/validation-results/performance/baseline.json`): ✅/❌
- [ ] Regression analysis recorded in validation notes: ✅/❌

## Dependency Validation ✅
- [ ] pip check passes (no broken requirements)
  - Runtime dependencies: ✅/❌
  - Development dependencies: ✅/❌
  - No version conflicts: ✅/❌
- [ ] pip-audit completed (vulnerabilities documented)
  - Security scan run: ✅/❌
  - Vulnerabilities documented: ✅/❌
  - Critical issues addressed: ✅/❌
- [ ] All imports working correctly
  - Core modules import: ✅/❌
  - Third-party libraries import: ✅/❌
  - No circular imports: ✅/❌
- [ ] Version compatibility matrix verified
  - Python 3.8: ✅/❌
  - Python 3.9: ✅/❌
  - Python 3.10: ✅/❌
  - Python 3.11: ✅/❌
  - Python 3.12: ✅/❌

## Real-world Validation ✅
- [ ] Nature paper processed successfully
  - References extracted: __ / __
  - Accuracy: __%
  - No crashes: ✅/❌
- [ ] IEEE paper processed successfully
  - References extracted: __ / __
  - Accuracy: __%
  - Two-column handling: ✅/❌
- [ ] arXiv paper processed successfully
  - References extracted: __ / __
  - Accuracy: __%
  - Preprint format: ✅/❌
- [ ] Mixed reference styles handled
  - APA format: ✅/❌
  - MLA format: ✅/❌
  - Chicago format: ✅/❌
  - Harvard format: ✅/❌
- [ ] Edge cases handled gracefully
  - Malformed references: ✅/❌
  - Missing DOIs: ✅/❌
  - Unicode characters: ✅/❌
  - Very long references: ✅/❌

## Documentation Validation ✅
- [ ] README reflects current features
  - Feature list up to date: ✅/❌
  - Installation instructions: ✅/❌
  - Usage examples: ✅/❌
  - Troubleshooting guide: ✅/❌
- [ ] API documentation complete
  - All classes documented: ✅/❌
  - Method signatures: ✅/❌
  - Parameter descriptions: ✅/❌
  - Return value documentation: ✅/❌
- [ ] Quickstart guide accurate
  - Step-by-step instructions: ✅/❌
  - Common use cases: ✅/❌
  - Expected outputs: ✅/❌
- [ ] Troubleshooting guide helpful
  - Common issues covered: ✅/❌
  - Error solutions: ✅/❌
  - Debug instructions: ✅/❌
- [ ] Validation plan referenced
  - Linked from README: ✅/❌
  - Linked from PLAN.md: ✅/❌
  - Test coverage targets: ✅/❌
  - Performance baselines: ✅/❌

## Test Coverage Analysis ✅
- [ ] Unit test coverage >80%
  - Overall coverage: __%
  - Core modules covered: ✅/❌
  - Edge cases tested: ✅/❌
- [ ] Integration test coverage adequate
  - End-to-end workflows: ✅/❌
  - Component interactions: ✅/❌
  - Error propagation: ✅/❌
- [ ] Performance tests implemented
  - Benchmarking scripts: ✅/❌
  - Regression detection: ✅/❌
  - Memory profiling: ✅/❌
- [ ] Manual validation procedures
  - Real-world test cases: ✅/❌
  - User acceptance criteria: ✅/❌
  - Release sign-off process: ✅/❌

## Issues Found

### Critical Issues
[记录发现的严重问题]

### Major Issues  
[记录发现的主要问题]

### Minor Issues
[记录发现的次要问题]

### Observations
[记录其他观察和注意事项]

## Performance Summary

| Metric | Target | Actual | Status |
|---------|--------|--------|--------|
| PDF Extraction (20 refs) | <2s | __s | ✅/❌ |
| PDF Extraction (50 refs) | <4s | __s | ✅/❌ |
| Download Rate | <5s/ref | __s | ✅/❌ |
| Memory Usage | <500MB | __MB | ✅/❌ |
| Test Coverage | >80% | __% | ✅/❌ |

## Sign-off

**Automated Validation**: [ ] PASS [ ] FAIL [ ] PASS WITH ISSUES  
**Manual Validation**: [ ] PASS [ ] FAIL [ ] PASS WITH ISSUES  
**Overall Result**: [ ] APPROVED [ ] NEEDS WORK [ ] REJECTED

**Validator Signature**: _________________________  
**Date**: ________________

**Comments**:
[填写总体评语和建议]