import argparse
from dataclasses import dataclass
from enum import Enum
from enum import auto
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

from pydantic import ValidationError
from scim2_client import SCIMClient
from scim2_models import EnterpriseUser
from scim2_models import Error
from scim2_models import Group
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ServiceProviderConfig
from scim2_models import User


class Status(Enum):
    SUCCESS = auto()
    ERROR = auto()


@dataclass
class CheckResult:
    """Store a check result."""

    status: Status
    title: str
    """The title of the check."""

    description: str
    """What the check does, and why the spec advises it to do."""

    reason: Optional[str] = None
    """Why it failed, or how it succeed."""

    data: Optional[Any] = None
    """Any related data that can help to debug."""


def check_service_provider_config_endpoint(
    scim: SCIMClient,
) -> Tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`,
    `/ServiceProviderConfig` is a mandatory endpoint, and should only be
    accessible by GET.

    .. todo::

        Check thet POST/PUT/PATCH/DELETE methods on the endpoint
    """

    try:
        response = scim.query(ServiceProviderConfig)
    except ValidationError as exc:
        return (
            None,
            CheckResult(
                status=Status.ERROR,
                title=check_service_provider_config_endpoint.__name__,
                description=check_service_provider_config_endpoint.__doc__,
                reason=f"Could not validate the response payload: {exc}",
                data=exc.response_payload,
            ),
        )

    if isinstance(response, Error):
        return (
            response,
            CheckResult(
                status=Status.ERROR,
                title=check_service_provider_config_endpoint.__name__,
                description=check_service_provider_config_endpoint.__doc__,
                reason=check_service_provider_config_endpoint.detail,
            ),
        )

    return response, CheckResult(
        status=Status.SUCCESS,
        title=check_service_provider_config_endpoint.__name__,
        description=check_service_provider_config_endpoint.__doc__,
    )


def check_schemas_endpoint(scim: SCIMClient) -> Tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`, `/ResourceTypes` is a
    mandatory endpoint, and should only be accessible by GET.

    .. todo::

        - Check the POST/PUT/PATCH/DELETE methods on the endpoint
        - Check accessing every subschema with /Schemas/urn:ietf:params:scim:schemas:core:2.0:User
        - Check that query parameters are ignored
        - Check that a 403 response is returned if a filter is passed
    """

    response = scim.query(Schema)
    if isinstance(response, Error):
        return (
            response,
            CheckResult(
                status=Status.ERROR,
                title=check_schemas_endpoint.__name__,
                description=check_schemas_endpoint.__doc__,
                reason=check_schemas_endpoint.detail,
            ),
        )

    available = ", ".join([f"'{resource.name}'" for resource in response.resources])
    return response, CheckResult(
        status=Status.SUCCESS,
        title=check_schemas_endpoint.__name__,
        description=check_schemas_endpoint.__doc__,
        reason=f"Schemas available are: {available}",
    )


def check_resource_types_endpoint(scim: SCIMClient) -> Tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`, `/ResourceTypes` is a
    mandatory endpoint, and should only be accessible by GET.

    .. todo::

        - Check POST/PUT/PATCH/DELETE on the endpoint
        - Check that query parameters are ignored
        - Check that query parameters are ignored
        - Check that a 403 response is returned if a filter is passed
        - Check that the `schema` attribute exists and is available.
    """

    response = scim.query(ResourceType)
    if isinstance(response, Error):
        return (
            response,
            CheckResult(
                status=Status.ERROR,
                title=check_resource_types_endpoint.__name__,
                description=check_resource_types_endpoint.__doc__,
                reason=check_resource_types_endpoint.detail,
            ),
        )

    available = ", ".join([f"'{resource.name}'" for resource in response.resources])

    return response, CheckResult(
        status=Status.SUCCESS,
        title=check_resource_types_endpoint.__name__,
        description=check_resource_types_endpoint.__doc__,
        reason=f"Resource types available are: {available}",
    )


def check_server(scim: SCIMClient) -> List[CheckResult]:
    """
    .. todo::

        Check that a random page returns a 404 in the expected error format.
    """

    results = []
    service_provider_config, result = check_service_provider_config_endpoint(scim)
    results.append(result)
    service_provider_config, result = check_schemas_endpoint(scim)
    results.append(result)
    service_provider_config, result = check_resource_types_endpoint(scim)
    results.append(result)
    return results


if __name__ == "__main__":
    from httpx import Client

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("host")
    parser.add_argument("--token", required=False)
    args = parser.parse_args()

    client = Client(
        base_url=args.host,
        headers={"Authorization": args.token} if args.token else None,
    )
    scim = SCIMClient(
        client,
        resource_types=(
            User[EnterpriseUser],
            Group,
            ResourceType,
            Schema,
            ServiceProviderConfig,
        ),
    )
    results = check_server(scim)
    for result in results:
        print(result.status.name, result.title)
        if result.reason:
            print("  ", result.reason)
