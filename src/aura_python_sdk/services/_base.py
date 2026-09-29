from __future__ import annotations

import logging
from typing import TypeVar

from aura_python_sdk._internal._call import Call
from aura_python_sdk._internal._request import AsyncRequestService, RequestService

T = TypeVar("T")

# List-filter query parameter names, as the v1 spec defines them. (The Go SDK sends tenant_id.)
TENANT_ID_PARAM = "tenantId"
INSTANCE_ID_PARAM = "instanceId"
ORGANIZATION_ID_PARAM = "organizationId"


class Service:
    """Base for the sync services on :class:`AuraClient`: runs each operation's ``Call``."""

    def __init__(self, api: RequestService, logger: logging.Logger) -> None:
        self._api = api
        self._logger = logger

    def _run(self, call: Call[T]) -> T:
        self._logger.debug(call.describe, extra=dict(call.context))
        response = self._api.request(
            call.method, call.path, params=call.params, json_body=call.json_body
        )
        result = call.parse(response)
        if call.done:
            self._logger.info(call.done, extra=dict(call.context))
        return result


class AsyncService:
    """Base for the async services on :class:`AsyncAuraClient`: awaits each operation's ``Call``."""

    def __init__(self, api: AsyncRequestService, logger: logging.Logger) -> None:
        self._api = api
        self._logger = logger

    async def _run(self, call: Call[T]) -> T:
        self._logger.debug(call.describe, extra=dict(call.context))
        response = await self._api.request(
            call.method, call.path, params=call.params, json_body=call.json_body
        )
        result = call.parse(response)
        if call.done:
            self._logger.info(call.done, extra=dict(call.context))
        return result
