from uuid import UUID
import traceback


class InvariantViolation(Exception):
    pass


class ParameterInvariantViolation(InvariantViolation):
    pass


def opt_param(obj, ttype, name):
    if obj and not isinstance(obj, ttype):
        stack_str = ''.join(traceback.format_stack())
        if obj == id:
            raise ParameterInvariantViolation("obj is id. typo?")
        raise ParameterInvariantViolation(
            'Param %s is not a %s. It is a %s. Value: %s' %
            (name, ttype.__name__, type(param).__name__, repr(obj)) + ' Stack: ' + stack_str
        )


def param(obj, ttype, name):
    if not isinstance(obj, ttype):
        stack_str = ''.join(traceback.format_stack())
        if obj == id:
            raise ParameterInvariantViolation("obj is id. typo?")
        raise ParameterInvariantViolation(
            'Param %s is not a %s. It is a %s. Value: %s' %
            (name, ttype.__name__, type(param).__name__, repr(obj)) + ' Stack: ' + stack_str
        )


def param_invariant(condition, name):
    if not condition:
        raise ParameterInvariantViolation('invariant failed for param ' + name)


def param_violation(condition, name):
    if condition:
        raise ParameterInvariantViolation('invariant failed for param ' + name)


def opt_cls_param(obj, name):
    return opt_param(obj, type, name)


def cls_param(obj, name):
    return param(obj, type, name)


def uuid_param(obj, name):
    return param(obj, UUID, name)


def opt_uuid_param(obj, name):
    return opt_param(obj, UUID, name)


def str_param(obj, name):
    return param(obj, str, name)


def int_param(obj, name):
    return param(obj, int, name)


def opt_int_param(obj, name):
    return opt_param(obj, int, name)


def list_param(obj, name, item_cls=None):
    param(obj, list, name)
    if item_cls:
        for item in obj:
            param_invariant(isinstance(item, item_cls), obj)


def dict_param(obj, name):
    return param(obj, dict, name)


def opt_dict_param(obj, name):
    return opt_param(obj, dict, name)


def bool_param(obj, name):
    return param(obj, bool, name)


def invariant(condition, msg):
    if not condition:
        raise InvariantViolation(msg)


def failed(msg):
    raise InvariantViolation(msg)
