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
from aura_python_sdk.models import (
    CDCEnrichmentMode,
    CloudProvider,
    CreatedInstance,
    CreatedSnapshot,
    CustomerManagedKey,
    CustomerManagedKeySummary,
    DeletedGDSSession,
    GDSSession,
    GDSSessionConfig,
    GDSSessionSizeEstimate,
    GDSSessionStatus,
    Instance,
    InstanceConfig,
    InstanceConfiguration,
    InstanceSizeEstimate,
    InstanceStatus,
    InstanceSummary,
    InstanceType,
    MetricsIntegration,
    Snapshot,
    SnapshotProfile,
    SnapshotStatus,
    Tenant,
    TenantSummary,
)

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
    "CDCEnrichmentMode",
    "CloudProvider",
    "ConflictError",
    "CreatedInstance",
    "CreatedSnapshot",
    "CustomerManagedKey",
    "CustomerManagedKeySummary",
    "DeletedGDSSession",
    "ErrorDetail",
    "GDSSession",
    "GDSSessionConfig",
    "GDSSessionSizeEstimate",
    "GDSSessionStatus",
    "HttpRequest",
    "HttpResponse",
    "HttpTransport",
    "Instance",
    "InstanceConfig",
    "InstanceConfiguration",
    "InstanceSizeEstimate",
    "InstanceStatus",
    "InstanceSummary",
    "InstanceType",
    "MetricsIntegration",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "Snapshot",
    "SnapshotProfile",
    "SnapshotStatus",
    "Tenant",
    "TenantSummary",
    "__version__",
]
