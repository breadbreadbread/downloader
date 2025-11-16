"""HTTP client with retry logic, header rotation, and smart backoff."""

import logging
import random
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import settings

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP client with robust retry logic and header rotation.

    Features:
    - Automatic retry with exponential backoff
    - User-Agent rotation on 403 errors
    - Desktop browser headers
    - Request/response logging at DEBUG level
    - Respect for Retry-After headers
    """

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds (defaults to settings.TIMEOUT)
        """
        self.timeout = timeout or settings.TIMEOUT
        self._session = None
        self._user_agent_index = 0
        self._host_user_agents: Dict[str, str] = {}

    def _create_session(self, user_agent: Optional[str] = None) -> requests.Session:
        """
        Create a new requests session with retry configuration.

        Args:
            user_agent: Optional user agent override

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=settings.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504, 403],
            allowed_methods=[
                "HEAD",
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
            ],
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        ua = user_agent or self._get_next_user_agent()
        headers = self._get_default_headers(ua)
        session.headers.update(headers)

        return session

    def _get_default_headers(self, user_agent: str) -> Dict[str, str]:
        """
        Get default browser-like headers.

        Args:
            user_agent: User-Agent string

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

    def _get_next_user_agent(self) -> str:
        """
        Get next User-Agent from pool with jittered selection.

        Returns:
            User-Agent string
        """
        pool = settings.USER_AGENT_POOL

        # Add jitter to avoid predictable patterns
        if len(pool) > 1:
            self._user_agent_index = random.randint(0, len(pool) - 1)

        return pool[self._user_agent_index % len(pool)]

    def _get_user_agent_for_host(self, host: str) -> str:
        """
        Get or assign consistent User-Agent for a specific host.

        Args:
            host: Hostname

        Returns:
            User-Agent string
        """
        if host not in self._host_user_agents:
            self._host_user_agents[host] = self._get_next_user_agent()

        return self._host_user_agents[host]

    def _rotate_user_agent_for_host(self, host: str) -> str:
        """
        Rotate to a new User-Agent for a specific host.

        Args:
            host: Hostname

        Returns:
            New User-Agent string
        """
        current_ua = self._host_user_agents.get(host)
        pool = settings.USER_AGENT_POOL

        # Get a different UA from the pool
        available_uas = [ua for ua in pool if ua != current_ua]
        if available_uas:
            new_ua = random.choice(available_uas)
        else:
            new_ua = self._get_next_user_agent()

        self._host_user_agents[host] = new_ua
        logger.debug(f"Rotated User-Agent for {host}")

        return new_ua

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        allow_redirects: bool = True,
        stream: bool = False,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Perform GET request with retry and header rotation logic.

        Args:
            url: URL to request
            headers: Optional additional headers
            allow_redirects: Whether to follow redirects
            stream: Whether to stream response
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object

        Raises:
            requests.RequestException: On request failure after all retries
        """
        host = urlparse(url).netloc
        attempt = 0
        max_attempts = settings.MAX_RETRIES + 1

        while attempt < max_attempts:
            attempt += 1

            try:
                # Create session with appropriate User-Agent
                if attempt > 1:
                    # On retry, rotate User-Agent for 403 errors
                    user_agent = self._rotate_user_agent_for_host(host)
                else:
                    user_agent = self._get_user_agent_for_host(host)

                session = self._create_session(user_agent)

                # Merge custom headers if provided
                request_headers = session.headers.copy()
                if headers:
                    request_headers.update(headers)

                # Add referer hint when available
                if attempt > 1 and host:
                    request_headers["Referer"] = f"https://{host}/"

                logger.debug(
                    f"HTTP GET {host} (attempt {attempt}/{max_attempts}): "
                    f"UA={user_agent[:50]}..."
                )

                response = session.get(
                    url,
                    headers=request_headers,
                    timeout=self.timeout,
                    allow_redirects=allow_redirects,
                    stream=stream,
                    **kwargs,
                )

                # Log response status
                logger.debug(
                    f"HTTP {response.status_code} from {host} " f"(attempt {attempt})"
                )

                # Handle 403 specifically
                if response.status_code == 403 and attempt < max_attempts:
                    logger.warning(
                        f"Received 403 Forbidden from {host}, "
                        f"retrying with fresh headers (attempt {attempt + 1}/{max_attempts})"
                    )
                    time.sleep(settings.RETRY_DELAY * attempt)
                    continue

                # Raise for other error status codes
                response.raise_for_status()

                # Success - honor request delay before next request
                if settings.REQUEST_DELAY > 0:
                    time.sleep(settings.REQUEST_DELAY)

                return response

            except requests.HTTPError as e:
                if e.response.status_code == 403 and attempt < max_attempts:
                    # Already logged above, just continue retry loop
                    continue

                # For other HTTP errors, provide detailed error message
                error_msg = self._format_http_error(e, host, attempt)
                logger.error(error_msg)

                if attempt >= max_attempts:
                    raise requests.RequestException(error_msg) from e

                # Exponential backoff for other errors
                time.sleep(settings.RETRY_DELAY * (2 ** (attempt - 1)))

            except requests.RequestException as e:
                logger.warning(
                    f"Request error for {host} (attempt {attempt}/{max_attempts}): {str(e)}"
                )

                if attempt >= max_attempts:
                    raise

                time.sleep(settings.RETRY_DELAY * attempt)

        # Should not reach here, but just in case
        raise requests.RequestException(
            f"Failed to fetch {url} after {max_attempts} attempts"
        )

    def _format_http_error(
        self, error: requests.HTTPError, host: str, attempt: int
    ) -> str:
        """
        Format HTTP error with status code and response snippet.

        Args:
            error: HTTPError exception
            host: Hostname
            attempt: Attempt number

        Returns:
            Formatted error message
        """
        response = error.response
        status_code = response.status_code

        # Get body snippet (avoid logging sensitive data)
        try:
            body_snippet = response.text[:200] if response.text else ""
            # Sanitize - remove potential sensitive data patterns
            import re

            body_snippet = re.sub(r"token=[^&\s]+", "token=***", body_snippet)
            body_snippet = re.sub(r"key=[^&\s]+", "key=***", body_snippet)
        except Exception:
            body_snippet = "<unable to read response body>"

        return (
            f"HTTP {status_code} from {host} after {attempt} attempts. "
            f"Response snippet: {body_snippet}"
        )

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Perform POST request.

        Args:
            url: URL to request
            data: Form data to send
            json: JSON data to send
            headers: Optional additional headers
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object

        Raises:
            requests.RequestException: On request failure
        """
        host = urlparse(url).netloc
        user_agent = self._get_user_agent_for_host(host)
        session = self._create_session(user_agent)

        # Merge custom headers if provided
        request_headers = session.headers.copy()
        if headers:
            request_headers.update(headers)

        logger.debug(f"HTTP POST {host}: UA={user_agent[:50]}...")

        response = session.post(
            url,
            data=data,
            json=json,
            headers=request_headers,
            timeout=self.timeout,
            **kwargs,
        )

        logger.debug(f"HTTP {response.status_code} from {host}")

        response.raise_for_status()

        # Honor request delay
        if settings.REQUEST_DELAY > 0:
            time.sleep(settings.REQUEST_DELAY)

        return response

    def close(self):
        """Close the session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
