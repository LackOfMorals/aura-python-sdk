from dataclasses import replace
from typing import Any

import pytest

from aura_python_sdk import (
    AuraValidationError,
    CDCEnrichmentMode,
    CloudProvider,
    ConflictError,
    CreatedInstance,
    Instance,
    InstanceConfig,
    InstanceStatus,
    InstanceSummary,
    InstanceType,
    NotFoundError,
)
from tests.unit.conftest import (
    BASE,
    INSTANCE,
    INSTANCE_ID,
    OTHER_INSTANCE_ID,
    SNAPSHOT_ID,
    TENANT_ID,
    Api,
)

CONFIG = InstanceConfig(
    name="Instance01",
    tenant_id=TENANT_ID,
    cloud_provider=CloudProvider.GCP,
    region="europe-west1",
    type=InstanceType.ENTERPRISE_DB,
    version="5",
    memory="8GB",
)

CONFIG_JSON = {
    "name": "Instance01",
    "tenant_id": TENANT_ID,
    "cloud_provider": "gcp",
    "region": "europe-west1",
    "type": "enterprise-db",
    "version": "5",
    "memory": "8GB",
}

CREATED = {
    "id": "db1d1234",
    "name": "Instance01",
    "tenant_id": TENANT_ID,
    "cloud_provider": "gcp",
    "region": "europe-west1",
    "type": "enterprise-db",
    "connection_url": "neo4j+s://db1d1234.databases.neo4j.io",
    "username": "neo4j",
    "password": "letMeIn123!",
    "created_at": "2023-01-20T13:44:42Z",
}


def test_list(api: Api) -> None:
    api.reply(
        200,
        {
            "data": [
                {"id": INSTANCE_ID, "name": "P", "tenant_id": TENANT_ID, "cloud_provider": "aws"}
            ]
        },
    )
    [summary] = api.client.instances.list()
    assert isinstance(summary, InstanceSummary)
    assert summary.cloud_provider is CloudProvider.AWS
    assert (api.request.method, api.request.url) == ("GET", f"{BASE}/instances")


def test_get(api: Api) -> None:
    api.reply(200, {"data": INSTANCE})
    instance = api.client.instances.get(INSTANCE_ID)
    assert isinstance(instance, Instance)
    assert instance.status is InstanceStatus.RUNNING
    assert api.request.url == f"{BASE}/instances/{INSTANCE_ID}"


def test_get_not_found(api: Api) -> None:
    api.reply(404, {"errors": [{"message": "Instance not found", "reason": "instance-not-found"}]})
    with pytest.raises(NotFoundError, match="Instance not found"):
        api.client.instances.get(INSTANCE_ID)


def test_create(api: Api) -> None:
    api.reply(202, {"data": CREATED})
    created = api.client.instances.create(CONFIG)

    assert isinstance(created, CreatedInstance)
    assert created.password == "letMeIn123!"
    assert (api.request.method, api.request.url) == ("POST", f"{BASE}/instances")
    assert api.body == CONFIG_JSON


def test_create_sends_optional_fields_when_set(api: Api) -> None:
    api.reply(202, {"data": CREATED})
    key_id = "8c764aed-8eb3-4a1c-92f6-e4ef0c7a6ed9"
    config = replace(
        CONFIG, vector_optimized=True, graph_analytics_plugin=False, customer_managed_key_id=key_id
    )
    api.client.instances.create(config)
    assert api.body == {
        **CONFIG_JSON,
        "vector_optimized": True,
        "graph_analytics_plugin": False,
        "customer_managed_key_id": key_id,
    }


def test_create_from_instance(api: Api) -> None:
    api.reply(202, {"data": CREATED})
    api.client.instances.create_from_instance(OTHER_INSTANCE_ID, CONFIG)
    assert api.body == {**CONFIG_JSON, "source_instance_id": OTHER_INSTANCE_ID}


def test_create_from_snapshot(api: Api) -> None:
    api.reply(202, {"data": CREATED})
    api.client.instances.create_from_snapshot(OTHER_INSTANCE_ID, SNAPSHOT_ID, CONFIG)
    assert api.body == {
        **CONFIG_JSON,
        "source_instance_id": OTHER_INSTANCE_ID,
        "source_snapshot_id": SNAPSHOT_ID,
    }


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"name": ""}, "instance name must not be empty"),
        ({"name": "x" * 31}, "at most 30 characters"),
        ({"tenant_id": ""}, "tenant ID must not be empty"),
        ({"tenant_id": "abc"}, "tenant ID must be a valid UUID"),
        ({"cloud_provider": ""}, "cloud provider must not be empty"),
        ({"region": ""}, "region must not be empty"),
        ({"type": ""}, "instance type must not be empty"),
        ({"version": ""}, "version must not be empty"),
        ({"memory": ""}, "memory must not be empty"),
        ({"customer_managed_key_id": ""}, "customer managed key ID must not be empty"),
    ],
)
def test_create_validation_matches_go(api: Api, overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(AuraValidationError, match=message):
        api.client.instances.create(replace(CONFIG, **overrides))
    api.assert_no_request()


def test_create_requires_instance_config(api: Api) -> None:
    with pytest.raises(AuraValidationError, match="config must be an InstanceConfig"):
        api.client.instances.create(CONFIG_JSON)  # type: ignore[arg-type]
    api.assert_no_request()


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.create_from_instance("", CONFIG),
        lambda s: s.create_from_instance("bad", CONFIG),
        lambda s: s.create_from_snapshot("bad", SNAPSHOT_ID, CONFIG),
        lambda s: s.create_from_snapshot(OTHER_INSTANCE_ID, "bad", CONFIG),
        lambda s: s.create_from_snapshot(OTHER_INSTANCE_ID, "", CONFIG),
    ],
)
def test_create_from_source_validation(api: Api, call: Any) -> None:
    with pytest.raises(AuraValidationError, match=r"source (instance|snapshot) ID"):
        call(api.client.instances)
    api.assert_no_request()


def test_update(api: Api) -> None:
    api.reply(202, {"data": {**INSTANCE, "status": "updating"}})
    instance = api.client.instances.update(
        INSTANCE_ID,
        name="Renamed",
        memory="16GB",
        cdc_enrichment_mode=CDCEnrichmentMode.FULL,
        secondaries_count=2,
    )
    assert instance.status is InstanceStatus.UPDATING
    assert (api.request.method, api.request.url) == ("PATCH", f"{BASE}/instances/{INSTANCE_ID}")
    assert api.body == {
        "name": "Renamed",
        "memory": "16GB",
        "cdc_enrichment_mode": "FULL",
        "secondaries_count": 2,
    }


def test_update_sends_only_given_fields(api: Api) -> None:
    api.reply(200, {"data": INSTANCE})
    api.client.instances.update(INSTANCE_ID, secondaries_count=0)
    assert api.body == {"secondaries_count": 0}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({}, "at least one field"),
        ({"name": "x" * 31}, "at most 30 characters"),
        ({"memory": ""}, "memory must not be empty"),
        ({"cdc_enrichment_mode": ""}, "CDC enrichment mode"),
        ({"secondaries_count": -1}, "secondaries count"),
    ],
)
def test_update_validation(api: Api, kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(AuraValidationError, match=message):
        api.client.instances.update(INSTANCE_ID, **kwargs)
    api.assert_no_request()


def test_delete(api: Api) -> None:
    api.reply(202, {"data": {**INSTANCE, "status": "destroying"}})
    instance = api.client.instances.delete(INSTANCE_ID)
    assert instance.status is InstanceStatus.DESTROYING
    assert (api.request.method, api.request.url) == ("DELETE", f"{BASE}/instances/{INSTANCE_ID}")
    assert api.request.body is None


@pytest.mark.parametrize(("action", "status"), [("pause", "pausing"), ("resume", "resuming")])
def test_pause_and_resume(api: Api, action: str, status: str) -> None:
    api.reply(202, {"data": {**INSTANCE, "status": status}})
    instance = getattr(api.client.instances, action)(INSTANCE_ID)
    assert instance.status == status
    assert (api.request.method, api.request.url) == (
        "POST",
        f"{BASE}/instances/{INSTANCE_ID}/{action}",
    )
    assert api.request.body is None


def test_pause_conflict(api: Api) -> None:
    api.reply(409, {"errors": [{"message": "Instance is not running", "reason": "conflict"}]})
    with pytest.raises(ConflictError):
        api.client.instances.pause(INSTANCE_ID)


def test_overwrite_from_instance(api: Api) -> None:
    api.reply(202, {"data": {**INSTANCE, "status": "overwriting"}})
    instance = api.client.instances.overwrite_from_instance(INSTANCE_ID, OTHER_INSTANCE_ID)
    assert instance.status is InstanceStatus.OVERWRITING
    assert api.request.url == f"{BASE}/instances/{INSTANCE_ID}/overwrite"
    assert api.body == {"source_instance_id": OTHER_INSTANCE_ID}


def test_overwrite_from_snapshot(api: Api) -> None:
    api.reply(202, {"data": {**INSTANCE, "status": "overwriting"}})
    api.client.instances.overwrite_from_snapshot(INSTANCE_ID, SNAPSHOT_ID)
    assert api.body == {"source_snapshot_id": SNAPSHOT_ID}


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.get("nope"),
        lambda s: s.delete(""),
        lambda s: s.pause("../../x"),
        lambda s: s.resume("12345"),
        lambda s: s.update("bad", name="x"),
        lambda s: s.overwrite_from_instance("bad", OTHER_INSTANCE_ID),
        lambda s: s.overwrite_from_instance(INSTANCE_ID, "bad"),
        lambda s: s.overwrite_from_snapshot(INSTANCE_ID, "bad"),
    ],
)
def test_invalid_ids_send_nothing(api: Api, call: Any) -> None:
    with pytest.raises(AuraValidationError):
        call(api.client.instances)
    api.assert_no_request()
