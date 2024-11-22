import re

from httpx import Client
from scim2_client import SCIMClient
from scim2_models import Context
from scim2_models import Error
from scim2_models import Group
from scim2_models import User

from scim2_tester.checker import check_schemas_endpoint
from scim2_tester.checker import check_server
from scim2_tester.resource import check_object_query
from scim2_tester.utils import Status


def test_unreachable_host():
    """Test reaching a invalid URL."""
    client = Client(base_url="https://invalid.test")
    scim = SCIMClient(client, resource_types=(User, Group))
    results = check_server(scim)

    assert all(result.status == Status.ERROR for result in results)
    assert all(
        result.reason == "Network error happened during request" for result in results
    )


def test_bad_authentication(httpserver):
    """Test reaching a valid URL with incorrect authentication."""
    httpserver.expect_request(re.compile(r".*")).respond_with_json(
        Error(status=401, detail="Authentication is needed").model_dump(),
        status=401,
        content_type="application/scim+json",
    )

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim = SCIMClient(client, resource_types=(User, Group))
    result = check_schemas_endpoint(scim)

    assert result.status == Status.ERROR
    assert (
        result.reason
        == "The server returned a SCIM Error object: Authentication is needed"
    )


def test_bad_content_type(httpserver):
    """Test reaching a valid URL returning an invalid content type."""
    scim_user = User(id="scim", username="scim")
    json_user = User(id="json", username="json")
    invalid_user = User(id="invalid", username="invalid")
    missing_user = User(id="missing", username="missing")

    httpserver.expect_request(re.compile(r"/Users/scim")).respond_with_json(
        scim_user.model_dump(scim_ctx=Context.RESOURCE_QUERY_RESPONSE),
        content_type="application/scim+json",
    )
    httpserver.expect_request(re.compile(r"/Users/json")).respond_with_json(
        json_user.model_dump(scim_ctx=Context.RESOURCE_QUERY_RESPONSE),
        content_type="application/json",
    )
    httpserver.expect_request(re.compile(r"/Users/invalid")).respond_with_json(
        invalid_user.model_dump(scim_ctx=Context.RESOURCE_QUERY_RESPONSE),
        content_type="application/invalid",
    )
    httpserver.expect_request(re.compile(r"/Users/missing")).respond_with_json(
        invalid_user.model_dump(scim_ctx=Context.RESOURCE_QUERY_RESPONSE),
        content_type="",
    )

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim = SCIMClient(client, resource_types=(User, Group))

    result = check_object_query(scim, scim_user)
    assert result.status == Status.SUCCESS

    result = check_object_query(scim, json_user)
    assert result.status == Status.SUCCESS

    result = check_object_query(scim, invalid_user)
    assert result.status == Status.ERROR
    assert result.reason == "Unexpected content type: application/invalid"

    result = check_object_query(scim, missing_user)
    assert result.status == Status.ERROR
    assert result.reason == "Unexpected content type: "
