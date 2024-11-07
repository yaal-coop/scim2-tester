from scim2_client import SCIMClient
from scim2_models import Resource
from scim2_models import ServiceProviderConfig

from .utils import CheckResult
from .utils import Status
from .utils import checker


@checker
def check_service_provider_config_endpoint(
    scim: SCIMClient,
) -> tuple[Resource, CheckResult]:
    """As described in RFC7644 §4 <rfc7644#section-4>`, `/ServiceProviderConfig` is a mandatory endpoint, and should only be accessible by GET.

    .. todo::

        Check thet POST/PUT/PATCH/DELETE methods on the endpoint
    """
    response = scim.query(ServiceProviderConfig)
    return CheckResult(status=Status.SUCCESS, data=response)
