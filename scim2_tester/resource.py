import random
import uuid
from enum import Enum
from typing import List
from typing import Tuple
from typing import get_origin

from pydantic import EmailStr
from scim2_client import SCIMClient
from scim2_client import SCIMClientError
from scim2_models import ComplexAttribute
from scim2_models import Group
from scim2_models import Meta
from scim2_models import Reference
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

        elif get_origin(field_type) is Reference:
            value = f"https://{str(uuid.uuid4())}.test"

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

    except SCIMClientError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc), data=exc.source)

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Successfull creation of a {obj.__class__.__name__} object with id {response.id}",
        data=response,
    )


@decorate_result
def check_object_query(scim: SCIMClient, obj: Resource) -> Tuple[Resource, CheckResult]:
    """Perform an object query by knowing its id.

    TODO:
      - check if the fields of the result object are the same than the
      fields of the request object
    """

    try:
        response = scim.query(obj.__class__, obj.id)

    except SCIMClientError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc), data=exc.source)

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Successfull query of a {obj.__class__.__name__} object with id {response.id}",
        data=response,
    )


@decorate_result
def check_object_query_without_id(
    scim: SCIMClient, obj: Resource
) -> Tuple[Resource, CheckResult]:
    """Perform an object creation.

    TODO:
      - look for the object across several pages
      - check if the fields of the result object are the same than the
      fields of the request object
    """

    try:
        response = scim.query(obj.__class__)

    except SCIMClientError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc), data=exc.source)

    found = any(obj.id == resource.id for resource in response.resources)
    if not found:
        return CheckResult(
            status=Status.ERROR,
            reason=f"Could not find object {obj.__class__.__name__} with id : {response.detail}",
            data=response,
        )

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Successfull query of a {obj.__class__.__name__} object with id {obj.id}",
        data=response,
    )


@decorate_result
def check_object_replacement(
    scim: SCIMClient, obj: Resource
) -> Tuple[Resource, CheckResult]:
    """Perform an object replacement.

    TODO:
      - check if the fields of the result object are the same than the
      fields of the request object
    """

    try:
        response = scim.replace(obj)

    except SCIMClientError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc), data=exc.source)

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Successfull replacement of a {obj.__class__.__name__} object with id {response.id}",
        data=response,
    )


@decorate_result
def check_object_deletion(
    scim: SCIMClient, obj: Resource
) -> Tuple[Resource, CheckResult]:
    """Perform an object deletion."""

    try:
        scim.delete(obj.__class__, obj.id)

    except SCIMClientError as exc:
        return CheckResult(status=Status.ERROR, reason=str(exc), data=exc.source)

    return CheckResult(
        status=Status.SUCCESS,
        reason=f"Successfull deletion of a {obj.__class__.__name__} object with id {obj.id}",
    )


def check_resource_type(
    scim: SCIMClient,
    resource_type: ResourceType,
    service_provider_config: ServiceProviderConfig,
) -> List[CheckResult]:
    """
    TODO:

    - Make a 'skip' status
    - Check search
    """
    results = []

    model = model_from_resource_type(resource_type)
    obj = model()
    fill_with_random_values(obj)

    result = check_object_creation(scim, obj)
    results.append(result)

    if result.status == Status.SUCCESS:
        created_obj = result.data
        result = check_object_query(scim, created_obj)
        queried_obj = result.data
        results.append(result)

        result = check_object_query_without_id(scim, created_obj)
        results.append(result)

        fill_with_random_values(queried_obj)
        result = check_object_replacement(scim, created_obj)
        results.append(result)

        result = check_object_deletion(scim, created_obj)
        results.append(result)

    return results
