from typing import Tuple

from scim2_client import SCIMClient
from scim2_client import SCIMClientError
from scim2_models import Resource
from scim2_models import Schema

from .utils import CheckResult
from .utils import Status
from .utils import decorate_result


@decorate_result
def check_schemas_endpoint(scim: SCIMClient) -> Tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`, `/ResourceTypes` is a
    mandatory endpoint, and should only be accessible by GET.

    .. todo::

        - Check the POST/PUT/PATCH/DELETE methods on the endpoint
        - Check accessing every subschema with /Schemas/urn:ietf:params:scim:schemas:core:2.0:User
        - Check that query parameters are ignored
        - Check that a 403 response is returned if a filter is passed
        - Check that the 'ResourceType', 'ServiceProviderConfig' and 'Schema' schemas are provided.
    """

    try:
        response = scim.query(Schema)

    except SCIMClientError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc), data=exc.source)

    available = ", ".join([f"'{resource.name}'" for resource in response.resources])
    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Schemas available are: {available}",
        data=response.resources,
    )
