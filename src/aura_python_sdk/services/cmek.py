"""``client.cmek`` (Go: CMEKService)."""

from __future__ import annotations

import builtins

from aura_python_sdk import _validation as validate
from aura_python_sdk._internal._serde import parse_data_list
from aura_python_sdk.models.cmek import CustomerManagedKeySummary
from aura_python_sdk.services._base import Service

# The spec names this query parameter tenantId. The Go SDK sends tenant_id.
TENANT_FILTER_PARAM = "tenantId"


class CMEKService(Service):
    """Customer-managed encryption keys."""

    def list(self, tenant_id: str | None = None) -> builtins.list[CustomerManagedKeySummary]:
        """Every key the credentials can access, optionally only those in one tenant."""
        if tenant_id is not None:
            tenant_id = validate.tenant_id(tenant_id)
        self._logger.debug("listing customer managed keys", extra={"tenant_id": tenant_id})
        response = self._api.get("customer-managed-keys", params={TENANT_FILTER_PARAM: tenant_id})
        keys = parse_data_list(CustomerManagedKeySummary, response.json())
        self._logger.debug("customer managed keys listed", extra={"count": len(keys)})
        return keys
