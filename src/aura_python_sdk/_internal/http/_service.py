"""Retries and response limits on top of an HttpTransport (Go: internal/httpclient)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping

from aura_python_sdk._errors import AuraConnectionError, AuraResponseError, AuraTimeoutError
from aura_python_sdk._transport import HttpRequest, HttpResponse, HttpTransport

# Methods that are safe to repeat when the server may already have received the request.
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})

RETRY_WAIT_MIN = 1.0
RETRY_WAIT_MAX = 5.0


class HttpService:
    """Sends requests through a transport, retrying network failures only.

    As in the Go SDK, a response with any HTTP status is final and is never retried. A network
    failure is retried up to ``max_retries`` times with exponential backoff (1 s doubling to 5 s).
    If the request may have reached the server, only idempotent methods are retried, so a
    ``POST /instances`` is never sent twice. No attempt or backoff runs past ``deadline``.
    """

    def __init__(
        self,
        transport: HttpTransport,
        *,
        max_retries: int,
        max_response_size: int,
        logger: logging.Logger,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._transport = transport
        self._max_retries = max_retries
        self._max_response_size = max_response_size
        self._logger = logger
        self._clock = clock
        self._sleep = sleep

    @property
    def clock(self) -> Callable[[], float]:
        return self._clock

    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        *,
        deadline: float,
    ) -> HttpResponse:
        attempt = 0
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise AuraTimeoutError("request deadline exceeded", request_sent=False)
            request = HttpRequest(
                method=method,
                url=url,
                headers=headers,
                body=body,
                timeout=remaining,
                max_response_size=self._max_response_size,
            )
            self._logger.debug("sending HTTP request", extra={"method": method, "url": url})
            try:
                response = self._transport.send(request)
            except AuraConnectionError as exc:
                wait = min(RETRY_WAIT_MAX, RETRY_WAIT_MIN * 2**attempt)
                if (
                    attempt >= self._max_retries
                    or not self._is_retryable(method, exc)
                    or self._clock() + wait >= deadline
                ):
                    raise
                self._logger.debug(
                    "retrying HTTP request after network error",
                    extra={"method": method, "url": url, "attempt": attempt + 1, "error": str(exc)},
                )
                self._sleep(wait)
                attempt += 1
                continue

            if len(response.body) > self._max_response_size:
                raise AuraResponseError(
                    f"response body exceeded limit of {self._max_response_size} bytes"
                )
            self._logger.debug(
                "HTTP response received",
                extra={"method": method, "url": url, "status": response.status_code},
            )
            return response

    @staticmethod
    def _is_retryable(method: str, exc: AuraConnectionError) -> bool:
        return not exc.request_sent or method.upper() in _IDEMPOTENT_METHODS
