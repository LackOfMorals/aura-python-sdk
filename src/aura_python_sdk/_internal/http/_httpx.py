"""The default transport, backed by httpx.

This is the only module in the SDK that imports httpx (enforced by
tests/unit/test_import_boundaries.py). Every httpx type and exception is translated to the SDK's
own types at this boundary.
"""

from __future__ import annotations

import ssl

import httpx

from aura_python_sdk._errors import AuraConnectionError, AuraResponseError, AuraTimeoutError
from aura_python_sdk._transport import HttpRequest, HttpResponse

# Mirrors the Go SDK's http.Transport settings.
_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=90.0)

# httpx errors raised before any request bytes reach the server, so retrying cannot duplicate
# a mutation.
_NOT_SENT_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)


def _tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


class HttpxTransport:
    """An :class:`~aura_python_sdk.HttpTransport` backed by a pooled ``httpx.Client``."""

    def __init__(self, *, _httpx_transport: httpx.BaseTransport | None = None) -> None:
        # _httpx_transport is only for tests; it replaces the network layer below httpx.
        self._client = httpx.Client(
            verify=_tls_context(),
            limits=_LIMITS,
            follow_redirects=True,
            transport=_httpx_transport,
        )

    def send(self, request: HttpRequest) -> HttpResponse:
        try:
            with self._client.stream(
                request.method,
                request.url,
                headers=dict(request.headers),
                content=request.body,
                timeout=httpx.Timeout(request.timeout),
            ) as response:
                body = self._read_limited(response, request.max_response_size)
                return HttpResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers.items()),
                    body=body,
                )
        except httpx.TimeoutException as exc:
            raise AuraTimeoutError(
                f"request timed out: {exc}", request_sent=not isinstance(exc, _NOT_SENT_ERRORS)
            ) from exc
        except httpx.TransportError as exc:
            raise AuraConnectionError(
                f"request failed: {exc}", request_sent=not isinstance(exc, _NOT_SENT_ERRORS)
            ) from exc

    @staticmethod
    def _read_limited(response: httpx.Response, limit: int) -> bytes:
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_bytes():
            size += len(chunk)
            if size > limit:
                raise AuraResponseError(f"response body exceeded limit of {limit} bytes")
            chunks.append(chunk)
        return b"".join(chunks)

    def close(self) -> None:
        self._client.close()
