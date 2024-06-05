import random
import uuid
from enum import Enum
from typing import List
from typing import Tuple

from httpx import HTTPError
from pydantic import AnyUrl
from pydantic import EmailStr
from scim2_client import SCIMClient
from scim2_client import SCIMResponseError
from scim2_models import ComplexAttribute
from scim2_models import Error
from scim2_models import Group
from scim2_models import Meta
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import ServiceProviderConfig
from scim2_models import User

from scim2_tester.utils import CheckResult
from scim2_tester.utils import Status
from scim2_tester.utils import decorate_result


def model_from_resource_type(resource_type: ResourceType):
    """TODO:

    - Actually guess the resource type from the schema.

    """
    if resource_type.id == "User":
        return User

    if resource_type.id == "Group":
        return Group


def fill_with_random_values(obj) -> Resource:
    for field_name, field in obj.model_fields.items():
        if field.default:
            continue

        field_type = obj.get_field_root_type(field_name)
        if field_type is Meta:
            value = None

        elif field_type is int:
            value = uuid.uuid4().int

        elif field_type is bool:
            value = random.choice([True, False])

        elif field_type is AnyUrl:
            value = AnyUrl(f"https://{str(uuid.uuid4())}.test")

        elif field_type is EmailStr:
            # pydantic won't allow to use the 'test' TLD here
            value = f"{uuid.uuid4()}@{uuid.uuid4()}.com"

        elif issubclass(field_type, Enum):
            value = random.choice(list(field_type))

        elif issubclass(field_type, ComplexAttribute):
            value = field_type()
            fill_with_random_values(value)

        else:
            value = str(uuid.uuid4())

        # TODO: fix this this is UGLY🤮
        if "list" in str(field.annotation).lower():
            setattr(obj, field_name, [value])

        else:
            setattr(obj, field_name, value)
    return obj


@decorate_result
def check_object_creation(
    scim: SCIMClient, obj: Resource
) -> Tuple[Resource, CheckResult]:
    """Perform an object creation.

    TODO:
      - check if the fields of the result object are the same than the
      fields of the request object
    """

    try:
        response = scim.create(obj)
    except HTTPError as exc:
        return CheckResult(
            status=Status.ERROR,
            reason=str(exc),
        ), None

    except SCIMResponseError as exc:
        return CheckResult(
            status=Status.ERROR,
            reason=f"Object creation did not return an {obj.__class__.__name__} object: {exc}",
            data=exc.response.content,
        ), None

    if isinstance(response, Error):
        return CheckResult(
            status=Status.ERROR,
            reason=f"Object creation returned an Error object: {response.detail}",
            data=response,
        ), None

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Successfull creation of a {obj.__class__.__name__} object with id {response.id}",
    ), response


def check_resource_type(
    scim: SCIMClient,
    resource_type: ResourceType,
    service_provider_config: ServiceProviderConfig,
) -> List[CheckResult]:
    """
    TODO:

    - Check creation
    - Check query
    - Check query all
    - Check replace
    - Check delete
    """
    results = []

    model = model_from_resource_type(resource_type)
    obj = model()
    fill_with_random_values(obj)

    result, created_obj = check_object_creation(scim, obj)
    results.append(result)

    return results
