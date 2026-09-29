import pytest

from aura_python_sdk import AuraValidationError, CustomerManagedKeySummary
from tests.unit.conftest import BASE, TENANT_ID, Api

KEY = {"id": "8c764aed-8eb3-4a1c-92f6-e4ef0c7a6ed9", "name": "Key01", "tenant_id": TENANT_ID}


def test_list(api: Api) -> None:
    api.reply(200, {"data": [KEY]})
    assert api.client.cmek.list() == [CustomerManagedKeySummary(**KEY)]
    assert api.request.url == f"{BASE}/customer-managed-keys"


def test_list_filtered_by_tenant(api: Api) -> None:
    api.reply(200, {"data": [KEY]})
    api.client.cmek.list(TENANT_ID)
    assert api.request.url == f"{BASE}/customer-managed-keys?tenantId={TENANT_ID}"


def test_list_invalid_tenant_sends_nothing(api: Api) -> None:
    with pytest.raises(AuraValidationError, match="tenant ID"):
        api.client.cmek.list("bad")
    api.assert_no_request()
