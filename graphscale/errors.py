from functools import wraps


class GraphscaleError(Exception):
    pass


class InvariantViolation(GraphscaleError):
    pass


class ParameterInvariantViolation(InvariantViolation):
    pass


class GraphQLFieldError(GraphscaleError):
    def __init__(self, error):
        # only load if we need it
        import traceback
        trace = error.__traceback__
        trace_string = ''.join(traceback.format_tb(trace))
        self.message = "Inner Exception: %s" % error + "\n" + "Stack: " + "\n" + trace_string
        self.inner = error
        super().__init__(self.message)


def async_field_error_boundary(async_resolver):
    @wraps(async_resolver)
    async def inner(*args, **kwargs):
        try:
            return await async_resolver(*args, **kwargs)
        except Exception as error:
            raise GraphQLFieldError(error)

    return inner


def field_error_boundary(resolver):
    @wraps(resolver)
    def inner(*args, **kwargs):
        try:
            return resolver(*args, **kwargs)
        except Exception as error:
            raise GraphQLFieldError(error)

    return inner
