from __future__ import annotations

import logging

from aura_python_sdk._internal._request import RequestService

# List-filter query parameter names, as the v1 spec defines them. (The Go SDK sends tenant_id.)
TENANT_ID_PARAM = "tenantId"
INSTANCE_ID_PARAM = "instanceId"
ORGANIZATION_ID_PARAM = "organizationId"


class Service:
    """Shared plumbing for the grouped services on :class:`AuraClient`."""

    def __init__(self, api: RequestService, logger: logging.Logger) -> None:
        self._api = api
        self._logger = logger
