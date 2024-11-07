from enum import Enum

from scim2_models import ComplexAttribute
from scim2_models import Reference
from scim2_models import Resource

from scim2_tester.resource import fill_with_random_values


def test_random_values():
    """Check that 'fill_with_random_values' produce valid objects."""

    class Complex(ComplexAttribute):
        str_unique: str | None = None
        str_multiple: list[str] | None = None

    class CustomModel(Resource):
        schemas: list[str] = ["org:test:CustomModel"]

        class Type(str, Enum):
            foo = "foo"
            bar = "bar"

        str_unique: str | None = None
        str_multiple: list[str] | None = None

        int_unique: int | None = None
        int_multiple: list[int] | None = None

        bool_unique: bool | None = None
        bool_multiple: list[bool] | None = None

        reference_unique: Reference | None = None
        reference_multiple: list[Reference] | None = None

        email_unique: Reference | None = None
        email_multiple: list[Reference] | None = None

        enum_unique: Type | None = None
        enum_multiple: list[Type] | None = None

        complex_unique: Complex | None = None
        complex_multiple: list[Complex] | None = None

    obj = CustomModel()
    fill_with_random_values(obj)
    for field_name in obj.model_fields:
        if field_name == "meta":
            continue

        assert getattr(obj, field_name) is not None
