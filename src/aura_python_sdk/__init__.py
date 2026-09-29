"""Python client library for the Neo4j Aura API (v1).

Example::

    import aura_python_sdk as aura

    with aura.AuraClient(client_id="...", client_secret="...") as client:
        for instance in client.instances.list():
            print(instance.id, instance.name)
"""

from aura_python_sdk._version import __version__

__all__ = ["__version__"]
