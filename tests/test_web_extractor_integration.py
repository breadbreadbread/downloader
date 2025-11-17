"""Integration tests for WebExtractor with HTTP client."""

import unittest
from unittest.mock import Mock, patch

from src.config import settings
from src.extractor.web_extractor import WebExtractor


class TestWebExtractorIntegration(unittest.TestCase):
    """Integration tests for WebExtractor with HTTP client."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = WebExtractor()
        # Save original settings
        self.original_max_retries = settings.MAX_RETRIES
        self.original_retry_delay = settings.RETRY_DELAY
        self.original_request_delay = settings.REQUEST_DELAY

        # Set test-friendly values
        settings.MAX_RETRIES = 2
        settings.RETRY_DELAY = 0.1
        settings.REQUEST_DELAY = 0

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original settings
        settings.MAX_RETRIES = self.original_max_retries
        settings.RETRY_DELAY = self.original_retry_delay
        settings.REQUEST_DELAY = self.original_request_delay

    def test_web_extractor_success(self):
        """Test successful web extraction."""
        with patch("requests.Session.get") as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """
            <html>
                <body>
                    <h2>References</h2>
                    <ol>
                        <li>Smith, J. (2023). Example Paper. Nature, 123, 456-789.</li>
                        <li>Johnson, A. (2022). Another Paper. Science, 234, 123-456.</li>
                    </ol>
                </body>
            </html>
            """
            mock_get.return_value = mock_response

            result = self.extractor.extract("https://example.com/paper")

            # Should succeed
            self.assertEqual(len(result.extraction_errors), 0)
            self.assertGreater(result.total_references, 0)

    def test_web_extractor_recovers_from_403(self):
        """Test that WebExtractor recovers from initial 403 error."""
        with patch("requests.Session.get") as mock_get:
            # First attempt returns 403
            from requests.exceptions import HTTPError

            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.raise_for_status.side_effect = HTTPError(
                response=mock_response_403
            )

            # Second attempt succeeds
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.text = """
            <html>
                <body>
                    <h2>References</h2>
                    <p>[1] Smith, J. (2023). Test Paper. Journal, 1, 1-10.</p>
                </body>
            </html>
            """

            mock_get.side_effect = [mock_response_403, mock_response_200]

            result = self.extractor.extract("https://example.com/paper")

            # Should succeed after retry
            self.assertEqual(len(result.extraction_errors), 0)

            # Should have made 2 attempts
            self.assertEqual(mock_get.call_count, 2)

    def test_web_extractor_handles_persistent_403(self):
        """Test that WebExtractor handles persistent 403 errors gracefully."""
        with patch("requests.Session.get") as mock_get:
            # All attempts return 403
            from requests.exceptions import HTTPError

            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.raise_for_status.side_effect = HTTPError(
                response=mock_response_403
            )

            mock_get.return_value = mock_response_403

            result = self.extractor.extract("https://example.com/paper")

            # Should have error message
            self.assertGreater(len(result.extraction_errors), 0)
            self.assertIn("Error fetching URL", result.extraction_errors[0])

            # Should have made max_retries + 1 attempts
            self.assertEqual(mock_get.call_count, settings.MAX_RETRIES + 1)

    def test_web_extractor_invalid_url(self):
        """Test that WebExtractor handles invalid URLs."""
        result = self.extractor.extract("not-a-valid-url")

        # Should have error message
        self.assertGreater(len(result.extraction_errors), 0)
        self.assertIn("Invalid URL format", result.extraction_errors[0])

    def test_web_extractor_empty_content(self):
        """Test that WebExtractor handles empty content."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body></body></html>"
            mock_get.return_value = mock_response

            result = self.extractor.extract("https://example.com/empty")

            # Should succeed but with no references
            self.assertEqual(len(result.extraction_errors), 0)
            self.assertEqual(result.total_references, 0)


if __name__ == "__main__":
    unittest.main()
