#!/usr/bin/env python3
"""
Dependency validation script for reference-downloader.

This script runs comprehensive dependency and security checks:
1. pip check - verifies no broken requirements
2. pip-audit - checks for known vulnerabilities
3. Coverage validation (optional)
4. Records results for CI/CD integration

Usage:
    python scripts/validate_dependencies.py [--coverage] [--verbose]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DependencyValidator:
    """Validates project dependencies and security."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            "pip_check": {"status": "unknown", "output": "", "error": ""},
            "pip_audit": {
                "status": "unknown",
                "output": "",
                "error": "",
                "vulnerabilities": [],
            },
            "coverage": {
                "status": "unknown",
                "output": "",
                "error": "",
                "percentage": None,
            },
        }

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 5 minutes"
        except Exception as e:
            return -1, "", f"Failed to run command: {e}"

    def check_pip_check(self) -> bool:
        """Run pip check to verify no broken requirements."""
        print("🔍 Running pip check...")
        returncode, stdout, stderr = self.run_command(
            [sys.executable, "-m", "pip", "check"]
        )

        self.results["pip_check"]["output"] = stdout
        self.results["pip_check"]["error"] = stderr

        if returncode == 0:
            print("✅ pip check passed - no broken requirements")
            self.results["pip_check"]["status"] = "passed"
            return True
        else:
            print("❌ pip check failed - broken requirements detected")
            self.results["pip_check"]["status"] = "failed"
            return False

    def check_pip_audit(self) -> bool:
        """Run pip audit to check for security vulnerabilities."""
        print("🔒 Running pip audit...")

        # Run pip-audit with JSON output for parsing
        returncode, stdout, stderr = self.run_command(["pip-audit", "--format", "json"])

        self.results["pip_audit"]["output"] = stdout
        self.results["pip_audit"]["error"] = stderr

        if returncode == 0:
            print("✅ pip audit passed - no vulnerabilities found")
            self.results["pip_audit"]["status"] = "passed"
            return True

        # Parse vulnerabilities from JSON output
        try:
            audit_data = json.loads(stdout)
            vulnerabilities = []
            # Extract vulnerabilities from the dependencies list
            for dep in audit_data.get("dependencies", []):
                for vuln in dep.get("vulns", []):
                    vulnerabilities.append(vuln)

            self.results["pip_audit"]["vulnerabilities"] = vulnerabilities

            # Check if all vulnerabilities are in our allowlist
            # Known vulnerabilities that are approved:
            allowed_vulns = {
                "GHSA-f83h-ghpp-7wcc",  # pdfminer.six insecure deserialization
                "GHSA-4xh5-x5gv-qwph",  # pip tarfile extraction vulnerability (fixed in pip 25.3)
                "PYSEC-2024-48",  # black regex DoS (fixed in black 24.3.0)
            }

            unapproved_vulns = []
            for vuln in vulnerabilities:
                vuln_id = vuln.get("id", "")
                if vuln_id not in allowed_vulns:
                    unapproved_vulns.append(vuln)

            if unapproved_vulns:
                print(
                    f"❌ pip audit found {len(unapproved_vulns)} unapproved vulnerabilities:"
                )
                for vuln in unapproved_vulns:
                    print(
                        f"  - {vuln.get('id', 'Unknown')}: {vuln.get('description', 'No summary')[:100]}..."
                    )
                self.results["pip_audit"]["status"] = "failed"
                return False
            else:
                print(
                    f"⚠️  pip audit found {len(vulnerabilities)} known but approved vulnerabilities"
                )
                self.results["pip_audit"]["status"] = "passed_with_allowed"
                return True

        except json.JSONDecodeError:
            print("❌ Failed to parse pip-audit JSON output")
            print(f"stdout: {stdout[:200]}...")
            print(f"stderr: {stderr[:200]}...")
            self.results["pip_audit"]["status"] = "error"
            return False

    def check_coverage(self) -> bool:
        """Check test coverage if requested."""
        print("📊 Running coverage check...")

        # Run pytest with coverage
        returncode, stdout, stderr = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=src",
                "--cov-report=json",
                "--cov-fail-under=80",
                "-q",
            ]
        )

        self.results["coverage"]["output"] = stdout
        self.results["coverage"]["error"] = stderr

        if returncode == 0:
            # Try to read coverage.json to get exact percentage
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                        total_coverage = coverage_data.get("totals", {}).get(
                            "percent_covered", 0
                        )
                        self.results["coverage"]["percentage"] = total_coverage
                        print(f"✅ Coverage check passed: {total_coverage:.1f}%")
                except (json.JSONDecodeError, KeyError):
                    print("✅ Coverage check passed (percentage unknown)")
            else:
                print("✅ Coverage check passed")

            self.results["coverage"]["status"] = "passed"
            return True
        else:
            print("❌ Coverage check failed - below 80% threshold")
            self.results["coverage"]["status"] = "failed"
            return False

    def save_results(self, output_file: Path) -> None:
        """Save validation results to JSON file."""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Results saved to {output_file}")

    def validate(self, check_coverage: bool = False) -> bool:
        """Run all validation checks."""
        print("🚀 Starting dependency validation...\n")

        all_passed = True

        # Run pip check
        if not self.check_pip_check():
            all_passed = False

        print()

        # Run pip audit
        if not self.check_pip_audit():
            all_passed = False

        print()

        # Run coverage check if requested
        if check_coverage:
            if not self.check_coverage():
                all_passed = False

        print()

        if all_passed:
            print("🎉 All validation checks passed!")
        else:
            print("💥 Some validation checks failed!")

        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate dependencies and security")
    parser.add_argument(
        "--coverage", action="store_true", help="Include test coverage validation"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation-results.json"),
        help="Output file for validation results (default: validation-results.json)",
    )

    args = parser.parse_args()

    # Determine project root
    project_root = Path(__file__).parent.parent

    # Run validation
    validator = DependencyValidator(project_root)
    success = validator.validate(check_coverage=args.coverage)

    # Save results
    validator.save_results(args.output)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
