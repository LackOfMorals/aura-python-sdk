"""OAuth client-credentials token management (Go: internal/api authManager)."""

from __future__ import annotations

import base64
import json
import logging
import threading
from dataclasses import dataclass
from urllib.parse import urlencode

from aura_python_sdk._errors import AuraResponseError, AuthenticationError, api_error_from_response
from aura_python_sdk._internal.http._service import HttpService

# Refresh this many seconds before the token actually expires.
REFRESH_MARGIN = 60.0
MAX_EXPIRES_IN = 86400 * 365


@dataclass(frozen=True, slots=True)
class _Token:
    token_type: str
    access_token: str
    expires_at: float  # on the HttpService clock (monotonic)


class TokenManager:
    """Obtains and caches a bearer token from ``{base_url}/oauth/token``.

    Thread-safe. Concurrent callers that find the token missing or near expiry trigger a single
    refresh between them.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        token_url: str,
        user_agent: str,
        http: HttpService,
        logger: logging.Logger,
    ) -> None:
        credentials = f"{client_id}:{client_secret}".encode()
        self._basic_auth = "Basic " + base64.b64encode(credentials).decode("ascii")
        self._token_url = token_url
        self._user_agent = user_agent
        self._http = http
        self._logger = logger
        self._lock = threading.Lock()
        self._token: _Token | None = None

    def authorization_header(self, *, deadline: float) -> str:
        """Return a valid ``Authorization`` header value, fetching a new token if needed."""
        token = self._token
        if token is None or not self._is_fresh(token):
            with self._lock:
                token = self._token
                if token is None or not self._is_fresh(token):
                    token = self._fetch(deadline=deadline)
                    self._token = token
        return f"{token.token_type} {token.access_token}"

    def invalidate(self) -> None:
        """Drop the cached token so the next request fetches a new one (e.g. after a 401)."""
        with self._lock:
            self._token = None

    def _is_fresh(self, token: _Token) -> bool:
        return self._http.clock() < token.expires_at - REFRESH_MARGIN

    def _fetch(self, *, deadline: float) -> _Token:
        self._logger.debug("obtaining new authentication token")
        response = self._http.send(
            "POST",
            self._token_url,
            {
                "Authorization": self._basic_auth,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self._user_agent,
            },
            urlencode({"grant_type": "client_credentials"}).encode("ascii"),
            deadline=deadline,
        )
        if not 200 <= response.status_code < 300:
            status = response.status_code
            # Any client error from the token endpoint means the credentials were rejected.
            # Rate limits and server errors keep their usual types.
            error_class = None if status == 429 or status >= 500 else AuthenticationError
            self._logger.debug("token request failed", extra={"status": status})
            raise api_error_from_response(
                status, response.body, response.headers, error_class=error_class
            )

        try:
            payload = json.loads(response.body)
            token_type = payload["token_type"]
            access_token = payload["access_token"]
            expires_in = payload["expires_in"]
        except (ValueError, KeyError, TypeError) as exc:
            raise AuraResponseError("failed to parse token response") from exc

        if not isinstance(token_type, str) or token_type.lower() != "bearer":
            raise AuraResponseError(f"token type is not valid: {token_type!r}")
        if not isinstance(access_token, str) or not access_token:
            raise AuraResponseError("token response did not contain an access token")
        if (
            isinstance(expires_in, bool)
            or not isinstance(expires_in, int | float)
            or not 0 < expires_in <= MAX_EXPIRES_IN
        ):
            raise AuraResponseError(f"invalid expires_in value: {expires_in!r}")

        self._logger.debug("token obtained", extra={"expires_in": expires_in})
        return _Token(
            token_type="Bearer",  # noqa: S106 - the OAuth scheme name, not a secret
            access_token=access_token,
            expires_at=self._http.clock() + float(expires_in),
        )
