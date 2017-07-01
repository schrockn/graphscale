from graphql import GraphQLList, GraphQLNonNull

import graphscale.check as check
from graphscale.errors import async_field_error_boundary, field_error_boundary
from graphscale.utils import to_snake_case


def pythonify_dict(input_data):
    data = {}
    for name, value in input_data.items():
        python_name = to_snake_case(name)
        data[python_name] = pythonify_dict(value) if isinstance(value, dict) else value
    return data


def process_args(args):
    if 'id' in args:
        args['obj_id'] = args['id']
        del args['id']
    return pythonify_dict(args)


def define_pent_mutation_resolver(python_name, pent_data_cls_name):
    check.str_param(python_name, 'python_name')

    @async_field_error_boundary
    async def mutation_resolver(obj, args, context, *_):
        args = process_args(args)
        pent_data_cls = context.cls_from_name(pent_data_cls_name)
        pent_data = pent_data_cls(**args['data'])
        args['data'] = pent_data
        prop = getattr(obj, python_name)
        check.invariant(callable(prop), 'must be async function')
        return await prop(**args)

    return mutation_resolver


def define_default_gen_resolver(python_name):
    check.str_param(python_name, 'python_name')

    @async_field_error_boundary
    async def the_resolver(obj, args, *_):
        if args:
            if 'id' in args:
                args['obj_id'] = args['id']
                del args['id']
            args = pythonify_dict(args)
        prop = getattr(obj, python_name)
        check.invariant(callable(prop), 'must be async function')
        return await prop(**args)

    return the_resolver


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
