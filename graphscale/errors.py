class GraphscaleError(Exception):
    pass


class InvariantViolation(GraphscaleError):
    pass


class ParameterInvariantViolation(InvariantViolation):
    pass
