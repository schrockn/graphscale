from typing import Any, Type
from mypy_extensions import NoReturn
from .errors import InvariantViolation


def isinst(obj: Any, ttype: Type, _msg: str=None) -> None:
    if not isinstance(obj, ttype):
        raise InvariantViolation(
            'incorrect type! expected {0} got {1}'.format(repr(type), repr(obj))
        )


def invariant(condition: Any, msg: str) -> None:
    if not condition:
        raise InvariantViolation(msg)


def failed(msg: str) -> NoReturn:
    raise InvariantViolation(msg)
