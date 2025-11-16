"""Tests for HTTP hardening and error handling."""

import unittest
from unittest.mock import patch, MagicMock
import requests
from pathlib import Path

from src.downloader.doi_resolver import DOIResolver
from src.downloader.arxiv import ArxivDownloader
from src.models import Reference, DownloadStatus


class TestHTTPHardening(unittest.TestCase):
    """Test HTTP hardening features across all downloaders."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.doi_resolver = DOIResolver()
        self.arxiv_downloader = ArxivDownloader()
        
        # Test references
        self.doi_reference = Reference(
            raw_text="Test paper with DOI",
            doi="10.1234/test.doi.2023"
        )
        self.arxiv_reference = Reference(
            raw_text="Test arXiv paper",
            arxiv_id="2301.12345"
        )
    
    def test_timeout_handling_doi_resolver(self):
        """Test DOI resolver handles timeouts gracefully."""
        with patch('requests.Session.get', side_effect=requests.Timeout()):
            result = self.doi_resolver.download(
                self.doi_reference, 
                Path("./test_output.pdf")
            )
            
            self.assertIsNotNone(result)
            # Timeouts in _get_pdf_url_from_doi return None, causing NOT_FOUND
            self.assertEqual(result.status, DownloadStatus.NOT_FOUND)
            self.assertIn("No direct PDF URL found", result.error_message)
    
    def test_timeout_handling_arxiv(self):
        """Test arXiv downloader handles timeouts gracefully."""
        with patch('requests.Session.get', side_effect=requests.Timeout()):
            result = self.arxiv_downloader.download(
                self.arxiv_reference,
                Path("./test_output.pdf")
            )
            
            self.assertIsNotNone(result)
            # arXiv downloader catches exceptions and returns NOT_FOUND
            self.assertEqual(result.status, DownloadStatus.NOT_FOUND)
            self.assertIn("Could not find preprint", result.error_message)
    
    def test_connection_error_handling(self):
        """Test connection errors are handled gracefully."""
        with patch('requests.Session.get', side_effect=requests.ConnectionError()):
            result = self.doi_resolver.download(
                self.doi_reference,
                Path("./test_output.pdf")
            )
            
            self.assertIsNotNone(result)
            # Connection errors in _get_pdf_url_from_doi return None, causing NOT_FOUND
            self.assertEqual(result.status, DownloadStatus.NOT_FOUND)
    
    def test_http_403_handling(self):
        """Test HTTP 403 Forbidden responses."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        
        with patch('requests.Session.get', return_value=mock_response):
            result = self.doi_resolver.download(
                self.doi_reference,
                Path("./test_output.pdf")
            )
            
            self.assertIsNotNone(result)
            # HTTP errors in _get_pdf_url_from_doi return None, causing NOT_FOUND
            self.assertEqual(result.status, DownloadStatus.NOT_FOUND)
    
    def test_user_agent_header_set(self):
        """Test User-Agent header is properly set."""
        # Test by checking that http_client creates sessions with proper User-Agent
        # We'll verify this by checking the user agent pool is not empty
        from src.config import settings
        
        # Check that User-Agent pool is configured
        self.assertIsNotNone(settings.USER_AGENT_POOL)
        self.assertGreater(len(settings.USER_AGENT_POOL), 0)
        
        # Verify the user agents are valid strings
        for ua in settings.USER_AGENT_POOL:
            self.assertIsInstance(ua, str)
            self.assertGreater(len(ua), 10)  # User agents should be substantial
            self.assertIn("Mozilla", ua)  # Should look like a browser UA
    
    def test_ssl_verification_enabled(self):
        """Test SSL verification is enabled by default."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        
        with patch('requests.Session.get', return_value=mock_response) as mock_get:
            self.doi_resolver.download(self.doi_reference, Path("./test.pdf"))
            
            # Verify SSL verification is enabled (default behavior)
            call_args = mock_get.call_args
            # If verify is not specified, it defaults to True
            verify_value = call_args[1].get('verify', True)
            self.assertTrue(verify_value)
    
    def test_session_timeout_configuration(self):
        """Test session timeout is configured."""
        self.assertEqual(self.doi_resolver.timeout, 30)
        self.assertEqual(self.arxiv_downloader.timeout, 30)
    
    def test_arxiv_rate_limiting_configuration(self):
        """Test arXiv rate limiting is configured in settings."""
        from src.config import settings
        self.assertGreater(settings.ARXIV_DELAY, 2.0)  # Should be at least 3 seconds


if __name__ == "__main__":
    unittest.main()