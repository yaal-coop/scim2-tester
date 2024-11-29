from scim2_models import Resource
from scim2_models import Schema

from .utils import CheckConfig
from .utils import CheckResult
from .utils import Status
from .utils import checker


@checker
def check_schemas_endpoint(conf: CheckConfig) -> tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`, `/ResourceTypes` is a mandatory endpoint, and should only be accessible by GET.

    .. todo::

        - Check the POST/PUT/PATCH/DELETE methods on the endpoint
        - Check accessing every subschema with /Schemas/urn:ietf:params:scim:schemas:core:2.0:User
        - Check that query parameters are ignored
        - Check that a 403 response is returned if a filter is passed
        - Check that the 'ResourceType', 'ServiceProviderConfig' and 'Schema' schemas are provided.
    """
    response = conf.client.query(
        Schema, expected_status_codes=conf.expected_status_codes or [200]
    )
    available = ", ".join([f"'{resource.name}'" for resource in response.resources])
    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Schemas available are: {available}",
        data=response.resources,
    )
