import random
import uuid
from enum import Enum
from inspect import isclass
from typing import Any
from typing import get_args
from typing import get_origin

from pydantic import EmailStr
from scim2_models import ComplexAttribute
from scim2_models import Extension
from scim2_models import ExternalReference
from scim2_models import Meta
from scim2_models import Mutability
from scim2_models import Reference
from scim2_models import Required
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import URIReference

from scim2_tester.utils import CheckConfig
from scim2_tester.utils import CheckResult
from scim2_tester.utils import Status
from scim2_tester.utils import checker


def model_from_resource_type(
    conf: CheckConfig, resource_type: ResourceType
) -> type[Resource] | None:
    for resource_model in conf.client.resource_models:
        if resource_model.model_fields["schemas"].default[0] == resource_type.schema_:
            return resource_model

    return None


def fill_with_random_values(obj: Resource) -> Resource:
    for field_name, field in obj.model_fields.items():
        if field.default:
            continue

        field_type = obj.get_field_root_type(field_name)
        is_multiple = obj.get_field_multiplicity(field_name)

        value: Any
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
                if (
                    obj.__class__.get_field_annotation(field_name, Required)
                    == Required.true
                ):
                    return None
                continue

            value = f"https://{str(uuid.uuid4())}.test"

        elif field_type is EmailStr:
            # pydantic won't allow to use the 'test' TLD here
            value = f"{uuid.uuid4()}@{uuid.uuid4()}.com"

        elif isclass(field_type) and issubclass(field_type, Enum):
            value = random.choice(list(field_type))

        elif isclass(field_type) and issubclass(field_type, ComplexAttribute):
            value = fill_with_random_values(field_type())

        elif isclass(field_type) and issubclass(field_type, Extension):
            value = fill_with_random_values(field_type())

        else:
            value = str(uuid.uuid4())

        if is_multiple:
            setattr(obj, field_name, [value])

        else:
            setattr(obj, field_name, value)

    return obj


@checker
def check_object_creation(conf: CheckConfig, obj: type[Resource]) -> CheckResult:
    """Perform an object creation.

    .. todo::
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
def check_object_query(conf: CheckConfig, obj: type[Resource]) -> CheckResult:
    """Perform an object query by knowing its id.

    .. todo::
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
    conf: CheckConfig, obj: type[Resource]
) -> CheckResult:
    """Perform the query of all objects of one kind.

    .. todo::
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
            reason=f"Could not find object {obj.__class__.__name__} with id : {obj.id}",
            data=response,
        )

    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful query of a {obj.__class__.__name__} object with id {obj.id}",
        data=response,
    )


@checker
def check_object_replacement(conf: CheckConfig, obj: type[Resource]) -> CheckResult:
    """Perform an object replacement.

    .. todo::
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
def check_object_reset(conf: CheckConfig, obj: type[Resource]) -> CheckResult:
    """Perform an object reset.

    All the editable fields of the object take a null value.

    .. todo::
      - check if the fields of the result object are the same than the
      fields of the request object

    """
    nullable_attributes = [
        field_name
        for field_name, field in obj.model_fields.items()
        if (
            obj.get_field_annotation(field_name, Mutability)
            in (Mutability.read_write, Mutability.write_only)
            and obj.get_field_annotation(field_name, Required) == Required.false
        )
    ]
    for attribute_name in nullable_attributes:
        setattr(obj, attribute_name, None)

    response = conf.client.replace(
        obj, expected_status_codes=conf.expected_status_codes or [200]
    )

    non_nulled = [
        field_name
        for field_name in nullable_attributes
        if getattr(response, field_name) is not None
    ]
    if non_nulled:
        return CheckResult(
            conf,
            status=Status.ERROR,
            reason=f"Some attributes of {obj.__class__.__name__} could not be reset: {non_nulled}",
            data=response,
        )

    return CheckResult(
        conf,
        status=Status.SUCCESS,
        reason=f"Successful reset of the editable attributes of {obj.__class__.__name__}",
        data=response,
    )


@checker
def check_object_deletion(conf: CheckConfig, obj: type[Resource]) -> CheckResult:
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
) -> list[CheckResult]:
    model = model_from_resource_type(conf, resource_type)
    if not model:
        return [
            CheckResult(
                conf,
                status=Status.ERROR,
                reason=f"No Schema matching the ResourceType {resource_type.id}",
            )
        ]

    results = []
    obj = fill_with_random_values(model())

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

        result = check_object_reset(conf, created_obj)
        results.append(result)

        result = check_object_deletion(conf, created_obj)
        results.append(result)

    return results
