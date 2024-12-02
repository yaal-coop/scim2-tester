import argparse
import uuid

from scim2_client import SCIMClient
from scim2_models import Error

from scim2_tester.resource import check_resource_type
from scim2_tester.resource_types import check_resource_types_endpoint
from scim2_tester.schemas import check_schemas_endpoint
from scim2_tester.service_provider_config import check_service_provider_config_endpoint
from scim2_tester.utils import CheckConfig
from scim2_tester.utils import CheckResult
from scim2_tester.utils import Status
from scim2_tester.utils import checker


@checker
def check_random_url(conf: CheckConfig) -> CheckResult:
    """Check that a request to a random URL returns a 404 Error object."""
    probably_invalid_url = f"/{str(uuid.uuid4())}"
    response = conf.client.query(url=probably_invalid_url, raise_scim_errors=False)

    if not isinstance(response, Error):
        return CheckResult(
            conf,
            status=Status.ERROR,
            reason=f"{probably_invalid_url} did not return an Error object",
            data=response,
        )

    if response.status != 404:
        return CheckResult(
            conf,
            status=Status.ERROR,
            reason=f"{probably_invalid_url} did return an object, but the status code is {response.status}",
            data=response,
        )

    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"{probably_invalid_url} correctly returned a 404 error",
        data=response,
    )


def check_server(client: SCIMClient, raise_exceptions=False) -> list[CheckResult]:
    """Perform a series of check to a SCIM server.

    It starts by retrieving the standard :class:`~scim2_models.ServiceProviderConfig`,
    :class:`~scim2_models.Schema` and :class:`~scim2_models.ResourceType` endpoints.
    Those configuration resources will be registered to the client if no other have been registered yet.

    Then for all available resources (whether they have been manually configured in the client,
    or dynamically discovered by the checker), it perform a series of creation, query, replacement and deletion.

    :param client: A SCIM client that will perform the requests.
    :param raise_exceptions: Whether exceptions should be raised or stored in a :class:`~scim2_tester.CheckResult` object.
    """
    conf = CheckConfig(client, raise_exceptions)
    results = []

    # Get the initial basic objects
    result_spc = check_service_provider_config_endpoint(conf)
    results.append(result_spc)
    if not conf.client.service_provider_config:
        conf.client.service_provider_config = result_spc.data

    results_resource_types = check_resource_types_endpoint(conf)
    results.extend(results_resource_types)
    if not conf.client.resource_types:
        conf.client.resource_types = results_resource_types[0].data

    results_schemas = check_schemas_endpoint(conf)
    results.extend(results_schemas)
    if not conf.client.resource_models:
        conf.client.resource_models = conf.client.build_resource_models(
            conf.client.resource_types or [], results_schemas[0].data or []
        )

    if (
        not conf.client.service_provider_config
        or not conf.client.resource_types
        or not conf.client.resource_models
    ):
        return results

    # Miscelleaneous checks
    result_random = check_random_url(conf)
    results.append(result_random)

    # Resource checks
    for resource_type in conf.client.resource_types or []:
        results.extend(check_resource_type(conf, resource_type))

    return results


if __name__ == "__main__":
    from httpx import Client
    from scim2_client.engines.httpx import SyncSCIMClient

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("host")
    parser.add_argument("--token", required=False)
    parser.add_argument("--verbose", required=False, action="store_true")
    args = parser.parse_args()

    client = Client(
        base_url=args.host,
        headers={"Authorization": f"Bearer {args.token}"} if args.token else None,
    )
    scim = SyncSCIMClient(client)
    scim.discover()
    results = check_server(scim)
    for result in results:
        print(result.status.name, result.title)
        if result.reason:
            print("  ", result.reason)
            if args.verbose and result.data:
                print("  ", result.data)
