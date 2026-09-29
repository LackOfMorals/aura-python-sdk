"""``client.snapshots`` (Go: SnapshotService)."""

from __future__ import annotations

import builtins
import datetime as dt

from aura_python_sdk import _validation as validate
from aura_python_sdk._errors import AuraValidationError
from aura_python_sdk._internal._request import build_path
from aura_python_sdk._internal._serde import parse_data, parse_data_list
from aura_python_sdk.models.instances import Instance
from aura_python_sdk.models.snapshots import CreatedSnapshot, Snapshot
from aura_python_sdk.services._base import Service


class SnapshotService(Service):
    """Instance snapshots."""

    def list(self, instance_id: str, date: dt.date | None = None) -> builtins.list[Snapshot]:
        """Snapshots of an instance taken on ``date``. The API defaults to today."""
        instance_id = validate.instance_id(instance_id)
        if date is not None and (not isinstance(date, dt.date) or isinstance(date, dt.datetime)):
            raise AuraValidationError("date must be a datetime.date")
        self._logger.debug("listing snapshots", extra={"instance_id": instance_id})
        response = self._api.get(
            build_path("instances", instance_id, "snapshots"),
            params={"date": date.isoformat() if date else None},
        )
        snapshots = parse_data_list(Snapshot, response.json())
        self._logger.debug("snapshots listed", extra={"count": len(snapshots)})
        return snapshots

    def get(self, instance_id: str, snapshot_id: str) -> Snapshot:
        """Details of one snapshot."""
        instance_id = validate.instance_id(instance_id)
        snapshot_id = validate.snapshot_id(snapshot_id)
        self._logger.debug(
            "getting snapshot", extra={"instance_id": instance_id, "snapshot_id": snapshot_id}
        )
        response = self._api.get(build_path("instances", instance_id, "snapshots", snapshot_id))
        return parse_data(Snapshot, response.json())

    def create(self, instance_id: str) -> CreatedSnapshot:
        """Start an on-demand snapshot."""
        instance_id = validate.instance_id(instance_id)
        self._logger.debug("creating snapshot", extra={"instance_id": instance_id})
        response = self._api.post(build_path("instances", instance_id, "snapshots"))
        created = parse_data(CreatedSnapshot, response.json())
        self._logger.info(
            "snapshot started",
            extra={"instance_id": instance_id, "snapshot_id": created.snapshot_id},
        )
        return created

    def restore(self, instance_id: str, snapshot_id: str) -> Instance:
        """Restore an instance from one of its own snapshots, replacing its current data."""
        instance_id = validate.instance_id(instance_id)
        snapshot_id = validate.snapshot_id(snapshot_id)
        self._logger.debug(
            "restoring snapshot", extra={"instance_id": instance_id, "snapshot_id": snapshot_id}
        )
        response = self._api.post(
            build_path("instances", instance_id, "snapshots", snapshot_id, "restore")
        )
        instance = parse_data(Instance, response.json())
        self._logger.info(
            "snapshot restore started",
            extra={"instance_id": instance_id, "snapshot_id": snapshot_id},
        )
        return instance
