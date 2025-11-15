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
- [ ] DOI resolution working (CrossRef)
  - Success rate: __% (__ / __)
  - Error handling: ✅/❌
  - Timeout handling: ✅/❌
- [ ] arXiv downloads working with rate limiting
  - Success rate: __% (__ / __)
  - 3-second delay enforced: ✅/❌
  - API error handling: ✅/❌
- [ ] PubMed downloads working
  - Success rate: __% (__ / __)
  - PMID resolution: ✅/❌
  - API key handling: ✅/❌
- [ ] Sci-Hub fallback chain working
  - Mirror failover: ✅/❌
  - Captcha handling: ✅/❌
  - Success rate: __% (__ / __)
- [ ] Error handling and logging appropriate
  - HTTP errors logged: ✅/❌
  - Timeouts handled gracefully: ✅/❌
  - User-friendly error messages: ✅/❌
- [ ] Parallel downloads working efficiently
  - Sequential vs parallel improvement: __x
  - Memory usage reasonable: ✅/❌
  - No race conditions: ✅/❌

## HTTP Hardening Validation ✅
- [ ] Timeouts handled gracefully (30s limit)
  - DOI resolver: ✅/❌
  - arXiv downloader: ✅/❌
  - All downloaders: ✅/❌
- [ ] Retry logic working (3 attempts)
  - Exponential backoff: ✅/❌
  - Success on retry: ✅/❌
  - Proper logging: ✅/❌
- [ ] User agent set correctly
  - All HTTP requests include User-Agent: ✅/❌
  - Custom User-Agent format: ✅/❌
  - No default Python UA: ✅/❌
- [ ] Rate limiting respected
  - arXiv 3-second delay: ✅/❌
  - General 0.5s delay: ✅/❌
  - No rate limit violations: ✅/❌
- [ ] SSL verification enabled
  - HTTPS verification: ✅/❌
  - Certificate validation: ✅/❌
  - No insecure connections: ✅/❌
- [ ] Connection pooling limits effective
  - Max connections configured: ✅/❌
  - Connection reuse: ✅/❌
  - Resource cleanup: ✅/❌

## CLI Interface Validation ✅
- [ ] PDF mode working with valid files
  - Single column PDF: ✅/❌
  - Two column PDF: ✅/❌
  - Three column PDF: ✅/❌
  - Large PDF handling: ✅/❌
- [ ] URL mode working with valid URLs
  - arXiv URLs: ✅/❌
  - PubMed URLs: ✅/❌
  - Journal URLs: ✅/❌
  - Invalid URL rejection: ✅/❌
- [ ] Output directory creation working
  - Nested directory creation: ✅/❌
  - Permission handling: ✅/❌
  - Existing directory handling: ✅/❌
- [ ] Log level configuration working
  - DEBUG logging: ✅/❌
  - INFO logging: ✅/❌
  - ERROR logging: ✅/❌
  - Log file creation: ✅/❌
- [ ] Error messages user-friendly
  - Clear error descriptions: ✅/❌
  - Actionable advice: ✅/❌
  - No stack traces to user: ✅/❌
- [ ] Help documentation complete
  - Usage examples: ✅/❌
  - Parameter descriptions: ✅/❌
  - Troubleshooting tips: ✅/❌

## Performance Validation ✅
- [ ] Extraction performance within targets
  - Single column (20 refs): <2s ✅/❌
  - Two column (50 refs): <3s ✅/❌
  - Three column (50 refs): <4s ✅/❌
- [ ] Download performance within targets
  - Sequential: <5s per reference ✅/❌
  - Parallel: 3-5x improvement ✅/❌
  - Fallback overhead: <1s ✅/❌
- [ ] Memory usage reasonable
  - Peak memory <500MB: ✅/❌
  - No memory leaks: ✅/❌
  - Cleanup after completion: ✅/❌
- [ ] Large batch processing stable
  - 100+ references: ✅/❌
  - Memory growth controlled: ✅/❌
  - Processing time linear: ✅/❌

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