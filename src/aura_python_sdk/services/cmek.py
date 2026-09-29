"""``client.cmek`` (Go: CMEKService)."""

from __future__ import annotations

import builtins

from aura_python_sdk import _validation as validate
from aura_python_sdk._internal._request import build_path
from aura_python_sdk._internal._serde import parse_data, parse_data_list, to_json
from aura_python_sdk.models._common import CloudProvider, InstanceType
from aura_python_sdk.models.cmek import CustomerManagedKey, CustomerManagedKeySummary
from aura_python_sdk.services._base import TENANT_ID_PARAM, Service

_KEYS = "customer-managed-keys"


class CMEKService(Service):
    """Customer-managed encryption keys."""

    def list(self, tenant_id: str | None = None) -> builtins.list[CustomerManagedKeySummary]:
        """Every key the credentials can access, optionally only those in one tenant."""
        if tenant_id is not None:
            tenant_id = validate.tenant_id(tenant_id)
        self._logger.debug("listing customer managed keys", extra={"tenant_id": tenant_id})
        response = self._api.get(_KEYS, params={TENANT_ID_PARAM: tenant_id})
        keys = parse_data_list(CustomerManagedKeySummary, response.json())
        self._logger.debug("customer managed keys listed", extra={"count": len(keys)})
        return keys

    def get(self, key_id: str) -> CustomerManagedKey:
        """Full details of one key. ``key_id`` is the Aura key ID, not the cloud provider's."""
        key_id = validate.require_non_empty("customer managed key ID", key_id)
        self._logger.debug("getting customer managed key", extra={"key_id": key_id})
        return parse_data(CustomerManagedKey, self._api.get(build_path(_KEYS, key_id)).json())

    def create(
        self,
        *,
        name: str,
        key_id: str,
        tenant_id: str,
        cloud_provider: CloudProvider | str,
        region: str,
        instance_type: InstanceType | str,
    ) -> CustomerManagedKey:
        """Register a key from your cloud provider with Aura.

        ``key_id`` is the key's ID in the cloud provider (the key ARN on AWS). The key can then
        encrypt new ``instance_type`` instances in ``region``. It starts in ``pending`` status.
        """
        body = {
            "name": validate.display_name("key name", name),
            "key_id": validate.require_non_empty("cloud provider key ID", key_id),
            "tenant_id": validate.tenant_id(tenant_id),
            "cloud_provider": validate.require_non_empty("cloud provider", cloud_provider),
            "region": validate.require_non_empty("region", region),
            "instance_type": validate.require_non_empty("instance type", instance_type),
        }
        self._logger.debug(
            "creating customer managed key", extra={"key_name": name, "tenant_id": tenant_id}
        )
        key = parse_data(CustomerManagedKey, self._api.post(_KEYS, json_body=to_json(body)).json())
        self._logger.info("customer managed key created", extra={"key_id": key.id})
        return key

    def delete(self, key_id: str) -> None:
        """Delete a key. The API refuses if any instance still uses it."""
        key_id = validate.require_non_empty("customer managed key ID", key_id)
        self._logger.debug("deleting customer managed key", extra={"key_id": key_id})
        self._api.delete(build_path(_KEYS, key_id))
        self._logger.info("customer managed key deleted", extra={"key_id": key_id})
