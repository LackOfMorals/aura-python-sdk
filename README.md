# aura-python-sdk

Python client library for the [Neo4j Aura API](https://neo4j.com/docs/aura/api/overview/) (v1),
modelled on [aura-go-sdk](https://github.com/neo4j-contrib/aura-go-sdk).

> Status: under development. See [PLAN.md](PLAN.md).

Requires Python 3.11+.

## Development

```sh
uv sync --all-extras
uv run ruff format && uv run ruff check
uv run mypy
uv run pytest -m "not integration"
```
