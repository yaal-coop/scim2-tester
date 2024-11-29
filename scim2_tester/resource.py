import random
import uuid
from enum import Enum
from inspect import isclass
from typing import get_args
from typing import get_origin

from pydantic import EmailStr
from scim2_models import ComplexAttribute
from scim2_models import EnterpriseUser
from scim2_models import Extension
from scim2_models import ExternalReference
from scim2_models import Group
from scim2_models import Meta
from scim2_models import Reference
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import ServiceProviderConfig
from scim2_models import URIReference
from scim2_models import User

from scim2_tester.utils import CheckConfig
from scim2_tester.utils import CheckResult
from scim2_tester.utils import Status
from scim2_tester.utils import checker


def model_from_resource_type(conf: CheckConfig, resource_type: ResourceType):
    if resource_type.id == "User":
        return (
            User[EnterpriseUser]
            if User[EnterpriseUser] in conf.client.resource_models
            else User
        )

    if resource_type.id == "Group":
        return Group


def fill_with_random_values(obj) -> Resource:
    for field_name, field in obj.model_fields.items():
        if field.default:
            continue

        field_type = obj.get_field_root_type(field_name)
        is_multiple = obj.get_field_multiplicity(field_name)

        if field_type is Meta:
            value = None

        elif field_type is int:
            value = uuid.uuid4().int

        elif field_type is bool:
            value = random.choice([True, False])

        elif get_origin(field_type) is Reference:
            if get_args(field_type)[0] not in (
                ExternalReference,
                URIReference,
            ):
                continue

            value = f"https://{str(uuid.uuid4())}.test"

        elif field_type is EmailStr:
            # pydantic won't allow to use the 'test' TLD here
            value = f"{uuid.uuid4()}@{uuid.uuid4()}.com"

        elif isclass(field_type) and issubclass(field_type, Enum):
            value = random.choice(list(field_type))

        elif isclass(field_type) and issubclass(field_type, ComplexAttribute):
            value = field_type()
            fill_with_random_values(value)

        elif isclass(field_type) and issubclass(field_type, Extension):
            value = field_type()
            fill_with_random_values(value)

        else:
            value = str(uuid.uuid4())

        if is_multiple:
            setattr(obj, field_name, [value])

        else:
            setattr(obj, field_name, value)

    return obj


@checker
def check_object_creation(
    conf: CheckConfig, obj: Resource
) -> tuple[Resource, CheckResult]:
    """Perform an object creation.

    Todo:
      - check if the fields of the result object are the same than the
      fields of the request object

    """
    response = conf.client.create(
        obj, expected_status_codes=conf.expected_status_codes or [201]
    )

    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful creation of a {obj.__class__.__name__} object with id {response.id}",
        data=response,
    )


@checker
def check_object_query(
    conf: CheckConfig, obj: Resource
) -> tuple[Resource, CheckResult]:
    """Perform an object query by knowing its id.

    Todo:
      - check if the fields of the result object are the same than the
      fields of the request object

    """
    response = conf.client.query(
        obj.__class__, obj.id, expected_status_codes=conf.expected_status_codes or [200]
    )
    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful query of a {obj.__class__.__name__} object with id {response.id}",
        data=response,
    )


@checker
def check_object_query_without_id(
    conf: CheckConfig, obj: Resource
) -> tuple[Resource, CheckResult]:
    """Perform the query of all objects of one kind.

    Todo:
      - look for the object across several pages
      - check if the fields of the result object are the same than the
      fields of the request object

    """
    response = conf.client.query(
        obj.__class__, expected_status_codes=conf.expected_status_codes or [200]
    )
    found = any(obj.id == resource.id for resource in response.resources)
    if not found:
        return CheckResult(
            conf,
            status=Status.ERROR,
            reason=f"Could not find object {obj.__class__.__name__} with id : {response.detail}",
            data=response,
        )

    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful query of a {obj.__class__.__name__} object with id {obj.id}",
        data=response,
    )


@checker
def check_object_replacement(
    conf: CheckConfig, obj: Resource
) -> tuple[Resource, CheckResult]:
    """Perform an object replacement.

    Todo:
      - check if the fields of the result object are the same than the
      fields of the request object

    """
    response = conf.client.replace(
        obj, expected_status_codes=conf.expected_status_codes or [200]
    )
    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful replacement of a {obj.__class__.__name__} object with id {response.id}",
        data=response,
    )


@checker
def check_object_deletion(
    conf: CheckConfig, obj: Resource
) -> tuple[Resource, CheckResult]:
    """Perform an object deletion."""
    conf.client.delete(
        obj.__class__, obj.id, expected_status_codes=conf.expected_status_codes or [204]
    )
    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful deletion of a {obj.__class__.__name__} object with id {obj.id}",
    )


def check_resource_type(
    conf: CheckConfig,
    resource_type: ResourceType,
    service_provider_config: ServiceProviderConfig,
) -> list[CheckResult]:
    results = []

    model = model_from_resource_type(conf, resource_type)
    obj = model()
    fill_with_random_values(obj)

    result = check_object_creation(conf, obj)
    results.append(result)

    if result.status == Status.SUCCESS:
        created_obj = result.data
        result = check_object_query(conf, created_obj)
        queried_obj = result.data
        results.append(result)

        result = check_object_query_without_id(conf, created_obj)
        results.append(result)

        fill_with_random_values(queried_obj)
        result = check_object_replacement(conf, created_obj)
        results.append(result)

        result = check_object_deletion(conf, created_obj)
        results.append(result)

    return results
