"""``client.tenants`` (Go: TenantService)."""

from __future__ import annotations

import builtins

from aura_python_sdk import _validation as validate
from aura_python_sdk._internal._request import build_path
from aura_python_sdk._internal._serde import parse_data, parse_data_list
from aura_python_sdk.models.tenants import MetricsIntegration, Tenant, TenantSummary
from aura_python_sdk.services._base import Service


class TenantService(Service):
    """Tenants (shown as projects in the Aura Console)."""

    def list(self) -> builtins.list[TenantSummary]:
        """Every tenant the credentials can access."""
        self._logger.debug("listing tenants")
        tenants = parse_data_list(TenantSummary, self._api.get("tenants").json())
        self._logger.debug("tenants listed", extra={"count": len(tenants)})
        return tenants

    def get(self, tenant_id: str) -> Tenant:
        """A tenant and the instance configurations it can create."""
        tenant_id = validate.tenant_id(tenant_id)
        self._logger.debug("getting tenant", extra={"tenant_id": tenant_id})
        return parse_data(Tenant, self._api.get(build_path("tenants", tenant_id)).json())

    def get_metrics_integration(self, tenant_id: str) -> MetricsIntegration:
        """The project-level Prometheus metrics endpoint (Go: ``GetMetrics``)."""
        tenant_id = validate.tenant_id(tenant_id)
        self._logger.debug("getting tenant metrics integration", extra={"tenant_id": tenant_id})
        response = self._api.get(build_path("tenants", tenant_id, "metrics-integration"))
        return parse_data(MetricsIntegration, response.json())
