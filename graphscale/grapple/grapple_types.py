from functools import wraps
from uuid import UUID

import graphscale.check as check
from graphql import (
    GraphQLArgument, GraphQLField, GraphQLID, GraphQLInt, GraphQLList, GraphQLNonNull,
    GraphQLObjectType, GraphQLScalarType
)
from graphql.language.ast import StringValue
from graphscale.pent import create_pent, delete_pent
from graphscale.utils import to_snake_case


def req(ttype):
    return GraphQLNonNull(type=ttype)


def list_of(ttype):
    return GraphQLList(type=ttype)


class GraphQLFieldError(Exception):
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
            print('in async field error boundary')
            raise GraphQLFieldError(error)

    return inner


def field_error_boundary(resolver):
    @wraps(resolver)
    def inner(*args, **kwargs):
        try:
            return resolver(*args, **kwargs)
        except Exception as error:
            print('in field error boundary')
            raise GraphQLFieldError(error)

    return inner


def pythonify_dict(input_data):
    data = {}
    for name, value in input_data.items():
        python_name = to_snake_case(name)
        data[python_name] = pythonify_dict(value) if isinstance(value, dict) else value
    return data


def define_pent_mutation_resolver(python_name, pent_data_cls_name):
    check.str_param(python_name, 'python_name')

    def mutation_resolver(obj, args, context, *_):
        # TODO: Refactor into an error boundary
        try:
            if 'id' in args:
                args['obj_id'] = args['id']
                del args['id']
            pent_data_cls = context.cls_from_name(pent_data_cls_name)
            data_value = args['data']
            raw_data = pythonify_dict(data_value)
            pent_data = pent_data_cls(**raw_data)
            args['data'] = pent_data
            prop = getattr(obj, python_name)
            if callable(prop):
                return prop(**args)
            return prop
        except Exception as error:
            print(error)
            raise error

    return mutation_resolver


def define_default_resolver(python_name):
    check.str_param(python_name, 'python_name')

    @field_error_boundary
    def the_resolver(obj, args, *_):
        if args:
            if 'id' in args:
                args['obj_id'] = args['id']
                del args['id']
            args = pythonify_dict(args)
        prop = getattr(obj, python_name)
        if callable(prop):
            return prop(**args)
        return prop

    return the_resolver
