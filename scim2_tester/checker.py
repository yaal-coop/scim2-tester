import argparse
import uuid

from scim2_client import SCIMClient
from scim2_models import Error
from scim2_models import Group
from scim2_models import Resource
from scim2_models import User

from scim2_tester.resource import check_resource_type
from scim2_tester.resource_types import check_resource_types_endpoint
from scim2_tester.schemas import check_schemas_endpoint
from scim2_tester.service_provider_config import check_service_provider_config_endpoint
from scim2_tester.utils import CheckResult
from scim2_tester.utils import Status
from scim2_tester.utils import checker


@checker
def check_random_url(scim: SCIMClient) -> tuple[Resource, CheckResult]:
    """Check that a request to a random URL returns a 404 Error object."""
    probably_invalid_url = f"/{str(uuid.uuid4())}"
    response = scim.query(url=probably_invalid_url, raise_scim_errors=False)

    if not isinstance(response, Error):
        return CheckResult(
            status=Status.ERROR,
            reason=f"{probably_invalid_url} did not return an Error object",
            data=response,
        )

    if response.status != 404:
        return CheckResult(
            status=Status.ERROR,
            reason=f"{probably_invalid_url} did return an object, but the status code is {response.status}",
            data=response,
        )

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"{probably_invalid_url} correctly returned a 404 error",
        data=response,
    )


def check_server(scim: SCIMClient) -> list[CheckResult]:
    """Perform a series of check to a SCIM server.

    It starts by retrieving the standard :class:`~scim2_models.ServiceProviderConfig`,
    :class:`~scim2_models.Schema` and :class:`~scim2_models.ResourceType` endpoints.

    Then for all discovered resources, it perform a series of creation, query, replacement and deletion.
    """
    results = []

    # Get the initial basic objects
    result_spc = check_service_provider_config_endpoint(scim)
    service_provider_config = result_spc.data
    results.append(result_spc)

    result_schemas = check_schemas_endpoint(scim)
    results.append(result_schemas)

    result_resource_types = check_resource_types_endpoint(scim)
    resource_types = result_resource_types.data
    results.append(result_resource_types)

    # Miscelleaneous checks
    result_random = check_random_url(scim)
    results.append(result_random)

    # Resource checks
    if result_resource_types.status == Status.SUCCESS:
        for resource_type in resource_types:
            results.extend(
                check_resource_type(scim, resource_type, service_provider_config)
            )

    return results


if __name__ == "__main__":
    from httpx import Client

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("host")
    parser.add_argument("--token", required=False)
    parser.add_argument("--verbose", required=False, action="store_true")
    args = parser.parse_args()

    client = Client(
        base_url=args.host,
        headers={"Authorization": f"Bearer {args.token}"} if args.token else None,
    )
    scim = SCIMClient(client, resource_types=(User, Group))
    results = check_server(scim)
    for result in results:
        print(result.status.name, result.title)
        if result.reason:
            print("  ", result.reason)
            if args.verbose and result.data:
                print("  ", result.data)
