from __future__ import annotations

import logging

from aura_python_sdk._internal._request import RequestService


class Service:
    """Shared plumbing for the grouped services on :class:`AuraClient`."""

    def __init__(self, api: RequestService, logger: logging.Logger) -> None:
        self._api = api
        self._logger = logger
