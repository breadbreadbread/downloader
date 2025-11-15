# Dependency & Coverage Automation Guide

This document describes the automated dependency validation and coverage enforcement system implemented for the reference-downloader project.

## Overview

The automation system provides:
- **Dependency validation** using `pip check` and `pip-audit`
- **Coverage enforcement** with configurable minimum thresholds
- **CI/CD integration** with GitHub Actions
- **Local development tools** via Makefile targets
- **Security vulnerability management** with allowlist handling

## Components

### 1. Validation Script (`scripts/validate_dependencies.py`)

**Purpose**: Centralized validation for dependencies and coverage

**Features**:
- Runs `pip check` to detect broken requirements
- Runs `pip-audit` with JSON output parsing
- Optional coverage validation with configurable thresholds
- Automatic allowlist handling for known vulnerabilities
- JSON result output for CI/CD integration
- Verbose logging and error handling

**Usage**:
```bash
# Security checks only
python scripts/validate_dependencies.py --verbose

# Full validation with coverage
python scripts/validate_dependencies.py --coverage --verbose

# Custom output file
python scripts/validate_dependencies.py --output custom-results.json
```

### 2. Pytest Configuration (`pytest.ini`)

**Purpose**: Enforce coverage standards and test configuration

**Key Settings**:
- Coverage minimum: 80% line coverage
- XML reports for CI/CD integration
- Terminal reports with missing lines
- Strict marker enforcement
- Test discovery configuration

**Coverage Reports**:
- `coverage.xml` - XML format for CI systems
- `coverage.json` - Machine-readable for parsing
- Terminal output - Human-readable with missing lines

### 3. Makefile Automation

**Purpose**: Local development workflow automation

**Key Targets**:

| Target | Description | Use Case |
|---------|-------------|----------|
| `make install` | Install runtime dependencies | Fresh setup |
| `make install-dev` | Install all dependencies | Development setup |
| `make test` | Run unit tests | Quick verification |
| `make test-coverage` | Run tests with coverage | CI validation |
| `make validate` | Full validation pipeline | Pre-commit checks |
| `make security-check` | Security validation only | Quick security check |
| `make lint` | Code quality checks | Pre-commit |
| `make format` | Auto-format code | Code style |
| `make clean` | Clean artifacts | Fresh start |
| `make ci` | Full CI pipeline locally | Pre-push validation |

### 4. GitHub Actions Workflow (`.github/workflows/ci.yml`)

**Purpose**: Automated CI/CD pipeline

**Features**:
- Matrix testing on Python 3.8 (minimum) and 3.12 (current)
- Dependency caching for faster builds
- Linting and formatting validation
- Security vulnerability scanning
- Coverage enforcement and reporting
- Build package verification
- PR comments with validation results
- Artifact upload for debugging

**Pipeline Stages**:
1. **Test Matrix**: Multi-version Python testing
2. **Dependency Validation**: Security and compatibility checks
3. **Build Verification**: Package build and validation
4. **Coverage Reporting**: Upload to Codecov for tracking

## Security Vulnerability Management

### Allowlisted Vulnerabilities

The system automatically allows known, low-risk vulnerabilities:

| ID | Component | Risk Level | Reason |
|-----|-----------|-------------|---------|
| `GHSA-f83h-ghpp-7wcc` | pdfminer.six | Low | Insecure deserialization in CMap loading; requires malicious PDF files |
| `GHSA-4xh5-x5gv-qwph` | pip | Medium | Tarfile extraction vulnerability; fixed in pip 25.3 |
| `PYSEC-2024-48` | black | Low | Regex DoS; fixed in black 24.3.0 |

### Adding New Allowlist Entries

To add new vulnerabilities to the allowlist:

1. **Identify the vulnerability ID** from `pip-audit` output
2. **Assess the risk level** for your use case
3. **Add to allowlist** in `scripts/validate_dependencies.py`:

```python
allowed_vulns = {
    "GHSA-f83h-ghpp-7wcc",  # Existing
    "NEW-VULN-ID",           # Add new vulnerability
    # ... other entries
}
```

### Removing Allowlist Entries

To remove a vulnerability from the allowlist:
1. **Update the dependency** to a fixed version
2. **Remove from allowlist** in the validation script
3. **Test validation** to ensure it passes

## Local Development Workflow

### Quick Start

```bash
# 1. Setup development environment
make install-dev

# 2. Run full validation (recommended before commits)
make validate

# 3. Individual checks as needed
make test-coverage    # Tests with coverage enforcement
make security-check   # Security validation only
make lint            # Code quality checks
```

### Pre-commit Workflow

```bash
# Before committing changes
make format           # Format code
make lint            # Check code quality
make validate         # Full validation
```

### Troubleshooting

**Coverage failures**:
```bash
# View detailed coverage report
make test-coverage

# Check coverage.json for specific percentages
cat coverage.json | jq '.totals.percent_covered'
```

**Security failures**:
```bash
# Run detailed security check
python scripts/validate_dependencies.py --verbose

# View specific vulnerabilities
cat validation-results.json | jq '.pip_audit.vulnerabilities[]'
```

**Dependency conflicts**:
```bash
# Check for broken requirements
pip check

# Reinstall dependencies cleanly
make clean
make install-dev
```

## CI/CD Integration

### GitHub Actions Configuration

The workflow automatically:

1. **Triggers** on pushes/PRs to main/develop branches
2. **Tests** on multiple Python versions
3. **Validates** dependencies and security
4. **Enforces** coverage requirements
5. **Reports** results via PR comments
6. **Uploads** artifacts for debugging

### Coverage Tracking

- **Codecov Integration**: Coverage reports uploaded to Codecov
- **Historical Tracking**: Coverage trends over time
- **PR Comments**: Coverage changes highlighted in pull requests
- **Branch Protection**: Can enforce coverage requirements

### Artifact Management

**Uploaded Artifacts**:
- `validation-results.json` - Full validation results
- `coverage.xml` - Coverage report for CI systems
- Test logs and outputs for debugging

**Retention**: 30 days (configurable in workflow)

## Configuration

### Coverage Threshold

**Current Setting**: 80% minimum line coverage

**To Modify**:
1. Update `pytest.ini`: `--cov-fail-under=XX`
2. Update `Makefile`: `--cov-fail-under=XX`
3. Update `scripts/validate_dependencies.py`: `--cov-fail-under=XX`

**Recommendation**: Start with 30-40% for new projects, increase to 80% for mature codebases.

### Python Version Testing

**Current Matrix**:
- Python 3.8 (minimum supported version)
- Python 3.12 (current latest tested)

**To Add Versions**:
```yaml
strategy:
  matrix:
    python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
```

## Best Practices

### Security
1. **Regular Audits**: Run `make security-check` weekly
2. **Dependency Updates**: Keep dependencies updated to avoid vulnerabilities
3. **Allowlist Review**: Quarterly review of allowlisted vulnerabilities
4. **Patch Management**: Prioritize high-risk vulnerabilities for removal

### Coverage
1. **Test Writing**: Focus on uncovered lines shown in reports
2. **Critical Paths**: Ensure core functionality is well-tested
3. **Edge Cases**: Test error conditions and edge cases
4. **Integration Tests**: Add end-to-end tests for workflows

### CI/CD
1. **Fast Feedback**: Keep CI runs under 5 minutes when possible
2. **Caching**: Use dependency caching to speed up builds
3. **Parallel Testing**: Test matrix runs in parallel
4. **Clear Failures**: Provide actionable error messages

## Maintenance

### Monthly Tasks
- [ ] Review and update dependencies
- [ ] Check for new security vulnerabilities
- [ ] Review coverage reports and add tests for uncovered areas
- [ ] Update allowlist if needed

### Quarterly Tasks
- [ ] Full security audit
- [ ] Coverage threshold evaluation
- [ ] Python version support review
- [ ] CI/CD pipeline optimization

## Troubleshooting Guide

### Common Issues

**"pip check failed"**
- Cause: Version conflicts between dependencies
- Solution: Update requirements.txt or use pip-tools for resolution

**"pip audit found unapproved vulnerabilities"**
- Cause: New security vulnerabilities discovered
- Solution: Update dependencies or add to allowlist after risk assessment

**"Coverage check failed - below threshold"**
- Cause: New code without sufficient tests
- Solution: Write tests for uncovered functionality

**"CI failed on Python 3.8"**
- Cause: Using features not available in Python 3.8
- Solution: Update code for compatibility or adjust Python version matrix

### Debug Commands

```bash
# Debug pip-audit issues
pip-audit --verbose --format=json

# Debug coverage issues
pytest --cov=src --cov-report=term-missing --cov-report=html

# Debug CI issues locally
act pull_request  # Run GitHub Actions locally
```

## Support

For issues with the automation system:

1. **Check logs** in validation results and CI output
2. **Review this document** for configuration guidance
3. **Check GitHub Issues** for known problems
4. **Create new issue** with detailed error information

Include:
- Validation results JSON
- CI logs (if applicable)
- Steps to reproduce
- Expected vs actual behavior