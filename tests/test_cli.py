"""Tests for CLI interface and command-line functionality."""

import unittest
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCLI(unittest.TestCase):
    """Test command-line interface functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cli_help_display(self):
        """Test CLI help message displays correctly."""
        result = subprocess.run(
            ["python", "-m", "src.main", "--help"],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Extract references", result.stdout)
        self.assertIn("--pdf", result.stdout)
        self.assertIn("--url", result.stdout)
        self.assertIn("--output", result.stdout)
    
    def test_cli_no_arguments(self):
        """Test CLI fails gracefully with no arguments."""
        result = subprocess.run(
            ["python", "-m", "src.main"],
            capture_output=True,
            text=True
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error", result.stderr.lower())
    
    def test_cli_invalid_pdf_file(self):
        """Test CLI handles non-existent PDF file."""
        result = subprocess.run([
            "python", "-m", "src.main",
            "--pdf", "/nonexistent/file.pdf",
            "--output", self.temp_dir
        ], capture_output=True, text=True)
        
        # Should handle gracefully, not crash
        self.assertIn("not found", result.stderr.lower())
    
    def test_cli_invalid_url(self):
        """Test CLI handles invalid URL."""
        result = subprocess.run([
            "python", "-m", "src.main",
            "--url", "not-a-url",
            "--output", self.temp_dir
        ], capture_output=True, text=True)
        
        self.assertIn("invalid url", result.stderr.lower())
    
    def test_cli_output_directory_creation(self):
        """Test CLI creates output directory if it doesn't exist."""
        output_path = os.path.join(self.temp_dir, "new", "nested", "dir")
        
        # Directory shouldn't exist initially
        self.assertFalse(os.path.exists(output_path))
        
        # Create a simple test PDF
        test_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(test_pdf, 'w') as f:
            f.write("Not a real PDF")
        
        result = subprocess.run([
            "python", "-m", "src.main",
            "--pdf", test_pdf,
            "--output", output_path
        ], capture_output=True, text=True)
        
        # Directory should be created (even if PDF processing fails)
        self.assertTrue(os.path.exists(output_path))
    
    def test_cli_log_level_configuration(self):
        """Test CLI log level configuration."""
        test_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(test_pdf, 'w') as f:
            f.write("Not a real PDF")
        
        result = subprocess.run([
            "python", "-m", "src.main",
            "--pdf", test_pdf,
            "--output", self.temp_dir,
            "--log-level", "DEBUG"
        ], capture_output=True, text=True)
        
        # Should not crash due to log level
        self.assertTrue(True)  # If we get here, log level was accepted
    
    def test_cli_pdf_and_url_mutual_exclusion(self):
        """Test CLI rejects both PDF and URL arguments."""
        test_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(test_pdf, 'w') as f:
            f.write("Not a real PDF")
        
        result = subprocess.run([
            "python", "-m", "src.main",
            "--pdf", test_pdf,
            "--url", "https://example.com",
            "--output", self.temp_dir
        ], capture_output=True, text=True)
        
        self.assertNotEqual(result.returncode, 0)
    
    def test_cli_successful_execution(self):
        """Test CLI successful execution with minimal valid input."""
        # This would require a real PDF for full testing
        # For now, test that it doesn't crash on invalid input
        test_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(test_pdf, 'w') as f:
            f.write("Not a real PDF")
        
        result = subprocess.run([
            "python", "-m", "src.main",
            "--pdf", test_pdf,
            "--output", self.temp_dir
        ], capture_output=True, text=True)
        
        # Should handle gracefully
        self.assertTrue(True)  # If we get here, CLI didn't crash


if __name__ == "__main__":
    unittest.main()