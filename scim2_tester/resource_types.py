from scim2_client import SCIMClient
from scim2_models import Resource
from scim2_models import ResourceType

from .utils import CheckResult
from .utils import Status
from .utils import checker


@checker
def check_resource_types_endpoint(scim: SCIMClient) -> tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`, `/ResourceTypes` is a mandatory endpoint, and should only be accessible by GET.

    .. todo::

        - Check POST/PUT/PATCH/DELETE on the endpoint
        - Check that query parameters are ignored
        - Check that query parameters are ignored
        - Check that a 403 response is returned if a filter is passed
        - Check that the `schema` attribute exists and is available.
    """
    response = scim.query(ResourceType)
    available = ", ".join([f"'{resource.name}'" for resource in response.resources])
    reason = f"Resource types available are: {available}"
    return CheckResult(status=Status.SUCCESS, reason=reason, data=response.resources)
