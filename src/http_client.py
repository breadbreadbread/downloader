"""Shared HTTP client with retry logic and user-agent rotation."""

from __future__ import annotations

import itertools
import logging
import time
from typing import Optional, Sequence, Set

import requests

from src.config import settings

DEFAULT_RETRYABLE_STATUS_CODES: Set[int] = {403, 429, 500, 502, 503, 504}
DEFAULT_ROTATE_STATUS_CODES: Set[int] = {403, 429}


class HTTPClientError(Exception):
    """Error raised when the HTTP client exhausts retries."""

    def __init__(
        self,
        message: str,
        response: Optional[requests.Response] = None,
        exception: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.response = response
        self.exception = exception
        self.status_code: Optional[int] = response.status_code if response is not None else None


class HTTPClient:
    """HTTP client wrapper that adds retries, backoff, and user-agent rotation."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        *,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None,
        user_agents: Optional[Sequence[str]] = None,
        retryable_statuses: Optional[Sequence[int]] = None,
        rotate_statuses: Optional[Sequence[int]] = None,
        verify: bool = True,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)

        self.max_retries = max_retries if max_retries is not None else settings.MAX_RETRIES
        self.retry_delay = retry_delay if retry_delay is not None else settings.RETRY_DELAY
        self.backoff_factor = (
            backoff_factor if backoff_factor is not None else getattr(settings, "RETRY_BACKOFF_FACTOR", 1.0)
        )
        self.verify = verify

        configured_agents = list(user_agents) if user_agents is not None else []
        if not configured_agents:
            if getattr(settings, "USER_AGENTS", None):
                configured_agents = list(settings.USER_AGENTS)
            elif getattr(settings, "USER_AGENT", None):
                configured_agents = [settings.USER_AGENT]

        if not configured_agents:
            configured_agents = ["ref-downloader/1.0"]

        # Preserve ordering but remove duplicates
        seen = set()
        deduped_agents = []
        for agent in configured_agents:
            if agent and agent not in seen:
                seen.add(agent)
                deduped_agents.append(agent)
        self._user_agents = deduped_agents or ["ref-downloader/1.0"]
        self._user_agent_cycle = itertools.cycle(self._user_agents)
        self._current_user_agent = next(self._user_agent_cycle)
        self.session.headers.setdefault("User-Agent", self._current_user_agent)

        self.retryable_statuses: Set[int] = set(retryable_statuses or DEFAULT_RETRYABLE_STATUS_CODES)
        self.rotate_statuses: Set[int] = set(rotate_statuses or DEFAULT_ROTATE_STATUS_CODES)

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Perform an HTTP request with retry and rotation behaviour."""
        method_upper = method.upper()

        max_retries = kwargs.pop("max_retries", self.max_retries)
        retry_delay = kwargs.pop("retry_delay", self.retry_delay)
        backoff_factor = kwargs.pop("backoff_factor", self.backoff_factor)
        rotate_on_retry = kwargs.pop("rotate_user_agent_on_retry", True)
        retryable_statuses = set(kwargs.pop("retryable_statuses", self.retryable_statuses))
        rotate_statuses = set(kwargs.pop("rotate_statuses", self.rotate_statuses))

        try:
            max_retries = int(max_retries)
        except (TypeError, ValueError):
            max_retries = self.max_retries
        if max_retries < 1:
            max_retries = 1

        try:
            retry_delay = float(retry_delay)
        except (TypeError, ValueError):
            retry_delay = self.retry_delay
        if retry_delay < 0:
            retry_delay = 0.0

        try:
            backoff_factor = float(backoff_factor)
        except (TypeError, ValueError):
            backoff_factor = self.backoff_factor
        if backoff_factor < 1.0:
            backoff_factor = 1.0

        if "timeout" not in kwargs:
            kwargs["timeout"] = settings.TIMEOUT

        verify = kwargs.get("verify", self.verify)
        kwargs["verify"] = verify

        last_response: Optional[requests.Response] = None
        last_exception: Optional[BaseException] = None
        last_detail: Optional[str] = None

        delay = retry_delay

        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                self._sleep(delay)

            try:
                self._ensure_user_agent()
                response = self.session.request(method_upper, url, **kwargs)
                last_response = response
            except requests.RequestException as exc:
                last_exception = exc
                last_detail = str(exc)
                self.logger.warning(
                    "%s %s failed on attempt %s/%s: %s",
                    method_upper,
                    url,
                    attempt,
                    max_retries,
                    exc,
                )
                if attempt == max_retries:
                    break

                if rotate_on_retry:
                    self.rotate_user_agent()

                delay *= backoff_factor
                continue

            if 200 <= response.status_code < 300:
                return response

            last_detail = f"HTTP {response.status_code} {response.reason or ''}".strip()

            if attempt < max_retries and response.status_code in retryable_statuses:
                self.logger.warning(
                    "%s %s returned status %s on attempt %s/%s; retrying",
                    method_upper,
                    url,
                    response.status_code,
                    attempt,
                    max_retries,
                )
                if rotate_on_retry and response.status_code in rotate_statuses:
                    self.rotate_user_agent()

                delay *= backoff_factor
                continue

            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                last_exception = exc
            break

        message = self._build_error_message(method_upper, url, attempt, last_detail, last_response)
        raise HTTPClientError(message, response=last_response, exception=last_exception)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Shortcut for GET requests."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Shortcut for POST requests."""
        return self.request("POST", url, **kwargs)

    def rotate_user_agent(self) -> str:
        """Rotate to the next user-agent in the pool."""
        self._current_user_agent = next(self._user_agent_cycle)
        self.session.headers["User-Agent"] = self._current_user_agent
        self.logger.debug("Rotated User-Agent to: %s", self._current_user_agent)
        return self._current_user_agent

    def _ensure_user_agent(self) -> None:
        if "User-Agent" not in self.session.headers:
            self.session.headers["User-Agent"] = self._current_user_agent

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def _build_error_message(
        self,
        method: str,
        url: str,
        attempts: int,
        detail: Optional[str],
        response: Optional[requests.Response],
    ) -> str:
        attempt_word = "attempt" if attempts == 1 else "attempts"
        base = f"{method} {url} failed after {attempts} {attempt_word}"
        if response is not None and response.status_code:
            base += f" (status {response.status_code})"
        if detail:
            base += f": {detail}"
        return base
