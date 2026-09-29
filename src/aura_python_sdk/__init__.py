"""Python client library for the Neo4j Aura API (v1).

Example::

    import aura_python_sdk as aura

    with aura.AuraClient(client_id="...", client_secret="...") as client:
        for instance in client.instances.list():
            print(instance.id, instance.name)
"""

import logging

from aura_python_sdk._client import AuraClient
from aura_python_sdk._errors import (
    AuraAPIError,
    AuraConfigurationError,
    AuraConnectionError,
    AuraError,
    AuraResponseError,
    AuraTimeoutError,
    AuraValidationError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ErrorDetail,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
)
from aura_python_sdk._transport import HttpRequest, HttpResponse, HttpTransport
from aura_python_sdk._version import __version__

# Library convention: emit nothing unless the application configures logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "AuraAPIError",
    "AuraClient",
    "AuraConfigurationError",
    "AuraConnectionError",
    "AuraError",
    "AuraResponseError",
    "AuraTimeoutError",
    "AuraValidationError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "ErrorDetail",
    "HttpRequest",
    "HttpResponse",
    "HttpTransport",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "__version__",
]
