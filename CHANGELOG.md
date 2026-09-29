# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The release workflow publishes
the `## vX.Y.Z` section that matches the pushed tag as the GitHub release notes.

## Unreleased

### Added

- `AuraClient` for the Aura API v1, with the Go SDK's options as keyword arguments, `from_env()`,
  and context-manager support.
- Services matching the Go SDK: `tenants`, `instances`, `snapshots`, `cmek`, `graph_analytics` and
  `prometheus`.
- Full v1 spec coverage beyond the Go SDK: `instances.estimate_size`, `instances.upgrade`,
  `cmek.get` / `create` / `delete`, list filters, and the `storage`, `vector_optimized` and
  `graph_analytics_plugin` update fields.
- Frozen dataclass models and `StrEnum`s that tolerate values the SDK doesn't know yet.
- An exception class per error: `NotFoundError`, `RateLimitError` (with `retry_after`) and others.
- A pluggable `HttpTransport`, with an httpx implementation as the default.
- Only network failures are retried, and a non-idempotent request is never re-sent once it may
  have reached the server.
- A stdlib Prometheus text-format parser whose output matches the Go SDK, and
  `get_instance_health` with the Go SDK's thresholds.
