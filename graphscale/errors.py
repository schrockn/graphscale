from functools import wraps
from typing import Any, Callable


class GraphscaleError(Exception):
    pass


class InvariantViolation(GraphscaleError):
    pass


class ParameterInvariantViolation(InvariantViolation):
    pass


class GraphQLFieldError(GraphscaleError):
    def __init__(self, error: Exception) -> None:
        # only load if we need it
        import traceback
        trace = error.__traceback__
        trace_string = ''.join(traceback.format_tb(trace))
        self.message = "Inner Exception: %s" % error + "\n" + "Stack: " + "\n" + trace_string
        self.inner = error
        super().__init__(self.message)


def async_field_error_boundary(async_resolver: Callable) -> Callable:
    @wraps(async_resolver)
    async def inner(*args: Any, **kwargs: Any) -> Any:
        try:
            return await async_resolver(*args, **kwargs)
        except Exception as error:
            raise GraphQLFieldError(error)

    return inner


def field_error_boundary(resolver: Callable) -> Callable:
    @wraps(resolver)
    def inner(*args: Any, **kwargs: Any) -> Any:
        try:
            return resolver(*args, **kwargs)
        except Exception as error:
            raise GraphQLFieldError(error)

    return inner
