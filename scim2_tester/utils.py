import functools
from dataclasses import dataclass
from enum import Enum
from enum import auto
from typing import Any
from typing import Optional


class Status(Enum):
    SUCCESS = auto()
    ERROR = auto()


@dataclass
class CheckResult:
    """Store a check result."""

    status: Status

    title: Optional[str] = None
    """The title of the check."""

    description: Optional[str] = None
    """What the check does, and why the spec advises it to do."""

    reason: Optional[str] = None
    """Why it failed, or how it succeed."""

    data: Optional[Any] = None
    """Any related data that can help to debug."""


def decorate_result(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, CheckResult):
            result.title = func.__name__
            result.description = func.__doc__
        else:
            result[0].title = func.__name__
            result[0].description = func.__doc__
        return result

    return wrapped
