from mypy_extensions import NoReturn
from typing import Any, Type
from .errors import InvariantViolation


def isinst(obj: Any, type: Type, msg: str=None) -> None:
    if not isinstance(obj, type):
        raise InvariantViolation(
            'incorrect type! expected {0} got {1}'.format(repr(type), repr(obj))
        )


def invariant(condition: Any, msg: str) -> None:
    if not condition:
        raise InvariantViolation(msg)


def failed(msg: str) -> NoReturn:
    raise InvariantViolation(msg)