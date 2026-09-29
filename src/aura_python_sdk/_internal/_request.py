"""Authenticated Aura API requests (Go: internal/api RequestService)."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import quote, urlencode

from aura_python_sdk._errors import AuraResponseError, api_error_from_response
from aura_python_sdk._internal._auth import TokenManager
from aura_python_sdk._internal.http._service import HttpService

QueryParams = Mapping[str, str | None]


def build_path(*segments: str) -> str:
    """Join path segments, percent-encoding each so an ID can never alter the path."""
    return "/".join(quote(segment, safe="") for segment in segments)


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status_code: int
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""

    def json(self) -> object:
        try:
            return json.loads(self.body)
        except ValueError as exc:
            raise AuraResponseError("response body is not valid JSON") from exc


class RequestService:
    """Adds authentication, headers and URL handling, and maps error responses to exceptions.

    A relative path such as ``instances/abc`` resolves to
    ``{base_url}/{api_version}/instances/abc``.
    An absolute ``http(s)://`` URL, such as a Prometheus metrics endpoint, is used unchanged but
    still gets the Aura bearer token.
    """

    def __init__(
        self,
        *,
        http: HttpService,
        auth: TokenManager,
        base_url: str,
        api_version: str,
        user_agent: str,
        default_headers: Mapping[str, str],
        timeout: float,
        logger: logging.Logger,
    ) -> None:
        self._http = http
        self._auth = auth
        self._endpoint_base = f"{base_url}/{api_version}"
        self._user_agent = user_agent
        self._default_headers = dict(default_headers)
        self._timeout = timeout
        self._logger = logger

    def get(self, path: str, *, params: QueryParams | None = None) -> ApiResponse:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json_body: object = None) -> ApiResponse:
        return self.request("POST", path, json_body=json_body)

    def patch(self, path: str, *, json_body: object = None) -> ApiResponse:
        return self.request("PATCH", path, json_body=json_body)

    def put(self, path: str, *, json_body: object = None) -> ApiResponse:
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str) -> ApiResponse:
        return self.request("DELETE", path)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json_body: object = None,
    ) -> ApiResponse:
        # One deadline covers the token fetch, every attempt and every backoff, like the
        # context.WithTimeout that wraps each Go service method.
        deadline = self._http.clock() + self._timeout
        url = self._resolve_url(path, params)

        headers = dict(self._default_headers)
        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = self._user_agent
        headers["Authorization"] = self._auth.authorization_header(deadline=deadline)

        body = None if json_body is None else json.dumps(json_body, separators=(",", ":")).encode()

        self._logger.debug("making authenticated API request", extra={"method": method, "url": url})
        response = self._http.send(method, url, headers, body, deadline=deadline)

        if not 200 <= response.status_code < 300:
            if response.status_code == 401:
                # The token may have been revoked; make the next call fetch a fresh one.
                self._auth.invalidate()
            error = api_error_from_response(response.status_code, response.body, response.headers)
            self._logger.debug(
                "API returned error",
                extra={"method": method, "url": url, "status": response.status_code},
            )
            raise error

        return ApiResponse(response.status_code, response.headers, response.body)

    def _resolve_url(self, path: str, params: QueryParams | None) -> str:
        if path.startswith(("https://", "http://")):
            url = path
        else:
            url = f"{self._endpoint_base}/{path.lstrip('/')}"
        query = {key: value for key, value in (params or {}).items() if value is not None}
        if query:
            url += ("&" if "?" in url else "?") + urlencode(query)
        return url
