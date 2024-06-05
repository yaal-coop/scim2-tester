from typing import Tuple

from httpx import HTTPError
from pydantic import ValidationError
from scim2_client import SCIMClient
from scim2_models import Error
from scim2_models import Resource
from scim2_models import ServiceProviderConfig
from utils import CheckResult
from utils import Status
from utils import decorate_result


@decorate_result
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
    except HTTPError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc)), None

    except ValidationError as exc:
        return (
            CheckResult(
                status=Status.ERROR,
                reason=f"Could not validate the response payload: {exc}",
                data=exc.response_payload,
            ),
            None,
        )

    if isinstance(response, Error):
        return CheckResult(status=Status.ERROR, reason=response.detail), response

    return CheckResult(status=Status.SUCCESS), response
