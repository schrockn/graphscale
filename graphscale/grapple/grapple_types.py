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


class GrappleType:
    _memo = {}

    @classmethod
    def type(cls):
        if cls in GrappleType._memo:
            return GrappleType._memo[cls]
        new_type = cls.create_type()
        GrappleType._memo[cls] = new_type
        return new_type

    @classmethod
    def create_type(cls):
        raise Exception('must implement @classmethod create_type')


def id_field():
    return GraphQLField(
        type=GraphQLNonNull(type=GraphQLID),
        resolver=lambda obj, *_: obj.get_obj_id(),
    )


def req(ttype):
    return GraphQLNonNull(type=ttype)


def list_of(ttype):
    return GraphQLList(type=ttype)


def define_top_level_getter(graphql_type, pent_type):
    check.param(graphql_type, GraphQLObjectType, 'graphql_type')
    return GraphQLField(
        type=graphql_type,
        args={'id': GraphQLArgument(type=GraphQLID)},
        resolver=get_pent_genner(pent_type)
    )


def get_pent_genner(klass):
    @async_field_error_boundary
    async def genner(_parent, args, context, *_):
        obj_id = UUID(args['id'])
        obj = await klass.gen(context, obj_id)
        return obj

    return genner


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


def define_create(out_type, in_type, resolver):
    return GraphQLField(
        type=out_type,
        args={
            'input': GraphQLArgument(type=req(in_type)),
        },
        resolver=resolver,
    )


def create_browse_field(graphql_type, pent_type):
    @async_field_error_boundary
    async def browse_resolver(_parent, args, context, *_):
        after = None
        if 'after' in args:
            after = UUID(hex=args['after'])
        first = args.get('first', 1000)  # cap at 1000 to prevent timeouts for now
        return await pent_type.gen_all(context, after, first) or []

    return GraphQLField(
        type=req(list_of(req(graphql_type))),
        args={
            'after': GraphQLArgument(type=GraphQLID),
            'first': GraphQLArgument(type=GraphQLInt, default_value=100),
        },
        resolver=browse_resolver,
    )


def create_pent_input(pent_map, in_graphql_type, input_data):
    check.param(pent_map, dict, 'pent_map')
    check.param(input_data, dict, 'input_data')

    if in_graphql_type.name not in pent_map:
        raise Exception('did you remember to put input %s in pent_map?' % in_graphql_type)

    data = pythonify_dict(input_data)

    in_pent_type = pent_map[in_graphql_type.name]
    return in_pent_type(data=data)


def pythonify_dict(input_data):
    data = {}
    for name, value in input_data.items():
        python_name = to_snake_case(name)
        data[python_name] = pythonify_dict(value) if isinstance(value, dict) else value
    return data


def define_default_create_resolver(in_graphql_type, out_pent_type, pent_map, create_gen):
    @async_field_error_boundary
    async def actual_resolver(_parent, args, context, *_):
        input_data = args['input']
        input_object = create_pent_input(pent_map, in_graphql_type, input_data)
        return await create_gen(context, input_object)

    return actual_resolver


def define_default_create(*, out_graphql, in_graphql, pent_map, create_gen=None):
    out_pent = pent_map[out_graphql.name]
    if not create_gen:

        async def create_gen_default(pent_context, input_object):
            return await create_pent(pent_context, out_pent, input_object)

        create_gen = create_gen_default
    resolver = define_default_create_resolver(in_graphql, out_pent, pent_map, create_gen)
    return define_create(out_graphql, in_graphql, resolver)


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


def define_default_delete(graphql_type, pent_map):
    @async_field_error_boundary
    async def default_delete_resolver(_parent, args, context, *_):
        pent_type = pent_map[graphql_type.name]
        obj_id = UUID(hex=args['id'])
        await delete_pent(context, pent_type, obj_id)
        return obj_id

    return GraphQLField(
        type=req(GraphQLID),
        args={
            'id': GraphQLArgument(req(GraphQLID)),
        },
        resolver=default_delete_resolver,
    )
