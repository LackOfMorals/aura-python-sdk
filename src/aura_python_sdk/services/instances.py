"""``client.instances`` (Go: InstanceService)."""

from __future__ import annotations

import builtins
from collections.abc import Sequence

from aura_python_sdk import _validation as validate
from aura_python_sdk._errors import AuraValidationError
from aura_python_sdk._internal._request import build_path
from aura_python_sdk._internal._serde import parse_data, parse_data_list, to_json
from aura_python_sdk.models._common import InstanceType
from aura_python_sdk.models.instances import (
    CDCEnrichmentMode,
    CreatedInstance,
    Instance,
    InstanceConfig,
    InstanceSizeEstimate,
    InstanceSummary,
)
from aura_python_sdk.services._base import TENANT_ID_PARAM, Service


class InstanceService(Service):
    """AuraDB and AuraDS instances."""

    def list(self, tenant_id: str | None = None) -> builtins.list[InstanceSummary]:
        """Every instance the credentials can access, optionally only those in one tenant."""
        if tenant_id is not None:
            tenant_id = validate.tenant_id(tenant_id)
        self._logger.debug("listing instances", extra={"tenant_id": tenant_id})
        response = self._api.get("instances", params={TENANT_ID_PARAM: tenant_id})
        instances = parse_data_list(InstanceSummary, response.json())
        self._logger.debug("instances listed", extra={"count": len(instances)})
        return instances

    def get(self, instance_id: str) -> Instance:
        """Full details of one instance."""
        instance_id = validate.instance_id(instance_id)
        self._logger.debug("getting instance", extra={"instance_id": instance_id})
        return parse_data(Instance, self._api.get(build_path("instances", instance_id)).json())

    def create(self, config: InstanceConfig) -> CreatedInstance:
        """Start creating an instance.

        Creation is asynchronous. Poll :meth:`get` until ``status`` is ``running``. The returned
        password is shown only once.
        """
        body = _create_body(config)
        return self._create(body)

    def create_from_instance(
        self, source_instance_id: str, config: InstanceConfig
    ) -> CreatedInstance:
        """Create an instance cloned from the current data of another instance."""
        source_instance_id = validate.instance_id(source_instance_id, "source instance ID")
        body = _create_body(config)
        body["source_instance_id"] = source_instance_id
        return self._create(body)

    def create_from_snapshot(
        self, source_instance_id: str, source_snapshot_id: str, config: InstanceConfig
    ) -> CreatedInstance:
        """Create an instance from a snapshot.

        The snapshot must belong to ``source_instance_id`` and be exportable.
        """
        source_instance_id = validate.instance_id(source_instance_id, "source instance ID")
        source_snapshot_id = validate.snapshot_id(source_snapshot_id, "source snapshot ID")
        body = _create_body(config)
        body["source_instance_id"] = source_instance_id
        body["source_snapshot_id"] = source_snapshot_id
        return self._create(body)

    def _create(self, body: dict[str, object]) -> CreatedInstance:
        self._logger.debug(
            "creating instance",
            extra={"instance_name": body["name"], "tenant_id": body["tenant_id"]},
        )
        created = parse_data(CreatedInstance, self._api.post("instances", json_body=body).json())
        self._logger.info(
            "instance creation started",
            extra={"instance_id": created.id, "instance_name": created.name},
        )
        return created

    def update(
        self,
        instance_id: str,
        *,
        name: str | None = None,
        memory: str | None = None,
        storage: str | None = None,
        vector_optimized: bool | None = None,
        graph_analytics_plugin: bool | None = None,
        cdc_enrichment_mode: CDCEnrichmentMode | str | None = None,
        secondaries_count: int | None = None,
    ) -> Instance:
        """Rename, resize or reconfigure an instance. Only the arguments given are changed.

        The update is asynchronous, and the instance stays available throughout.
        ``secondaries_count`` applies only to Virtual Dedicated Cloud, and
        ``cdc_enrichment_mode`` only to Virtual Dedicated Cloud and Business Critical.
        """
        instance_id = validate.instance_id(instance_id)
        changes: dict[str, object] = {}
        if name is not None:
            changes["name"] = validate.instance_name(name)
        if memory is not None:
            changes["memory"] = validate.require_non_empty("memory", memory)
        if storage is not None:
            changes["storage"] = validate.require_non_empty("storage", storage)
        if vector_optimized is not None:
            changes["vector_optimized"] = validate.boolean("vector optimized", vector_optimized)
        if graph_analytics_plugin is not None:
            changes["graph_analytics_plugin"] = validate.boolean(
                "graph analytics plugin", graph_analytics_plugin
            )
        if cdc_enrichment_mode is not None:
            changes["cdc_enrichment_mode"] = validate.require_non_empty(
                "CDC enrichment mode", cdc_enrichment_mode
            )
        if secondaries_count is not None:
            changes["secondaries_count"] = validate.non_negative_int(
                "secondaries count", secondaries_count
            )
        if not changes:
            raise AuraValidationError("update requires at least one field to change")

        self._logger.debug(
            "updating instance", extra={"instance_id": instance_id, "fields": sorted(changes)}
        )
        response = self._api.patch(build_path("instances", instance_id), json_body=to_json(changes))
        instance = parse_data(Instance, response.json())
        self._logger.info("instance update started", extra={"instance_id": instance_id})
        return instance

    def estimate_size(
        self,
        *,
        node_count: int,
        relationship_count: int,
        instance_type: InstanceType | str | None = None,
        algorithm_categories: Sequence[str] | None = None,
    ) -> InstanceSizeEstimate:
        """Estimate the instance size needed for a graph.

        Supported for ``enterprise-ds`` and ``professional-ds``. Pass the recommended size as
        ``memory`` when creating the instance.
        """
        body: dict[str, object] = {
            "node_count": validate.non_negative_int("node count", node_count),
            "relationship_count": validate.non_negative_int(
                "relationship count", relationship_count
            ),
        }
        if instance_type is not None:
            body["instance_type"] = validate.require_non_empty("instance type", instance_type)
        if algorithm_categories is not None:
            body["algorithm_categories"] = validate.string_list(
                "algorithm categories", algorithm_categories
            )
        self._logger.debug("estimating instance size")
        response = self._api.post("instances/sizing", json_body=to_json(body))
        return parse_data(InstanceSizeEstimate, response.json())

    def upgrade(
        self, instance_id: str, *, memory: str | None = None, storage: str | None = None
    ) -> Instance:
        """Upgrade an AuraDB Professional instance to Business Critical.

        Pass both ``memory`` and ``storage`` to resize as part of the upgrade, or neither to keep
        the current size. Not available for Marketplace projects or trial instances.
        """
        instance_id = validate.instance_id(instance_id)
        if (memory is None) != (storage is None):
            raise AuraValidationError("upgrade requires both memory and storage, or neither")
        body: dict[str, object] = {}
        if memory is not None and storage is not None:
            body["memory"] = validate.require_non_empty("memory", memory)
            body["storage"] = validate.require_non_empty("storage", storage)
        self._logger.debug("upgrading instance", extra={"instance_id": instance_id})
        response = self._api.post(build_path("instances", instance_id, "upgrade"), json_body=body)
        instance = parse_data(Instance, response.json())
        self._logger.info("instance upgrade started", extra={"instance_id": instance_id})
        return instance

    def delete(self, instance_id: str) -> Instance:
        """Start deleting an instance. This cannot be undone."""
        instance_id = validate.instance_id(instance_id)
        self._logger.debug("deleting instance", extra={"instance_id": instance_id})
        instance = parse_data(
            Instance, self._api.delete(build_path("instances", instance_id)).json()
        )
        self._logger.info("instance deletion started", extra={"instance_id": instance_id})
        return instance

    def pause(self, instance_id: str) -> Instance:
        """Pause a running instance."""
        return self._lifecycle(instance_id, "pause")

    def resume(self, instance_id: str) -> Instance:
        """Resume a paused instance."""
        return self._lifecycle(instance_id, "resume")

    def _lifecycle(self, instance_id: str, action: str) -> Instance:
        instance_id = validate.instance_id(instance_id)
        self._logger.debug("%s instance", action, extra={"instance_id": instance_id})
        response = self._api.post(build_path("instances", instance_id, action))
        instance = parse_data(Instance, response.json())
        self._logger.info("instance %s started", action, extra={"instance_id": instance_id})
        return instance

    def overwrite_from_instance(self, instance_id: str, source_instance_id: str) -> Instance:
        """Replace an instance's data with the current data of another instance."""
        instance_id = validate.instance_id(instance_id)
        source_instance_id = validate.instance_id(source_instance_id, "source instance ID")
        return self._overwrite(instance_id, {"source_instance_id": source_instance_id})

    def overwrite_from_snapshot(self, instance_id: str, source_snapshot_id: str) -> Instance:
        """Replace an instance's data with a snapshot."""
        instance_id = validate.instance_id(instance_id)
        source_snapshot_id = validate.snapshot_id(source_snapshot_id, "source snapshot ID")
        return self._overwrite(instance_id, {"source_snapshot_id": source_snapshot_id})

    def _overwrite(self, instance_id: str, body: dict[str, object]) -> Instance:
        self._logger.debug("overwriting instance", extra={"instance_id": instance_id, **body})
        response = self._api.post(build_path("instances", instance_id, "overwrite"), json_body=body)
        instance = parse_data(Instance, response.json())
        self._logger.info("instance overwrite started", extra={"instance_id": instance_id})
        return instance


def _create_body(config: InstanceConfig) -> dict[str, object]:
    """Validate a create request as the Go SDK's validateCreateInstanceConfig does."""
    if not isinstance(config, InstanceConfig):
        raise AuraValidationError("config must be an InstanceConfig")
    validate.instance_name(config.name)
    validate.tenant_id(config.tenant_id)
    validate.require_non_empty("cloud provider", config.cloud_provider)
    validate.require_non_empty("region", config.region)
    validate.require_non_empty("instance type", config.type)
    validate.require_non_empty("version", config.version)
    validate.require_non_empty("memory", config.memory)
    if config.customer_managed_key_id is not None:
        validate.require_non_empty("customer managed key ID", config.customer_managed_key_id)
    body = to_json(config)
    if not isinstance(body, dict):  # pragma: no cover - to_json of a dataclass is a dict
        raise TypeError("expected a JSON object")
    return body
