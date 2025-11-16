"""Tests for HTTP client with retry logic and header rotation."""

import unittest
from unittest.mock import MagicMock, Mock, patch

import requests
from requests.exceptions import HTTPError, RequestException

from src.config import settings
from src.network.http_client import HTTPClient


class TestHTTPClient(unittest.TestCase):
    """Test HTTP client functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = HTTPClient()
        # Store original settings
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
        self.client.close()

    def test_get_success(self):
        """Test successful GET request."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Success"
            mock_get.return_value = mock_response

            response = self.client.get("https://example.com")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "Success")

    def test_user_agent_rotation(self):
        """Test User-Agent rotation across requests."""
        user_agents = []

        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Make multiple requests to same host
            for _ in range(3):
                self.client.get("https://example.com/page1")
                # Extract User-Agent from the session headers
                call_args = mock_get.call_args
                if call_args and "headers" in call_args[1]:
                    user_agents.append(call_args[1]["headers"].get("User-Agent"))

        # At least one User-Agent should be set
        self.assertTrue(any(ua for ua in user_agents))

    def test_403_retry_with_header_rotation(self):
        """Test retry with header rotation on 403 error."""
        with patch("requests.Session.get") as mock_get:
            # First attempt returns 403
            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.raise_for_status.side_effect = HTTPError(
                response=mock_response_403
            )

            # Second attempt succeeds
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.text = "Success after retry"

            mock_get.side_effect = [mock_response_403, mock_response_200]

            response = self.client.get("https://example.com")

            # Should succeed after retry
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "Success after retry")

            # Should have made 2 attempts
            self.assertEqual(mock_get.call_count, 2)

    def test_403_exhausts_retries(self):
        """Test that 403 errors eventually fail after max retries."""
        with patch("requests.Session.get") as mock_get:
            # All attempts return 403
            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.raise_for_status.side_effect = HTTPError(
                response=mock_response_403
            )

            mock_get.return_value = mock_response_403

            # Should raise exception after retries exhausted
            with self.assertRaises(RequestException):
                self.client.get("https://example.com")

            # Should have made max_retries + 1 attempts
            self.assertEqual(mock_get.call_count, settings.MAX_RETRIES + 1)

    def test_retry_on_500_error(self):
        """Test retry on 500 server error."""
        with patch("requests.Session.get") as mock_get:
            # First attempt returns 500
            mock_response_500 = Mock()
            mock_response_500.status_code = 500
            mock_response_500.raise_for_status.side_effect = HTTPError(
                response=mock_response_500
            )

            # Second attempt succeeds
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.text = "Success"

            mock_get.side_effect = [mock_response_500, mock_response_200]

            response = self.client.get("https://example.com")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(mock_get.call_count, 2)

    def test_retry_on_503_error(self):
        """Test retry on 503 service unavailable."""
        with patch("requests.Session.get") as mock_get:
            # First attempt returns 503
            mock_response_503 = Mock()
            mock_response_503.status_code = 503
            mock_response_503.raise_for_status.side_effect = HTTPError(
                response=mock_response_503
            )

            # Second attempt succeeds
            mock_response_200 = Mock()
            mock_response_200.status_code = 200

            mock_get.side_effect = [mock_response_503, mock_response_200]

            response = self.client.get("https://example.com")

            self.assertEqual(response.status_code, 200)

    def test_custom_headers_override(self):
        """Test custom headers override default headers."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            custom_headers = {"X-Custom-Header": "test-value"}
            self.client.get("https://example.com", headers=custom_headers)

            call_args = mock_get.call_args
            request_headers = call_args[1]["headers"]

            # Custom header should be present
            self.assertIn("X-Custom-Header", request_headers)
            self.assertEqual(request_headers["X-Custom-Header"], "test-value")

    def test_default_browser_headers(self):
        """Test that default browser headers are set."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            self.client.get("https://example.com")

            call_args = mock_get.call_args
            request_headers = call_args[1]["headers"]

            # Check for browser-like headers
            self.assertIn("User-Agent", request_headers)
            self.assertIn("Accept", request_headers)
            self.assertIn("Accept-Language", request_headers)

    def test_post_request(self):
        """Test POST request."""
        with patch("requests.Session.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "POST success"
            mock_post.return_value = mock_response

            response = self.client.post(
                "https://example.com/api", json={"key": "value"}
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "POST success")

    def test_referer_added_on_retry(self):
        """Test that Referer header is added on retry attempts."""
        with patch("requests.Session.get") as mock_get:
            # First attempt returns 403
            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.raise_for_status.side_effect = HTTPError(
                response=mock_response_403
            )

            # Second attempt succeeds
            mock_response_200 = Mock()
            mock_response_200.status_code = 200

            mock_get.side_effect = [mock_response_403, mock_response_200]

            self.client.get("https://example.com/page")

            # Second call should have Referer
            second_call_headers = mock_get.call_args_list[1][1]["headers"]
            self.assertIn("Referer", second_call_headers)
            self.assertIn("example.com", second_call_headers["Referer"])

    def test_context_manager(self):
        """Test HTTP client as context manager."""
        with HTTPClient() as client:
            with patch("requests.Session.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_get.return_value = mock_response

                response = client.get("https://example.com")
                self.assertEqual(response.status_code, 200)

    def test_timeout_configuration(self):
        """Test custom timeout configuration."""
        custom_timeout = 60
        client = HTTPClient(timeout=custom_timeout)

        self.assertEqual(client.timeout, custom_timeout)

    def test_error_message_formatting(self):
        """Test error message includes status code and response snippet."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Page not found - detailed error message here"
            mock_response.raise_for_status.side_effect = HTTPError(
                response=mock_response
            )

            mock_get.return_value = mock_response

            with self.assertRaises(RequestException) as context:
                self.client.get("https://example.com/notfound")

            error_msg = str(context.exception)
            # Error message should contain status code
            self.assertIn("404", error_msg)


class TestHTTPClientIntegration(unittest.TestCase):
    """Integration-style tests for HTTP client."""

    def test_recovery_from_initial_403(self):
        """Test successful recovery from initial 403 error."""
        with patch("requests.Session.get") as mock_get:
            # Simulate server returning 403 then 200
            responses = []

            # First response: 403
            response_403 = Mock()
            response_403.status_code = 403
            response_403.raise_for_status.side_effect = HTTPError(response=response_403)
            responses.append(response_403)

            # Second response: 200
            response_200 = Mock()
            response_200.status_code = 200
            response_200.text = "<html>Success</html>"
            responses.append(response_200)

            mock_get.side_effect = responses

            client = HTTPClient()

            # Save settings
            original_retry_delay = settings.RETRY_DELAY
            settings.RETRY_DELAY = 0.1

            try:
                response = client.get("https://example.com")

                # Should succeed after retry
                self.assertEqual(response.status_code, 200)
                self.assertIn("Success", response.text)

                # Should have attempted twice
                self.assertEqual(mock_get.call_count, 2)
            finally:
                settings.RETRY_DELAY = original_retry_delay
                client.close()


if __name__ == "__main__":
    unittest.main()
