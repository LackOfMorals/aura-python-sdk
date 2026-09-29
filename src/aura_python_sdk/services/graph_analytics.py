"""``client.graph_analytics`` (Go: GDSSessionService)."""

from __future__ import annotations

import builtins
from collections.abc import Sequence

from aura_python_sdk import _validation as validate
from aura_python_sdk._errors import AuraValidationError
from aura_python_sdk._internal._request import build_path
from aura_python_sdk._internal._serde import parse_data, parse_data_list, to_json
from aura_python_sdk.models.graph_analytics import (
    DeletedGDSSession,
    GDSSession,
    GDSSessionConfig,
    GDSSessionSizeEstimate,
)
from aura_python_sdk.services._base import Service

_SESSIONS = "graph-analytics/sessions"


class GDSSessionService(Service):
    """Graph Analytics (GDS) sessions."""

    def list(self) -> builtins.list[GDSSession]:
        """Every session the credentials can access."""
        self._logger.debug("listing GDS sessions")
        sessions = parse_data_list(GDSSession, self._api.get(_SESSIONS).json())
        self._logger.debug("GDS sessions listed", extra={"count": len(sessions)})
        return sessions

    def estimate_size(
        self,
        *,
        node_count: int,
        relationship_count: int,
        node_property_count: int | None = None,
        node_label_count: int | None = None,
        relationship_property_count: int | None = None,
        algorithm_categories: Sequence[str] | None = None,
    ) -> GDSSessionSizeEstimate:
        """Estimate the session size needed for a graph (Go: ``Estimate``)."""
        body: dict[str, object] = {
            "node_count": validate.non_negative_int("node count", node_count),
            "relationship_count": validate.non_negative_int(
                "relationship count", relationship_count
            ),
        }
        optional_counts = {
            "node_property_count": node_property_count,
            "node_label_count": node_label_count,
            "relationship_property_count": relationship_property_count,
        }
        for key, value in optional_counts.items():
            if value is not None:
                body[key] = validate.non_negative_int(key.replace("_", " "), value)
        if algorithm_categories is not None:
            if isinstance(algorithm_categories, str):
                raise AuraValidationError("algorithm categories must be a sequence of strings")
            body["algorithm_categories"] = [
                validate.require_non_empty("algorithm category", category)
                for category in algorithm_categories
            ]

        self._logger.debug("estimating GDS session size")
        response = self._api.post(f"{_SESSIONS}/sizing", json_body=body)
        return parse_data(GDSSessionSizeEstimate, response.json())

    def create(self, config: GDSSessionConfig) -> GDSSession:
        """Create a session, or return the matching existing one.

        Attach it to an instance with ``instance_id`` and ``database_uuid``, or make a standalone
        session with ``cloud_provider`` and ``region``.
        """
        if not isinstance(config, GDSSessionConfig):
            raise AuraValidationError("config must be a GDSSessionConfig")
        validate.require_non_empty("session name", config.name)
        validate.require_non_empty("memory", config.memory)
        if config.tenant_id is not None:
            validate.tenant_id(config.tenant_id)
        if config.instance_id is not None:
            validate.instance_id(config.instance_id)

        self._logger.debug("creating GDS session", extra={"session_name": config.name})
        session = parse_data(
            GDSSession, self._api.post(_SESSIONS, json_body=to_json(config)).json()
        )
        self._logger.info("GDS session created", extra={"session_id": session.id})
        return session

    def get(self, session_id: str) -> GDSSession:
        """Details of one session."""
        session_id = validate.session_id(session_id)
        self._logger.debug("getting GDS session", extra={"session_id": session_id})
        return parse_data(
            GDSSession, self._api.get(build_path("graph-analytics", "sessions", session_id)).json()
        )

    def delete(self, session_id: str) -> DeletedGDSSession:
        """Delete a session."""
        session_id = validate.session_id(session_id)
        self._logger.debug("deleting GDS session", extra={"session_id": session_id})
        response = self._api.delete(build_path("graph-analytics", "sessions", session_id))
        deleted = parse_data(DeletedGDSSession, response.json())
        self._logger.info("GDS session deleted", extra={"session_id": session_id})
        return deleted
